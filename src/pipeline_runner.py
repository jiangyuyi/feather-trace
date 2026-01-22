import os
import sys
import yaml
import logging
import hashlib
from pathlib import Path
from datetime import datetime

# Add project root to sys.path to allow running as script
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from src.metadata.ioc_manager import IOCManager
from src.core.detector import BirdDetector
from src.core.quality import QualityChecker
from src.core.processor import ImageProcessor
from src.recognition.inference_local import LocalBirdRecognizer
from src.recognition.inference_dongniao import DongniaoRecognizer
from src.recognition.inference_api import APIBirdRecognizer
from src.metadata.exif_writer import ExifWriter
from src.utils.config_loader import load_config
from src.utils.env_check import check_system_dependencies

from src.core.io.fs_manager import FileSystemManager
from src.core.io.temp_manager import TempFileManager
from src.core.io.path_generator import PathGenerator
from src.core.io.path_parser import PathParser

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

class FeatherTracePipeline:
    def __init__(self, config_path: str = "config/settings.yaml"):
        # Use centralized config loader
        self.config = load_config(config_path)
        
        # Initialize FS Manager
        self.fs_manager = FileSystemManager.get_instance(self.config.get('paths', {}))
        
        self.db = IOCManager(self.config['paths']['db_path'])
        self.device = self.config['processing'].get('device', 'cpu')
        self.detector = BirdDetector(
            self.config['processing']['yolo_model'], 
            self.config['processing']['confidence_threshold'],
            device=self.device
        )
        self.recognizer = None # Lazy load later
        self.exif_writer = ExifWriter()
        
        # Path Generator
        out_conf = self.config['paths'].get('output', {})
        self.path_generator = PathGenerator(
            template=out_conf.get('structure_template', "{year}/{location}/{species_cn}/{filename}"),
            output_root=out_conf.get('root_dir', 'data/processed')
        )
        self.write_back_raw = out_conf.get('write_back_to_source', False)
        
        # Load taxonomy and config lists
        self.foreign_countries = self._load_list(self.config['paths']['foreign_list'])
        self.china_allowlist = self._load_list(self.config['paths']['china_list'])
        self.all_labels = self._get_taxonomy_labels()

    def _load_list(self, path_str):
        path = Path(path_str)
        if path.exists():
            with open(path, 'r', encoding='utf-8') as f:
                return set(line.strip() for line in f if line.strip())
        return set()

    def _calculate_file_hash(self, provider, file_path: str, size: int) -> str:
        """
        Calculate partial SHA256 hash for fast deduplication.
        """
        sha256 = hashlib.sha256()
        
        data = provider.read_bytes(file_path)
        
        if size < 12288:
             sha256.update(data)
        else:
             sha256.update(data[:4096])
             sha256.update(data[size//2 : size//2 + 4096])
             sha256.update(data[-4096:])

        return f"{size}_{sha256.hexdigest()}"

    def _get_taxonomy_labels(self):
        # Check if DB is empty
        self.db.cursor.execute("SELECT count(*) FROM taxonomy")
        count = self.db.cursor.fetchone()[0]
        
        if count == 0:
            logging.warning("Taxonomy table is empty! Attempting auto-import from Excel...")
            excel_path = self.config['paths']['ioc_list_path']
            if Path(excel_path).exists():
                self.db.import_from_excel(excel_path)
                # Re-check count
                self.db.cursor.execute("SELECT count(*) FROM taxonomy")
                count = self.db.cursor.fetchone()[0]
                logging.info(f"Auto-import completed. Taxonomy count: {count}")
            else:
                logging.error(f"Cannot auto-import: Excel file not found at {excel_path}")
                return []

        # Fetch all scientific names from taxonomy table
        self.db.cursor.execute("SELECT scientific_name FROM taxonomy")
        all_labels = [row[0] for row in self.db.cursor.fetchall()]
        logging.info(f"Loaded {len(all_labels)} total labels from DB.")
        return all_labels

    def _select_candidate_labels(self, location_tag: str):
        mode = self.config.get('recognition', {}).get('region_filter')
        
        if mode == 'china':
            if not self.china_allowlist:
                 logging.warning("Region filter is 'china' but china_bird_list.txt is empty/missing. Using full list.")
                 return self.all_labels
            return [name for name in self.all_labels if name in self.china_allowlist]
            
        if mode == 'auto':
            is_foreign = False
            for country in self.foreign_countries:
                if country in location_tag:
                    is_foreign = True
                    break
            
            if is_foreign:
                logging.info(f"Location '{location_tag}' identified as Foreign. Using Global list.")
                return self.all_labels
            else:
                logging.info(f"Location '{location_tag}' identified as Domestic. Using China list.")
                if not self.china_allowlist:
                    return self.all_labels
                return [name for name in self.all_labels if name in self.china_allowlist]

        return self.all_labels

    def run(self):
        sources = self.config['paths'].get('sources', [])
        # Fallback for old config
        if not sources and 'raw_dir' in self.config['paths']:
             sources = [{'path': self.config['paths']['raw_dir'], 'recursive': False}]

        for source in sources:
            if not source.get('enabled', True):
                continue
                
            path_str = source['path']
            recursive = source.get('recursive', True)
            structure_pattern = source.get('structure_pattern', None)
            
            logging.info(f"Scanning source: {path_str} (Recursive: {recursive})")
            
            provider, rel_path = self.fs_manager.resolve_path(path_str)
            
            if not provider.exists(rel_path):
                logging.warning(f"Source path not found: {path_str}")
                continue
            
            # Initialize PathParser for this source root
            # Note: We pass the resolved absolute root to parser
            # rel_path here might be relative to provider root, let's assume provider.get_local_path handles resolution
            # For LocalProvider, list_dir returns entries with absolute paths.
            # So we create a parser with the absolute root of the source.
            
            # TODO: Improve this for remote providers where 'absolute path' concept differs
            # For LocalProvider, we can resolve the root once.
            source_root_abs = provider.get_local_path(rel_path) 
            parser = PathParser(source_root_abs, structure_pattern)

            # Iterate files
            for entry in provider.list_dir(rel_path, recursive=recursive):
                if entry.is_dir:
                    continue
                
                if not entry.name.lower().endswith(('.jpg', '.jpeg')):
                    continue
                
                # Parse metadata using the new parser
                meta = parser.parse(entry.path)
                
                # Process
                self.process_image(provider, entry, meta)

    def process_image(self, provider, entry, meta: dict):
        logging.info(f"--- Processing {entry.name} ---")
        captured_date = meta['captured_date']
        location_tag = meta['location_tag']
        
        # 0. Deduplication Check
        file_hash = self._calculate_file_hash(provider, entry.path, entry.size)
        if self.db.check_hash_exists(file_hash):
            logging.info(f"Skipping {entry.name}: Already processed (Hash match).")
            return

        with TempFileManager.get_local_copy(provider, entry.path) as local_img_path:
            
            # 1. Quality Check
            blur_score = QualityChecker.calculate_blur_score(local_img_path)
            if blur_score < self.config['processing']['blur_threshold']:
                logging.warning(f"Skipping {entry.name}: Sharpness ({blur_score:.2f}) below threshold.")
                return

            # 2. Detection
            boxes = self.detector.detect(local_img_path)
            if not boxes:
                logging.warning(f"No birds detected in {entry.name}")
                return
            
            main_box = boxes[0]
            
            # Pre-calculate labels
            candidate_labels = self._select_candidate_labels(location_tag)
            
            # 3. Cropping
            processed_temp_dir = Path("data/processed/.temp")
            processed_temp_dir.mkdir(parents=True, exist_ok=True)
            temp_cropped = processed_temp_dir / f"temp_{entry.name}"
            
            success = ImageProcessor.crop_and_resize(
                local_img_path, 
                main_box, 
                str(temp_cropped),
                target_size=self.config['processing']['target_size'],
                padding=self.config['processing']['crop_padding']
            )
            
            if not success: return

            # 4. Recognition
            if self.recognizer is None:
                mode = self.config['recognition'].get('mode', 'local')
                rec_config = self.config['recognition']
                if mode == 'dongniao':
                    dn_conf = rec_config.get('dongniao', {})
                    self.recognizer = DongniaoRecognizer(dn_conf.get('key'), dn_conf.get('url'))
                elif mode == 'api':
                    api_conf = rec_config.get('api', {})
                    self.recognizer = APIBirdRecognizer(api_conf.get('url'), api_conf.get('key'))
                else:
                    local_conf = rec_config.get('local', {})
                    self.recognizer = LocalBirdRecognizer(local_conf.get('model_type', 'bioclip'), self.device)
            
            results = self.recognizer.predict(str(temp_cropped), candidate_labels)
            
            if not results:
                logging.warning(f"Recognition returned no results for {entry.name}.")
                sci_name = "Unknown"
                chinese_name = "未知鸟种"
                conf = 0.0
                family_cn = ""
            else:
                best_match = results[0]
                sci_name = best_match['scientific_name']
                conf = best_match['confidence']
                
                # 5. Translation
                bird_info = self.db.get_bird_info(sci_name)
                chinese_name = bird_info['chinese_name'] if bird_info else sci_name
                family_cn = bird_info['family_cn'] if bird_info else ""

            # 6. Metadata and Archiving
            conf_pct = int(conf * 100)
            
            # Update meta dict for generator
            meta.update({
                'primary_bird_cn': chinese_name,
                'scientific_name': sci_name,
                'confidence_score': conf
            })
            
            # Generate FINAL Path
            final_path = self.path_generator.generate_path(meta, entry.name)
            
            # Ensure parent dir exists
            final_path.parent.mkdir(parents=True, exist_ok=True)
            
            # Handle collision
            if final_path.exists():
                stem = final_path.stem
                counter = 1
                while final_path.exists():
                    final_path = final_path.with_name(f"{stem}_{counter}.jpg")
                    counter += 1
            
            # Move
            try:
                temp_cropped.rename(final_path)
            except OSError as e:
                logging.error(f"Failed to move processed file to {final_path}: {e}")
                return

            # Prepare Tags
            tags = {
                "IPTC:Keywords": [chinese_name, location_tag, family_cn, sci_name],
                "XMP:Description": f"AI Identification: {chinese_name} ({conf_pct}%)"
            }
            
            # Write EXIF
            self.exif_writer.write_metadata(str(final_path), tags)
            
            # Write EXIF to Source
            if self.write_back_raw:
                logging.info(f"Writing metadata back to source: {entry.path}")
                src_local_path = provider.get_local_path(entry.path)
                if src_local_path:
                    source_tags = tags.copy()
                    source_tags["IPTC:Keywords"] = source_tags["IPTC:Keywords"] + ["FeatherTrace"]
                    self.exif_writer.write_metadata(src_local_path, source_tags)
                else:
                    logging.warning("Skipping source writeback: Remote provider writeback not yet supported.")
            
            # 7. Database Entry
            from PIL import Image
            try:
                with Image.open(final_path) as img:
                    w, h = img.size
            except Exception:
                w, h = 0, 0
                
            self.db.add_photo_record({
                'file_path': str(final_path.absolute()),
                'filename': final_path.name,
                'original_path': entry.path,
                'file_hash': file_hash,
                'captured_date': captured_date,
                'location_tag': location_tag,
                'primary_bird_cn': chinese_name,
                'scientific_name': sci_name,
                'confidence_score': conf,
                'width': w,
                'height': h
            })
            
            logging.info(f"Successfully processed and archived: {final_path.name}")

if __name__ == "__main__":
    config_path = "config/settings.yaml"
    config = load_config(config_path)
    
    if not check_system_dependencies(config):
        logging.error("System check failed. Please fix the issues above and restart.")
        sys.exit(1)
        
    runner = FeatherTracePipeline(config_path)
    runner.run()