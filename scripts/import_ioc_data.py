import yaml
import sys
import os
from pathlib import Path
import csv

# Add src to path
sys.path.append(str(Path(__file__).parent.parent))
from src.metadata.ioc_manager import IOCManager

def load_csv_mapping(csv_path: str) -> dict:
    """从CSV文件加载映射关系"""
    mapping = {}
    if Path(csv_path).exists():
        with open(csv_path, 'r', encoding='utf-8-sig') as f:
            reader = csv.DictReader(f)
            for row in reader:
                key = row.get(list(row.keys())[0], '')  # 第一列作为key
                value = row.get(list(row.keys())[1], '')  # 第二列作为value
                if key and value:
                    mapping[key] = value
    return mapping

def import_data():
    config_path = Path("config/settings.yaml")
    with open(config_path, 'r', encoding='utf-8') as f:
        config = yaml.safe_load(f)

    excel_path = config['paths']['ioc_list_path']
    db_path = config['paths']['db_path']
    refs_path = Path(config['paths'].get('references_path', 'data/references'))

    # Check for Chinese taxonomy Excel file (optional)
    cn_excel_path = config['paths'].get('cn_taxonomy_path')

    if not Path(excel_path).exists():
        print(f"Error: IOC Excel file not found at {excel_path}")
        return

    print(f"Connecting to DB at {db_path}...")
    manager = IOCManager(db_path)

    # Load genus mapping if Chinese taxonomy file exists
    genus_mapping = {}
    if cn_excel_path and Path(cn_excel_path).exists():
        print(f"Loading genus mapping from {cn_excel_path}...")
        genus_mapping = manager.load_genus_mapping(cn_excel_path)
        print(f"Loaded {len(genus_mapping)} genus mappings")
    else:
        print("No Chinese taxonomy file found, proceeding without genus Chinese names")

    # Load order, family, genus Chinese mappings from CSV files (if available)
    order_mapping = load_csv_mapping(refs_path / 'bird_order_mapping.csv')
    family_mapping = load_csv_mapping(refs_path / 'bird_family_mapping.csv')
    genus_cn_mapping = load_csv_mapping(refs_path / 'bird_genus_mapping.csv')

    # Merge genus mappings (prioritize genus_cn_mapping from CSV)
    genus_mapping.update(genus_cn_mapping)

    if order_mapping:
        print(f"Loaded {len(order_mapping)} order mappings")
    if family_mapping:
        print(f"Loaded {len(family_mapping)} family mappings")
    if genus_cn_mapping:
        print(f"Loaded {len(genus_cn_mapping)} genus mappings from CSV")

    print("Starting import...")
    manager.import_from_excel(excel_path,
                             genus_mapping=genus_mapping,
                             order_mapping=order_mapping,
                             family_mapping=family_mapping)

    print("Verification check (first 5 records):")
    cursor = manager.conn.cursor()
    cursor.execute("SELECT * FROM taxonomy LIMIT 5")
    for row in cursor.fetchall():
        print(dict(row))

    print(f"\nTotal species in database: {cursor.execute('SELECT COUNT(*) FROM taxonomy').fetchone()[0]}")

    manager.close()
    print("Import completed successfully!")

if __name__ == "__main__":
    import_data()
