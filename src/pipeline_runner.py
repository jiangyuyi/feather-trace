import os
import sys
import yaml
import logging
import hashlib
import time
import json
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

class SmartScanner:
    def __init__(self, root_path: Path, start_date: str = None, end_date: str = None):
        self.root_path = root_path
        self.start_date = int(start_date) if start_date else 0
        self.end_date = int(end_date) if end_date else 99999999

    def _is_in_range(self, d_start, d_end):
        if not d_start: return True # No date info, assume safe to explore
        
        # d_start is always present if d_end is present
        start_int = int(d_start)
        end_int = int(d_end) if d_end else start_int
        
        # Check intersection
        # Folder range: [start_int, end_int]
        # Query range: [self.start_date, self.end_date]
        return not (end_int < self.start_date or start_int > self.end_date)

    def scan(self, current_path: Path):
        try:
            # First, process files in current dir
            for entry in os.scandir(current_path):
                if entry.is_file():
                    yield entry
                elif entry.is_dir():
                    # Check pruning
                    d_start, d_end, _ = PathParser.parse_folder_name(entry.name)
                    
                    if self._is_in_range(d_start, d_end):
                         # Recurse
                         yield from self.scan(Path(entry.path))
                    else:
                        logging.debug(f"Pruning skipped: {entry.name}")
        except PermissionError:
            pass

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

    def _init_recognizer(self):
        """
        Lazy load the recognizer to save resources if no birds are found.
        """
        rec_config = self.config['recognition']
        mode = rec_config.get('mode', 'local')
        
        if mode == 'local':
            conf = rec_config.get('local', {})
            self.recognizer = LocalBirdRecognizer(
                model_name=conf.get('model_type', 'bioclip'),
                device=self.device
            )
        elif mode == 'dongniao':
            conf = rec_config.get('dongniao', {})
            self.recognizer = DongniaoRecognizer(
                api_key=conf.get('key'),
                base_url=conf.get('url')
            )
        elif mode == 'api':
             conf = rec_config.get('api', {})
             self.recognizer = APIBirdRecognizer(
                 api_key=conf.get('key'),
                 base_url=conf.get('url')
             )
        else:
            logging.error(f"Unknown recognition mode: {mode}")
            raise ValueError(f"Unknown recognition mode: {mode}")

    def process_image(self, provider, entry, meta):
        try:
            # 1. Deduplication Check
            file_hash = self._calculate_file_hash(provider, entry.path, entry.size)
            if self.db.check_hash_exists(file_hash):
                 logging.debug(f"Skipping duplicate: {entry.name}")
                 return

            # 2. Get Local Path (Required for Detector/Processor currently)
            # If provider is remote, we might need to download to temp first.
            # Currently assuming LocalProvider or mounted path.
            local_source_path = provider.get_local_path(entry.path)
            if not local_source_path:
                logging.warning(f"Could not get local path for {entry.name}, skipping.")
                return

            # 3. Detect
            detections = self.detector.detect(local_source_path)
            if not detections:
                logging.debug(f"No birds detected in {entry.name}")
                return
            
            # Initialize Recognizer if needed
            if self.recognizer is None:
                 self._init_recognizer()

            # 4. Process Detections
            # Filter candidate labels based on location
            location_tag = meta.get('location_tag', 'Unknown')
            candidate_labels = self._select_candidate_labels(location_tag)
            
            # Iterate through detections
            # For this version, we process all detections. 
            # If multiple birds are in one photo, we might generate multiple outputs 
            # OR just process the main one.
            # Strategy: Crop and Save each valid bird.
            
            img_width, img_height = 0, 0
            try:
                from PIL import Image
                with Image.open(local_source_path) as tmp_img:
                    img_width, img_height = tmp_img.size
            except:
                pass

            for i, (box, score) in enumerate(detections):
                # 4a. Crop to Temp
                # We need a temp file for recognition
                temp_crop_path = Path("data/processed/temp") / f"temp_{entry.name}"
                
                success = ImageProcessor.crop_and_resize(
                    local_source_path, 
                    box, 
                    str(temp_crop_path), 
                    target_size=self.config['processing']['target_size'],
                    padding=self.config['processing']['crop_padding']
                )
                
                if not success:
                    continue

                # 4b. Recognize
                top_k = self.config.get('recognition', {}).get('top_k', 5)
                alt_threshold = self.config.get('recognition', {}).get('alternatives_threshold', 70)
                
                results = self.recognizer.predict(str(temp_crop_path), candidate_labels, top_k=top_k)
                
                # Default to Unknown if no result
                if not results:
                    top_result = {"scientific_name": "Unknown", "confidence": 0.0}
                    user_comment = "No recognition results."
                else:
                    top_result = results[0]
                    top_conf_pct = top_result['confidence'] * 100
                    
                    # Format UserComment with alternatives
                    # Use &#xa; for newlines to be compatible with ExifWriter's -E flag
                    comment_lines = []
                    candidates_data = [] # Data to be stored in DB
                    
                    # Logic: If top result > threshold, ONLY show top result. 
                    # Else, show top + alternatives.
                    show_alternatives = (top_conf_pct <= alt_threshold)
                    
                    # Limit iteration based on logic
                    display_results = results if show_alternatives else [results[0]]

                    for i, res in enumerate(results):
                        r_sci = res['scientific_name']
                        r_conf = res['confidence'] * 100
                        
                        # Lookup Chinese name
                        r_info = self.db.get_bird_info(r_sci)
                        r_cn = r_info['chinese_name'] if r_info else r_sci
                        
                        # Add to DB data (store all results regardless of threshold for future reference)
                        candidates_data.append({
                            "sci": r_sci,
                            "cn": r_cn,
                            "score": res['confidence']
                        })

                        # Add to Comment (filtered by threshold)
                        if i == 0:
                            comment_lines.append(f"Top Match: {r_cn} ({r_sci}) - {r_conf:.1f}%")
                            if show_alternatives and len(results) > 1:
                                comment_lines.append("Alternatives:")
                        elif show_alternatives:
                            comment_lines.append(f"{i}. {r_cn} ({r_sci}) - {r_conf:.1f}%")
                    
                    user_comment = "&#xa;".join(comment_lines)

                # 4c. Metadata & Path Generation
                sci_name = top_result['scientific_name']
                confidence = top_result['confidence']
                
                # Get Chinese Name
                bird_info = self.db.get_bird_info(sci_name)
                cn_name = bird_info['chinese_name'] if bird_info else sci_name
                
                # Generate Final Path
                # Prepare metadata dict for PathGenerator (must match its expected keys)
                gen_meta = {
                    'captured_date': meta.get('captured_date', '00000000'),
                    'location_tag': location_tag,
                    'primary_bird_cn': cn_name,
                    'scientific_name': sci_name,
                    'confidence_score': confidence,
                    'source_structure': meta.get('source_structure', '.')
                }
                
                # If we have multiple birds, append suffix via filename arg (handled by generate_path if supported, 
                # but generate_path takes original_filename. We might need to fake the filename if we want suffix.)
                # PathGenerator uses Path(original_filename).stem
                
                current_filename = entry.name
                if len(detections) > 1:
                    base = Path(entry.name).stem
                    ext = Path(entry.name).suffix
                    current_filename = f"{base}_{i+1}{ext}"

                final_path = self.path_generator.generate_path(gen_meta, current_filename)
                
                # 4d. Save Final Image (Move from temp)
                # Ensure directory exists
                Path(final_path).parent.mkdir(parents=True, exist_ok=True)
                
                import shutil
                shutil.move(str(temp_crop_path), final_path)
                
                # 5. Write Metadata (EXIF + DB)
                description = f"{cn_name} ({sci_name})"
                self.exif_writer.write_metadata(final_path, {
                    'ImageDescription': description,
                    'XMP:Description': description,
                    'XPTitle': description, # Windows Explorer Title
                    'XPSubject': "",        # Explicitly clear Subject
                    'Keywords': [cn_name, sci_name, location_tag, "FeatherTrace"],
                    'UserComment': user_comment
                })
                
                self.db.add_photo_record({
                    'file_path': str(final_path),
                    'filename': Path(final_path).name,
                    'original_path': entry.path,
                    'file_hash': file_hash,
                    'captured_date': meta.get('captured_date'),
                    'location_tag': location_tag,
                    'primary_bird_cn': cn_name,
                    'scientific_name': sci_name,
                    'confidence_score': confidence,
                    'width': img_width,
                    'height': img_height,
                    'candidates_json': json.dumps(candidates_data, ensure_ascii=False)
                })
                
                logging.info(f"Processed: {entry.name} -> {cn_name} ({confidence*100:.1f}%)")
                
        except Exception as e:
            logging.error(f"Error processing {entry.name}: {e}", exc_info=True)

    def run(self, start_date: str = None, end_date: str = None):
        t_start = time.time()
        start_time_str = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        processed_count = 0
        
        if start_date:
            logging.info(f"Pipeline Filter: Range [{start_date} - {end_date or 'Max'}]")
        
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
            
            # Smart Scanning Logic
            # We bypass provider.list_dir for recursive + date filter combination
            # ONLY if it's a LocalProvider (which it currently is)
            # For remote providers, we'd need a different strategy, but for now assuming local mount
            
            source_root_abs = Path(provider.get_local_path(rel_path))
            parser = PathParser(source_root_abs, structure_pattern)
            
            iterator = []
            if recursive and (start_date or end_date):
                # Use SmartScanner for pruning
                scanner = SmartScanner(source_root_abs, start_date, end_date)
                iterator = scanner.scan(source_root_abs)
            else:
                # Fallback to standard provider listing (flat or simple recursive without prune)
                # Note: provider.list_dir yields FileEntry objects, SmartScanner yields scandir entries
                # We need to normalize
                iterator = provider.list_dir(rel_path, recursive=recursive)

            # Iterate files
            for entry in iterator:
                # Normalize entry to be object with .name, .path, .is_dir, .size
                # SmartScanner yields os.DirEntry, provider yields FileEntry
                
                is_dir = entry.is_dir() if callable(entry.is_dir) else entry.is_dir
                if is_dir: continue
                
                entry_name = entry.name
                entry_path = entry.path # Absolute path string
                
                # Check extension
                if not entry_name.lower().endswith(('.jpg', '.jpeg')):
                    continue
                
                # Parse metadata
                meta = parser.parse(entry_path)
                
                # Double Check Date (File level check)
                # SmartScanner prunes folders, but if a folder is "2023_Trip", it might contain "20230101.jpg"
                # If range is very specific, we might still want to skip specific files.
                c_date = meta.get('captured_date')
                if start_date and c_date:
                    if int(c_date) < int(start_date): continue
                if end_date and c_date:
                    if int(c_date) > int(end_date): continue

                # Process
                # Fake a FileEntry-like object if it came from os.scandir
                # process_image expects an object with .path, .name, .size
                if not hasattr(entry, 'size'):
                    # It's os.DirEntry
                    class Adapter:
                        def __init__(self, e):
                            self.path = e.path
                            self.name = e.name
                            self.size = e.stat().st_size
                    entry_obj = Adapter(entry)
                else:
                    entry_obj = entry
                    
                processed_count += 1
                self.process_image(provider, entry_obj, meta)

        # Record History
        t_end = time.time()
        duration = t_end - t_start
        end_time_str = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        
        self.db.add_scan_history({
            'start_time': start_time_str,
            'end_time': end_time_str,
            'range_start': start_date or "All",
            'range_end': end_date or "All",
            'processed_count': processed_count,
            'duration_seconds': round(duration, 2),
            'status': 'Completed'
        })
        logging.info(f"Pipeline completed. Processed: {processed_count}. Duration: {duration:.2f}s")

if __name__ == "__main__":
    config_path = "config/settings.yaml"
    config = load_config(config_path)
    
    if not check_system_dependencies(config):
        logging.error("System check failed. Please fix the issues above and restart.")
        sys.exit(1)
        
    runner = FeatherTracePipeline(config_path)
    runner.run()