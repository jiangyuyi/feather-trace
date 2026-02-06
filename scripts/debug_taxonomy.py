import sys
sys.path.insert(0, 'src')
import pandas as pd

df = pd.read_excel('data/references/Multiling IOC 15.1_d.xlsx')
df.columns = [str(c).strip() for c in df.columns]

print('First 10 species with genus:')
for i, row in df.head(10).iterrows():
    parts = str(row.get('IOC_15.1', '')).split()
    genus_sci = parts[0] if parts else ''
    print(f"  {row['IOC_15.1']} -> genus: {genus_sci}, chinese: {row.get('Chinese', '')}")

# Check genus_mapping keys
from metadata.ioc_manager import IOCManager
ioc = IOCManager('data/db/wingscribe.db')
genus_mapping = ioc.load_csv_mapping('data/references/bird_genus_mapping.csv', 'Genus_SCI', 'Genus_CN')
print(f"\nGenus mapping sample (first 5):")
for k, v in list(genus_mapping.items())[:5]:
    print(f"  {k} -> {v}")
ioc.close()
