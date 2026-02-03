import sys
sys.path.insert(0, 'src')
import pandas as pd
from metadata.ioc_manager import IOCManager

# Load Excel and get all unique genera
df = pd.read_excel('data/references/Multiling IOC 15.1_d.xlsx')
df.columns = [str(c).strip() for c in df.columns]

all_genera = set()
for _, row in df.iterrows():
    parts = str(row.get('IOC_15.1', '')).split()
    if parts:
        genus_sci = parts[0]
        all_genera.add(genus_sci)

print(f"Total unique genera in IOC Excel: {len(all_genera)}")

# Load genus mapping
ioc = IOCManager('data/db/feathertrace.db')
genus_mapping = ioc.load_csv_mapping('data/references/bird_genus_mapping.csv', 'Genus_SCI', 'Genus_CN')
print(f"Genera in genus_mapping.csv: {len(genus_mapping)}")

# Find missing genera
missing = all_genera - set(genus_mapping.keys())
print(f"\nMissing genera count: {len(missing)}")
print("Sample missing genera (first 20):")
for g in sorted(list(missing))[:20]:
    print(f"  {g}")

# Check order mapping
order_mapping = ioc.load_csv_mapping('data/references/bird_order_mapping.csv', 'Order_SCI', 'Order_CN')
all_orders = set(df['Order'].unique())
print(f"\nTotal unique orders in IOC Excel: {len(all_orders)}")
print(f"Orders in bird_order_mapping.csv: {len(order_mapping)}")

missing_orders = all_orders - set(order_mapping.keys())
print(f"Missing orders count: {len(missing_orders)}")
print("Sample missing orders:")
for o in sorted(list(missing_orders))[:10]:
    print(f"  {o}")

ioc.close()
