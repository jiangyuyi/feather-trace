import os
import sys
import yaml
import logging
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

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

class FeatherTracePipeline:
    def __init__(self, config_path: str = "config/settings.yaml"):
        # Use centralized config loader
        self.config = load_config(config_path)
        
        self.db = IOCManager(self.config['paths']['db_path'])
        self.device = self.config['processing'].get('device', 'cpu')
        self.detector = BirdDetector(
            self.config['processing']['yolo_model'], 
            self.config['processing']['confidence_threshold'],
            device=self.device
        )
        self.recognizer = None # Lazy load later
        self.exif_writer = ExifWriter()
        
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

    def _calculate_file_hash(self, file_path: Path) -> str:
        """
        Calculate partial SHA256 hash for fast deduplication.
        Reads first 4k + middle 4k + last 4k bytes.
        """
        import hashlib
        size = file_path.stat().st_size
        sha256 = hashlib.sha256()
        
        with open(file_path, 'rb') as f:
            if size < 12288:
                sha256.update(f.read())
            else:
                sha256.update(f.read(4096))
                f.seek(size // 2)
                sha256.update(f.read(4096))
                f.seek(-4096, 2)
                sha256.update(f.read(4096))
                
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
            # Check if location contains any foreign country name
            is_foreign = False
            for country in self.foreign_countries:
                if country in location_tag:
                    is_foreign = True
                    break
            
            if is_foreign:
                logging.info(f"Location '{location_tag}' identified as Foreign. Using Global list.")
                return self.all_labels
            else:
                # Default to China for auto mode if not foreign
                logging.info(f"Location '{location_tag}' identified as Domestic (or unknown). Using China list.")
                if not self.china_allowlist:
                    return self.all_labels
                return [name for name in self.all_labels if name in self.china_allowlist]

        # Default / Global
        return self.all_labels

    def run(self):
        raw_dir = Path(self.config['paths']['raw_dir'])
        processed_dir = Path(self.config['paths']['processed_dir'])
        
        if not raw_dir.exists():
            logging.error(f"Raw directory {raw_dir} does not exist.")
            return

        # Scan subdirectories: format {Date}_{Location}
        for sub_dir in raw_dir.iterdir():
            if not sub_dir.is_dir():
                continue
            
            parts = sub_dir.name.split('_')
            if len(parts) >= 2:
                captured_date = parts[0]
                location_tag = parts[1]
            else:
                captured_date = datetime.now().strftime("%Y%m%d")
                location_tag = sub_dir.name

            logging.info(f"Processing folder: {sub_dir.name} ({location_tag})")
            
            # Pre-calculate labels for this folder to avoid per-image overhead logic
            folder_labels = self._select_candidate_labels(location_tag)
            
            if not folder_labels:
                logging.warning("No candidate labels available! Check taxonomy/config.")
                continue

            for img_path in sub_dir.glob("*.[jJ][pP][gG]"):
                self.process_image(img_path, captured_date, location_tag, processed_dir, folder_labels)

    def process_image(self, img_path: Path, captured_date: str, location_tag: str, processed_dir: Path, candidate_labels: list):
        logging.info(f"--- Processing {img_path.name} ---")
        
        # 0. Deduplication Check
        file_hash = self._calculate_file_hash(img_path)
        if self.db.check_hash_exists(file_hash):
            logging.info(f"Skipping {img_path.name}: Already processed (Hash match).")
            return

        # 1. Quality Check
        blur_score = QualityChecker.calculate_blur_score(str(img_path))
        if blur_score < self.config['processing']['blur_threshold']:
            logging.warning(f"Skipping {img_path.name}: Sharpness ({blur_score:.2f}) below threshold.")
            return

        # 2. Detection
        boxes = self.detector.detect(str(img_path))
        if not boxes:
            logging.warning(f"No birds detected in {img_path.name}")
            return
        
        # We process the first detected bird for now
        main_box = boxes[0]
        
        # 3. Cropping and Resizing
        temp_cropped = processed_dir / f"temp_{img_path.name}"
        success = ImageProcessor.crop_and_resize(
            str(img_path), 
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
                self.recognizer = DongniaoRecognizer(
                    api_key=dn_conf.get('key'),
                    api_url=dn_conf.get('url')
                )
                logging.info("Initialized Dongniao Recognizer.")
            elif mode == 'api':
                # Generic API (HuggingFace)
                api_conf = rec_config.get('api', {})
                self.recognizer = APIBirdRecognizer(
                    api_url=api_conf.get('url'),
                    api_key=api_conf.get('key')
                )
                logging.info("Initialized HuggingFace API Recognizer.")
            else:
                # Default to local
                local_conf = rec_config.get('local', {})
                model_type = local_conf.get('model_type', 'bioclip')
                self.recognizer = LocalBirdRecognizer(
                    model_name=model_type,
                    device=self.device
                )
                logging.info(f"Initialized Local {model_type} Recognizer on {self.device}.")
        
        results = self.recognizer.predict(str(temp_cropped), candidate_labels)
        
        if not results:
            logging.warning(f"Recognition returned no results for {img_path.name}. Saving as Unknown.")
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
        # Initial filename guess
        base_filename = f"{captured_date}_{location_tag}_{chinese_name}_{conf_pct}pct"
        new_filename = f"{base_filename}.jpg"
        final_path = processed_dir / new_filename
        
        # Handle collisions
        if final_path.exists():
            new_filename = f"{base_filename}_{img_path.stem[-4:]}.jpg"
            final_path = processed_dir / new_filename
        
        # Perform move
        temp_cropped.rename(final_path)
        
        # Write EXIF
        tags = {
            "IPTC:Keywords": [chinese_name, location_tag, family_cn, sci_name],
            "XMP:Description": f"AI Identification: {chinese_name} ({conf_pct}%)"
        }
        self.exif_writer.write_metadata(str(final_path), tags)
        
        # 7. Database Entry
        from PIL import Image
        try:
            with Image.open(final_path) as img:
                w, h = img.size
        except Exception:
            w, h = 0, 0
            
        self.db.add_photo_record({
            'file_path': str(final_path.absolute()),
            'filename': new_filename,
            'original_path': str(img_path.absolute()), # Store original path
            'file_hash': file_hash, # Store hash for dedup
            'captured_date': captured_date,
            'location_tag': location_tag,
            'primary_bird_cn': chinese_name,
            'scientific_name': sci_name,
            'confidence_score': conf,
            'width': w,
            'height': h
        })
        
        logging.info(f"Successfully processed and archived: {new_filename}")

if __name__ == "__main__":
    runner = FeatherTracePipeline("config/settings.yaml")
    runner.run()