import os
import shutil
import time
import sys
import yaml
from pathlib import Path

# Add project root to path
BASE_DIR = Path(__file__).parent.parent.absolute()
sys.path.append(str(BASE_DIR))

from src.metadata.ioc_manager import IOCManager

def force_reset():
    config_path = BASE_DIR / "config" / "settings.yaml"
    with open(config_path, 'r', encoding='utf-8') as f:
        config = yaml.safe_load(f)

    db_path = BASE_DIR / config['paths']['db_path']
    processed_dir = BASE_DIR / config['paths']['processed_dir']

    print("=== Force Reset Tool ===")
    print("This will DELETE the database and ALL processed images.")
    print("Please ensure the Web Server is STOPPED.")
    
    confirm = input("Type 'DELETE' to confirm: ")
    if confirm != "DELETE":
        print("Cancelled.")
        return

    # 1. Try to remove DB
    if db_path.exists():
        print(f"Removing DB: {db_path}")
        try:
            os.remove(db_path)
            print("DB removed successfully.")
        except PermissionError:
            print("ERROR: Database file is locked!")
            print("Please STOP any running python processes (web/pipeline).")
            return
    else:
        print("DB file not found (already deleted).")

    # 2. Clear Processed
    print(f"Clearing processed directory: {processed_dir}")
    if processed_dir.exists():
        for item in processed_dir.iterdir():
            try:
                if item.is_file() or item.is_symlink():
                    item.unlink()
                elif item.is_dir():
                    shutil.rmtree(item)
            except Exception as e:
                print(f"Failed to delete {item}: {e}")
    else:
        os.makedirs(processed_dir, exist_ok=True)
        
    print("Processed directory cleared.")
    
    # 3. Re-init DB
    print("\n--- Re-initializing Database & Taxonomy ---")
    try:
        manager = IOCManager(str(db_path))
        
        # Import taxonomy
        excel_path = BASE_DIR / config['paths']['ioc_list_path']
        if excel_path.exists():
            print(f"Importing taxonomy from {excel_path}...")
            manager.import_from_excel(str(excel_path))
        else:
            print(f"Warning: IOC Excel not found at {excel_path}")
            
        manager.close()
        print("Database re-initialized successfully.")
    except Exception as e:
        print(f"Failed to re-init DB: {e}")

if __name__ == "__main__":
    force_reset()
