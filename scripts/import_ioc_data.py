import yaml
import sys
import os
from pathlib import Path

# Add src to path
sys.path.append(str(Path(__file__).parent.parent))
from src.metadata.ioc_manager import IOCManager

def import_data():
    config_path = Path("config/settings.yaml")
    with open(config_path, 'r', encoding='utf-8') as f:
        config = yaml.safe_load(f)
    
    excel_path = config['paths']['ioc_list_path']
    db_path = config['paths']['db_path']
    
    if not Path(excel_path).exists():
        print(f"Error: Excel file not found at {excel_path}")
        return

    print(f"Connecting to DB at {db_path}...")
    manager = IOCManager(db_path)
    
    print("Starting import...")
    manager.import_from_excel(excel_path)
    
    print("Verification check (first 5 records):")
    cursor = manager.conn.cursor()
    cursor.execute("SELECT * FROM taxonomy LIMIT 5")
    for row in cursor.fetchall():
        print(dict(row))
        
    manager.close()

if __name__ == "__main__":
    import_data()
