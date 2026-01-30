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
        # Removed persistent self.cursor for thread safety
        self._init_db()

    def _init_db(self):
        # Taxonomy Table
        self.conn.execute('''
            CREATE TABLE IF NOT EXISTS taxonomy (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                scientific_name TEXT UNIQUE,
                chinese_name TEXT,
                family_cn TEXT,
                order_cn TEXT,
                genus_cn TEXT,
                genus_sci TEXT,
                family_sci TEXT,
                order_sci TEXT,
                english_name TEXT
            )
        ''')
        # Create index for faster search (basic indexes that should always exist)
        self.conn.execute('CREATE INDEX IF NOT EXISTS idx_sci_name ON taxonomy(scientific_name)')
        self.conn.execute('CREATE INDEX IF NOT EXISTS idx_cn_name ON taxonomy(chinese_name)')

        # Photos Table
        self.conn.execute('''
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

        # Scan History Table
        self.conn.execute('''
            CREATE TABLE IF NOT EXISTS scan_history (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                start_time TEXT,
                end_time TEXT,
                range_start TEXT,
                range_end TEXT,
                processed_count INTEGER,
                duration_seconds REAL,
                status TEXT
            )
        ''')

        # Migration - Photos table
        try:
            self.conn.execute("SELECT file_hash, original_path, candidates_json FROM photos LIMIT 1")
        except sqlite3.OperationalError:
            logging.info("Migrating database: Adding new columns to photos...")
            try: self.conn.execute("ALTER TABLE photos ADD COLUMN file_hash TEXT")
            except: pass
            try: self.conn.execute("ALTER TABLE photos ADD COLUMN original_path TEXT")
            except: pass
            try: self.conn.execute("ALTER TABLE photos ADD COLUMN candidates_json TEXT")
            except: pass

        # Migration - Taxonomy table (add genus, family_sci, order_sci, english_name)
        try:
            self.conn.execute("SELECT genus_cn, genus_sci, family_sci, order_sci, english_name FROM taxonomy LIMIT 1")
        except sqlite3.OperationalError:
            logging.info("Migrating database: Adding new columns to taxonomy...")
            try: self.conn.execute("ALTER TABLE taxonomy ADD COLUMN genus_cn TEXT")
            except: pass
            try: self.conn.execute("ALTER TABLE taxonomy ADD COLUMN genus_sci TEXT")
            except: pass
            try: self.conn.execute("ALTER TABLE taxonomy ADD COLUMN family_sci TEXT")
            except: pass
            try: self.conn.execute("ALTER TABLE taxonomy ADD COLUMN order_sci TEXT")
            except: pass
            try: self.conn.execute("ALTER TABLE taxonomy ADD COLUMN english_name TEXT")
            except: pass

            # After adding columns, create additional indexes
            try: self.conn.execute("CREATE INDEX IF NOT EXISTS idx_order ON taxonomy(order_cn, order_sci)")
            except: pass
            try: self.conn.execute("CREATE INDEX IF NOT EXISTS idx_family ON taxonomy(family_cn, family_sci)")
            except: pass
            try: self.conn.execute("CREATE INDEX IF NOT EXISTS idx_genus ON taxonomy(genus_cn, genus_sci)")
            except: pass

            self.conn.commit()

        self.conn.commit()

    def load_genus_mapping(self, cn_excel_path: str) -> Dict[str, str]:
        """
        从动物界-脊索动物门Excel文件加载属中文名映射
        返回 {属拉丁名: 属中文名} 字典
        """
        logging.info(f"Loading genus mapping from {cn_excel_path}...")
        try:
            df = pd.read_excel(cn_excel_path, engine='openpyxl')
            df.columns = [c.strip() for c in df.columns]

            mapping = {}
            for _, row in df.iterrows():
                genus_sci = str(row.get('属拉丁名', '')).strip()
                genus_cn = str(row.get('属中文名', '')).strip()
                if genus_sci and genus_cn and genus_sci != 'nan' and genus_cn != 'nan':
                    mapping[genus_sci] = genus_cn

            logging.info(f"Loaded {len(mapping)} genus mappings")
            return mapping

        except Exception as e:
            logging.error(f"Failed to load genus mapping: {e}")
            return {}

    def import_from_excel(self, excel_path: str, genus_mapping: Dict[str, str] = None,
                        order_mapping: Dict[str, str] = None, family_mapping: Dict[str, str] = None):
        """
        Import full IOC list from Excel into taxonomy table.

        Args:
            excel_path: Path to IOC Excel file
            genus_mapping: Optional {属拉丁名: 属中文名} mapping dictionary
            order_mapping: Optional {目拉丁名: 目中文名} mapping dictionary
            family_mapping: Optional {科拉丁名: 科中文名} mapping dictionary
        """
        logging.info(f"Importing taxonomy from {excel_path}...")
        if genus_mapping:
            logging.info(f"Using genus mapping with {len(genus_mapping)} entries")
        if order_mapping:
            logging.info(f"Using order mapping with {len(order_mapping)} entries")
        if family_mapping:
            logging.info(f"Using family mapping with {len(family_mapping)} entries")

        try:
            df = pd.read_excel(excel_path)
            df.columns = [c.strip() for c in df.columns]

            records = []
            for _, row in df.iterrows():
                sci = str(row.get('IOC_15.1', '')).strip()
                cn = str(row.get('Chinese', '')).strip()
                fam_cn = str(row.get('Family', '')).strip()
                ord_cn = str(row.get('Order', '')).strip()
                eng = str(row.get('English', '')).strip()

                if sci and sci != 'nan':
                    # Extract scientific names from IOC_15.1
                    # Example: "Acrocephalus arundinaceus" -> genus="Acrocephalus", species="arundinaceus"
                    parts = sci.split()
                    genus_sci = parts[0] if parts else ''

                    # Family and Order columns in IOC Excel are already Latin names
                    fam_sci = fam_cn  # Family column contains Latin names
                    ord_sci = ord_cn  # Order column contains Latin names

                    # Get Chinese names from mappings
                    genus_cn = genus_mapping.get(genus_sci, '') if genus_mapping else ''
                    family_cn = family_mapping.get(fam_sci, '') if family_mapping else ''
                    order_cn = order_mapping.get(ord_sci, '') if order_mapping else ''

                    # Use scientific names as fallback for Chinese names
                    final_genus_cn = genus_cn if genus_cn else genus_sci
                    final_family_cn = family_cn if family_cn else fam_sci
                    final_order_cn = order_cn if order_cn else ord_sci

                    records.append((
                        sci,        # scientific_name
                        cn,         # chinese_name
                        final_family_cn,   # family_cn
                        final_order_cn,   # order_cn
                        final_genus_cn,   # genus_cn
                        genus_sci,  # genus_sci
                        fam_sci,    # family_sci
                        ord_sci,    # order_sci
                        eng         # english_name
                    ))

            # Bulk upsert
            self.conn.executemany('''
                INSERT OR REPLACE INTO taxonomy
                (scientific_name, chinese_name, family_cn, order_cn,
                 genus_cn, genus_sci, family_sci, order_sci, english_name)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', records)
            self.conn.commit()
            logging.info(f"Successfully imported {len(records)} species into taxonomy.")

        except Exception as e:
            logging.error(f"Failed to import Excel: {e}")

    def get_bird_info(self, scientific_name: str) -> Optional[Dict]:
        cursor = self.conn.execute("SELECT * FROM taxonomy WHERE scientific_name=?", (scientific_name,))
        row = cursor.fetchone()
        return dict(row) if row else None

    def search_species(self, query: str, limit: int = 20) -> List[Dict]:
        q_like = f"%{query}%"
        q_start = f"{query}%"

        cursor = self.conn.execute('''
            SELECT scientific_name, chinese_name,
            CASE
                WHEN chinese_name = ? THEN 1
                WHEN chinese_name LIKE ? THEN 2
                WHEN chinese_name LIKE ? THEN 3
                ELSE 4
            END as relevance
            FROM taxonomy
            WHERE scientific_name LIKE ? OR chinese_name LIKE ?
            ORDER BY relevance ASC, LENGTH(chinese_name) ASC
            LIMIT ?
        ''', (query, q_start, q_like, q_like, q_like, limit))
        return [dict(row) for row in cursor.fetchall()]

    def get_taxonomy_tree(self, include_empty: bool = True, date_filter: str = None) -> List[Dict]:
        """
        获取完整的分类树结构（目-科-属-物种）

        Args:
            include_empty: 是否包含没有照片的层级
            date_filter: 可选日期过滤器，格式为 "YYYYMMDD"

        Returns:
            分类树列表，每个元素是一个目（Order）对象，包含其下的科、属、物种
        """
        # Build WHERE clause for date filter if needed
        date_where = ""
        params = []
        if date_filter:
            date_where = "AND p.captured_date = ?"
            params.append(date_filter)

        # Get all orders
        orders_sql = f'''
            SELECT DISTINCT order_cn, order_sci
            FROM taxonomy
            WHERE order_cn IS NOT NULL AND order_cn != ''
            ORDER BY order_cn
        '''
        orders = [dict(row) for row in self.conn.execute(orders_sql)]

        result = []
        for order in orders:
            # Count photos for this order
            order_count_sql = f'''
                SELECT COUNT(DISTINCT p.id)
                FROM taxonomy t
                LEFT JOIN photos p ON t.scientific_name = p.scientific_name
                WHERE t.order_cn = ? AND t.order_sci = ?
                {date_where}
            '''
            order_count = self.conn.execute(order_count_sql, [order['order_cn'], order['order_sci']] + params).fetchone()[0]

            if not include_empty and order_count == 0:
                continue

            # Get families for this order
            families_sql = f'''
                SELECT DISTINCT family_cn, family_sci
                FROM taxonomy
                WHERE order_cn = ? AND family_cn IS NOT NULL AND family_cn != ''
                ORDER BY family_cn
            '''
            families = [dict(row) for row in self.conn.execute(families_sql, [order['order_cn']])]

            families_data = []
            for family in families:
                # Count photos for this family
                family_count_sql = f'''
                    SELECT COUNT(DISTINCT p.id)
                    FROM taxonomy t
                    LEFT JOIN photos p ON t.scientific_name = p.scientific_name
                    WHERE t.family_cn = ? AND t.family_sci = ?
                    {date_where}
                '''
                family_count = self.conn.execute(family_count_sql, [family['family_cn'], family['family_sci']] + params).fetchone()[0]

                if not include_empty and family_count == 0:
                    continue

                # Get genera for this family
                genera_sql = f'''
                    SELECT DISTINCT genus_cn, genus_sci
                    FROM taxonomy
                    WHERE family_cn = ? AND genus_sci IS NOT NULL AND genus_sci != ''
                    ORDER BY genus_sci
                '''
                genera = [dict(row) for row in self.conn.execute(genera_sql, [family['family_cn']])]

                genera_data = []
                for genus in genera:
                    # Count photos for this genus
                    genus_count_sql = f'''
                        SELECT COUNT(DISTINCT p.id)
                        FROM taxonomy t
                        LEFT JOIN photos p ON t.scientific_name = p.scientific_name
                        WHERE t.genus_sci = ?
                        {date_where}
                    '''
                    genus_count = self.conn.execute(genus_count_sql, [genus['genus_sci']] + params).fetchone()[0]

                    if not include_empty and genus_count == 0:
                        continue

                    # Get species for this genus
                    species_sql = f'''
                        SELECT scientific_name, chinese_name, english_name
                        FROM taxonomy
                        WHERE genus_sci = ?
                        ORDER BY chinese_name
                    '''
                    species_list = [dict(row) for row in self.conn.execute(species_sql, [genus['genus_sci']])]

                    # Count photos for each species
                    species_data = []
                    for sp in species_list:
                        species_count_sql = f'''
                            SELECT COUNT(DISTINCT p.id)
                            FROM taxonomy t
                            LEFT JOIN photos p ON t.scientific_name = p.scientific_name
                            WHERE t.scientific_name = ?
                            {date_where}
                        '''
                        species_count = self.conn.execute(species_count_sql, [sp['scientific_name']] + params).fetchone()[0]

                        if include_empty or species_count > 0:
                            sp['photo_count'] = species_count
                            species_data.append(sp)

                    if include_empty or species_data:
                        genus['species_count'] = len(species_data)
                        genus['photo_count'] = genus_count
                        genus['species'] = species_data
                        genera_data.append(genus)

                if include_empty or genera_data:
                    family['genera_count'] = len(genera_data)
                    family['photo_count'] = family_count
                    family['genera'] = genera_data
                    families_data.append(family)

            if include_empty or families_data:
                order['families_count'] = len(families_data)
                order['photo_count'] = order_count
                order['families'] = families_data
                result.append(order)

        return result

    def get_stats_by_level(self, level: str, date_filter: str = None) -> List[Dict]:
        """
        按层级统计物种数量

        Args:
            level: 'order', 'family', 'genus', 'species'
            date_filter: 可选日期过滤器，格式为 "YYYYMMDD"

        Returns:
            统计结果列表，每个元素包含名称和照片数量
        """
        date_where = ""
        params = []
        if date_filter:
            date_where = "AND p.captured_date = ?"
            params.append(date_filter)

        if level == 'order':
            sql = f'''
                SELECT DISTINCT t.order_cn as name, t.order_sci as sci, COUNT(DISTINCT p.id) as count
                FROM taxonomy t
                LEFT JOIN photos p ON t.scientific_name = p.scientific_name
                WHERE t.order_cn IS NOT NULL AND t.order_cn != ''
                {date_where}
                GROUP BY t.order_cn, t.order_sci
                ORDER BY count DESC, t.order_cn
            '''
        elif level == 'family':
            sql = f'''
                SELECT DISTINCT t.family_cn as name, t.family_sci as sci, COUNT(DISTINCT p.id) as count
                FROM taxonomy t
                LEFT JOIN photos p ON t.scientific_name = p.scientific_name
                WHERE t.family_cn IS NOT NULL AND t.family_cn != ''
                {date_where}
                GROUP BY t.family_cn, t.family_sci
                ORDER BY count DESC, t.family_cn
            '''
        elif level == 'genus':
            sql = f'''
                SELECT DISTINCT t.genus_cn as name, t.genus_sci as sci, COUNT(DISTINCT p.id) as count
                FROM taxonomy t
                LEFT JOIN photos p ON t.scientific_name = p.scientific_name
                WHERE t.genus_cn IS NOT NULL AND t.genus_cn != ''
                {date_where}
                GROUP BY t.genus_cn, t.genus_sci
                ORDER BY count DESC, t.genus_cn
            '''
        elif level == 'species':
            sql = f'''
                SELECT t.chinese_name as name, t.scientific_name as sci, COUNT(DISTINCT p.id) as count
                FROM taxonomy t
                LEFT JOIN photos p ON t.scientific_name = p.scientific_name
                {date_where}
                GROUP BY t.chinese_name, t.scientific_name
                ORDER BY count DESC, t.chinese_name
            '''
        else:
            return []

        return [dict(row) for row in self.conn.execute(sql, params)]

    def search_taxonomy(self, query: str, limit: int = 20) -> List[Dict]:
        """
        搜索分类信息（支持目、科、属、物种）

        Args:
            query: 搜索关键词
            limit: 返回结果数量限制

        Returns:
            匹配的分类信息列表，包含层级类型和匹配名称
        """
        q_like = f"%{query}%"

        # Search all levels
        results = []

        # Search orders
        cursor = self.conn.execute('''
            SELECT DISTINCT 'order' as level, order_cn as name_cn, order_sci as name_sci
            FROM taxonomy
            WHERE order_cn LIKE ?
            ORDER BY order_cn
            LIMIT ?
        ''', (q_like, limit))
        results.extend([dict(row) for row in cursor.fetchall()])

        # Search families
        cursor = self.conn.execute('''
            SELECT DISTINCT 'family' as level, family_cn as name_cn, family_sci as name_sci
            FROM taxonomy
            WHERE family_cn LIKE ?
            ORDER BY family_cn
            LIMIT ?
        ''', (q_like, limit))
        results.extend([dict(row) for row in cursor.fetchall()])

        # Search genera
        cursor = self.conn.execute('''
            SELECT DISTINCT 'genus' as level, genus_cn as name_cn, genus_sci as name_sci
            FROM taxonomy
            WHERE genus_cn LIKE ?
            ORDER BY genus_cn
            LIMIT ?
        ''', (q_like, limit))
        results.extend([dict(row) for row in cursor.fetchall()])

        # Search species (relevance-weighted)
        cursor = self.conn.execute('''
            SELECT DISTINCT 'species' as level, chinese_name as name_cn, scientific_name as name_sci,
            CASE
                WHEN chinese_name = ? THEN 1
                WHEN chinese_name LIKE ? THEN 2
                WHEN chinese_name LIKE ? THEN 3
                ELSE 4
            END as relevance
            FROM taxonomy
            WHERE chinese_name LIKE ?
            ORDER BY relevance ASC, LENGTH(chinese_name) ASC
            LIMIT ?
        ''', (query, f"{query}%", q_like, q_like, limit))
        results.extend([dict(row) for row in cursor.fetchall()])

        return results[:limit]

    def check_hash_exists(self, file_hash: str) -> bool:
        if not file_hash: return False
        cursor = self.conn.execute("SELECT 1 FROM photos WHERE file_hash = ? LIMIT 1", (file_hash,))
        return cursor.fetchone() is not None

    def add_photo_record(self, record: Dict):
        keys = ', '.join(record.keys())
        placeholders = ', '.join(['?'] * len(record))
        values = tuple(record.values())
        
        sql = f"INSERT INTO photos ({keys}) VALUES ({placeholders})"
        cursor = self.conn.execute(sql, values)
        self.conn.commit()
        return cursor.lastrowid
        
    def update_photo_species(self, photo_id: int, scientific_name: str, chinese_name: str):
        self.conn.execute('''
            UPDATE photos 
            SET scientific_name = ?, primary_bird_cn = ?, confidence_score = 1.0
            WHERE id = ?
        ''', (scientific_name, chinese_name, photo_id))
        self.conn.commit()

    def add_scan_history(self, record: Dict):
        keys = ', '.join(record.keys())
        placeholders = ', '.join(['?'] * len(record))
        values = tuple(record.values())
        
        sql = f"INSERT INTO scan_history ({keys}) VALUES ({placeholders})"
        self.conn.execute(sql, values)
        self.conn.commit()

    def get_recent_scans(self, limit: int = 5) -> List[Dict]:
        cursor = self.conn.execute("SELECT * FROM scan_history ORDER BY id DESC LIMIT ?", (limit,))
        return [dict(row) for row in cursor.fetchall()]

    def close(self):
        self.conn.close()