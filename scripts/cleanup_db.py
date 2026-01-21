import sqlite3
import yaml
from pathlib import Path
import os

def cleanup_db():
    # Get project root directory (scripts/cleanup_db.py -> scripts -> root)
    BASE_DIR = Path(__file__).parent.parent.absolute()
    
    config_path = BASE_DIR / "config" / "settings.yaml"
    with open(config_path, 'r', encoding='utf-8') as f:
        config = yaml.safe_load(f)

    db_path = BASE_DIR / config['paths']['db_path']
    processed_dir = BASE_DIR / config['paths']['processed_dir']

    print(f"Cleaning up database at: {db_path}")
    print(f"Checking files in: {processed_dir}")

    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()

    cursor.execute("SELECT id, filename, file_path FROM photos")
    rows = cursor.fetchall()
    
    deleted_count = 0
    updated_count = 0
    
    for row in rows:
        photo_id = row['id']
        filename = row['filename']
        # Check if the filename itself exists in the processed directory
        actual_path = processed_dir / filename
        
        if not actual_path.exists():
            # Maybe the file exists with a different name but file_path is correct?
            # Or maybe it's just gone.
            print(f"File missing: {filename}")
            cursor.execute("DELETE FROM photos WHERE id = ?", (photo_id,))
            deleted_count += 1
        else:
            # File exists, ensure file_path in DB is absolute and correct
            if row['file_path'] != str(actual_path.absolute()):
                cursor.execute("UPDATE photos SET file_path = ? WHERE id = ?", 
                               (str(actual_path.absolute()), photo_id))
                updated_count += 1

    conn.commit()
    conn.close()
    print(f"Cleanup complete. Deleted {deleted_count} records, Updated {updated_count} paths.")

if __name__ == "__main__":
    cleanup_db()
