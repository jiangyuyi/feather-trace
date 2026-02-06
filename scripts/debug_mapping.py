import sys
sys.path.insert(0, 'src')
import pandas as pd
from metadata.ioc_manager import IOCManager

# Load genus mapping
ioc = IOCManager('data/db/wingscribe.db')
genus_mapping = ioc.load_csv_mapping('data/references/bird_genus_mapping.csv', 'Genus_SCI', 'Genus_CN')

# Check specific genera from Excel
test_genera = ['Struthio', 'Rhea', 'Apteryx', 'Casuarius', 'Abroscopus', 'Accipiter']
print("Genus mapping lookup test:")
for g in test_genera:
    cn = genus_mapping.get(g, 'NOT FOUND')
    print(f"  {g} -> {repr(cn)}")

# Check what was imported
print("\nDatabase check:")
cur = ioc.conn.execute("SELECT genus_cn, genus_sci FROM taxonomy WHERE genus_sci IN (?, ?, ?)", test_genera[:3])
for r in cur.fetchall():
    print(f"  genus_cn: {repr(r['genus_cn'])}, genus_sci: {r['genus_sci']}")

# Check order mapping
order_mapping = ioc.load_csv_mapping('data/references/bird_order_mapping.csv', 'Order_SCI', 'Order_CN')
print("\nOrder mapping lookup test:")
for o in ['STRUTHIONIFORMES', 'RHEIFORMES', 'PASSERIFORMES']:
    cn = order_mapping.get(o, 'NOT FOUND')
    print(f"  {o} -> {repr(cn)}")

ioc.close()
