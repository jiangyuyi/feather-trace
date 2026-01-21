import sys
import os
import yaml
from pathlib import Path
from unittest.mock import MagicMock

# Add src to sys.path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from src.pipeline_runner import FeatherTracePipeline
from PIL import Image

def test_pipeline_mocked():
    print("--- Testing Pipeline (Mocked) ---")
    
    # 1. Setup paths and config
    config_path = "config/settings.yaml"
    with open(config_path, 'r') as f:
        config = yaml.safe_load(f)
    
    raw_test_dir = Path("data/raw/20231020_TestPark")
    raw_test_dir.mkdir(parents=True, exist_ok=True)
    
    img_path = raw_test_dir / "test_bird.jpg"
    img = Image.new('RGB', (1000, 1000), color=(100, 150, 200))
    img.save(img_path)
    
    # 2. Init Pipeline
    pipeline = FeatherTracePipeline(config_path)
    # We skip re-importing the huge excel in the mock test to save time, 
    # unless the DB is empty or we specifically want to test it.
    # But since we changed the method name, we must update the call if it's there.
    # Let's just comment it out or use the new name if we really need to import.
    # Given the previous step populated the DB, we might not need to import again.
    # However, 'pipeline' init creates a fresh IOCManager which connects to the existing DB.
    # pipeline.db.import_ioc_data(config['paths']['ioc_list_path']) 
    
    pipeline.config['processing']['blur_threshold'] = 0.0
    
    # 3. Mock the heavy components
    # Mock detector to return a box
    pipeline.detector.detect = MagicMock(return_value=[[100, 100, 500, 500]])
    
    # Mock recognizer
    mock_recognizer = MagicMock()
    mock_recognizer.predict = MagicMock(return_value=[
        {"scientific_name": "Pycnonotus sinensis", "confidence": 0.98}
    ])
    pipeline.recognizer = mock_recognizer
    
    # Mock exif writer to avoid needing the tool
    pipeline.exif_writer.write_metadata = MagicMock(return_value=True)
    
    # 4. Run the processing for one folder
    pipeline.run()
    
    # 5. Verify results
    processed_files = list(Path("data/processed").glob("*.jpg"))
    print(f"Processed files: {[f.name for f in processed_files]}")
    
    assert len(processed_files) > 0
    # Check if DB has the record
    pipeline.db.cursor.execute("SELECT * FROM photos WHERE filename LIKE '%白头鹎%'")
    record = pipeline.db.cursor.fetchone()
    print(f"DB Record: {record}")
    assert record is not None
    
    print("--- Pipeline Mock Test Passed ---")

if __name__ == "__main__":
    test_pipeline_mocked()
