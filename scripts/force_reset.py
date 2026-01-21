import os
import shutil
import time
import sqlite3
from pathlib import Path

def force_reset():
    root = Path(__file__).parent.parent
    db_path = root / "data/db/feathertrace.db"
    processed_dir = root / "data/processed"

    print("=== Force Reset Tool ===")
    
    # 1. Try to remove DB
    if db_path.exists():
        print(f"Removing DB: {db_path}")
        try:
            os.remove(db_path)
            print("DB removed successfully.")
        except PermissionError:
            print("ERROR: Database file is locked!")
            print("Please STOP the running web server (python src/web/app.py) first.")
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
    
    # 3. Re-init DB (Re-import Taxonomy)
    # We need to run import_ioc_data.py logic again
    print("\n--- Re-initializing Database & Taxonomy ---")
    try:
        import sys
        sys.path.append(str(root))
        from scripts.import_ioc_data import import_data
        import_data()
        print("Database re-initialized successfully.")
    except Exception as e:
        print(f"Failed to re-init DB: {e}")

if __name__ == "__main__":
    force_reset()
