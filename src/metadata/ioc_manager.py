import sqlite3
import logging
import pandas as pd
from pathlib import Path
from typing import List, Dict, Optional

class IOCManager:
    def __init__(self, db_path: str):
        self.db_path = db_path
        self.conn = sqlite3.connect(db_path, check_same_thread=False)
        self.conn.row_factory = sqlite3.Row
        self.cursor = self.conn.cursor()
        self._init_db()

    def _init_db(self):
        # Taxonomy Table
        self.cursor.execute('''
            CREATE TABLE IF NOT EXISTS taxonomy (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                scientific_name TEXT UNIQUE,
                chinese_name TEXT,
                family_cn TEXT,
                order_cn TEXT
            )
        ''')
        # Create index for faster search
        self.cursor.execute('CREATE INDEX IF NOT EXISTS idx_sci_name ON taxonomy(scientific_name)')
        self.cursor.execute('CREATE INDEX IF NOT EXISTS idx_cn_name ON taxonomy(chinese_name)')

        # Photos Table
        # Added file_hash and original_path for deduplication and raw mapping
        self.cursor.execute('''
            CREATE TABLE IF NOT EXISTS photos (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                file_path TEXT,
                filename TEXT,
                original_path TEXT,
                file_hash TEXT,
                captured_date TEXT,
                location_tag TEXT,
                primary_bird_cn TEXT,
                scientific_name TEXT,
                confidence_score REAL,
                width INTEGER,
                height INTEGER
            )
        ''')
        
        # Migration: Check if new columns exist, if not add them (for existing dbs)
        try:
            self.cursor.execute("SELECT file_hash, original_path FROM photos LIMIT 1")
        except sqlite3.OperationalError:
            logging.info("Migrating database: Adding file_hash and original_path columns...")
            try:
                self.cursor.execute("ALTER TABLE photos ADD COLUMN file_hash TEXT")
            except: pass
            try:
                self.cursor.execute("ALTER TABLE photos ADD COLUMN original_path TEXT")
            except: pass
            self.conn.commit()

        self.conn.commit()

    def import_from_excel(self, excel_path: str):
        """
        Import full IOC list from Excel into taxonomy table.
        """
        logging.info(f"Importing taxonomy from {excel_path}...")
        try:
            df = pd.read_excel(excel_path)
            # Normalize column names just in case
            df.columns = [c.strip() for c in df.columns]
            
            # Prepare data
            records = []
            for _, row in df.iterrows():
                sci = str(row.get('IOC_15.1', '')).strip()
                cn = str(row.get('Chinese', '')).strip()
                fam = str(row.get('Family', '')).strip()
                ordr = str(row.get('Order', '')).strip()
                
                if sci and sci != 'nan':
                    records.append((sci, cn, fam, ordr))
            
            # Bulk upsert
            self.cursor.executemany('''
                INSERT OR REPLACE INTO taxonomy (scientific_name, chinese_name, family_cn, order_cn)
                VALUES (?, ?, ?, ?)
            ''', records)
            self.conn.commit()
            logging.info(f"Successfully imported {len(records)} species into taxonomy.")
            
        except Exception as e:
            logging.error(f"Failed to import Excel: {e}")

    def get_bird_info(self, scientific_name: str) -> Optional[Dict]:
        self.cursor.execute("SELECT * FROM taxonomy WHERE scientific_name=?", (scientific_name,))
        row = self.cursor.fetchone()
        if row:
            return dict(row)
        return None

    def search_species(self, query: str, limit: int = 20) -> List[Dict]:
        """
        Search for species by Latin or Chinese name.
        """
        q = f"%{query}%"
        self.cursor.execute('''
            SELECT scientific_name, chinese_name 
            FROM taxonomy 
            WHERE scientific_name LIKE ? OR chinese_name LIKE ?
            LIMIT ?
        ''', (q, q, limit))
        return [dict(row) for row in self.cursor.fetchall()]

    def check_hash_exists(self, file_hash: str) -> bool:
        """
        Check if a file with this hash has already been processed.
        """
        if not file_hash: return False
        self.cursor.execute("SELECT 1 FROM photos WHERE file_hash = ? LIMIT 1", (file_hash,))
        return self.cursor.fetchone() is not None

    def add_photo_record(self, record: Dict):
        keys = ', '.join(record.keys())
        placeholders = ', '.join(['?'] * len(record))
        values = tuple(record.values())
        
        sql = f"INSERT INTO photos ({keys}) VALUES ({placeholders})"
        self.cursor.execute(sql, values)
        self.conn.commit()
        return self.cursor.lastrowid
        
    def update_photo_species(self, photo_id: int, scientific_name: str, chinese_name: str):
        self.cursor.execute('''
            UPDATE photos 
            SET scientific_name = ?, primary_bird_cn = ?, confidence_score = 1.0
            WHERE id = ?
        ''', (scientific_name, chinese_name, photo_id))
        self.conn.commit()

    def close(self):
        self.conn.close()