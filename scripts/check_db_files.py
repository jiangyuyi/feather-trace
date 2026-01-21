import sqlite3
import yaml
from pathlib import Path

config_path = Path("config/settings.yaml")
with open(config_path, 'r', encoding='utf-8') as f:
    config = yaml.safe_load(f)

db_path = config['paths']['db_path']
conn = sqlite3.connect(db_path)
conn.row_factory = sqlite3.Row
cursor = conn.cursor()

cursor.execute("SELECT filename, file_path FROM photos")
rows = cursor.fetchall()
for row in rows:
    print(f"DB Filename: {row['filename']}")
    print(f"DB File Path: {row['file_path']}")
    p = Path(row['file_path'])
    print(f"Exists on disk: {p.exists()}")
    print("-" * 20)

conn.close()
