import sys
sys.path.insert(0, 'src')
from metadata.ioc_manager import IOCManager
import json

# Check if a string contains Chinese characters
def has_chinese(s):
    if not s:
        return False
    for char in str(s):
        code = ord(char)
        # Common Chinese character ranges
        if 0x4e00 <= code <= 0x9fff or 0x3400 <= code <= 0x4dbf:
            return True
    return False

ioc = IOCManager('data/db/wingscribe.db')
tree = ioc.get_taxonomy_tree(include_empty=True)

# Check coverage with proper Chinese detection
order_cn = sum(1 for o in tree if has_chinese(o.get('order_cn', '')))
family_cn = sum(1 for o in tree for f in o.get('families', []) if has_chinese(f.get('family_cn', '')))
genus_cn = sum(1 for o in tree for f in o.get('families', []) for g in f.get('genera', []) if has_chinese(g.get('genus_cn', '')))

total_orders = len(tree)
total_families = sum(len(o.get('families', [])) for o in tree)
total_genera = sum(len(f.get('genera', [])) for o in tree for f in o.get('families', []))

print(f"Orders with Chinese names: {order_cn}/{total_orders}")
print(f"Families with Chinese names: {family_cn}/{total_families}")
print(f"Genera with Chinese names: {genus_cn}/{total_genera}")

# Show some genera without Chinese names
print("\n=== Genera without Chinese names (first 20) ===")
count = 0
for order in tree:
    for fam in order.get('families', []):
        for gen in fam.get('genera', []):
            if not has_chinese(gen.get('genus_cn', '')) and count < 20:
                print(f"  {gen['genus_cn']} ({fam['family_cn']})")
                count += 1

# Show some families without Chinese names
print("\n=== Families without Chinese names (first 10) ===")
count = 0
for order in tree:
    for fam in order.get('families', []):
        if not has_chinese(fam.get('family_cn', '')) and count < 10:
            print(f"  {fam['family_cn']} ({order['order_cn']})")
            count += 1

# Save to file
with open('data/taxonomy_debug.json', 'w', encoding='utf-8') as f:
    json.dump(tree, f, ensure_ascii=False, indent=2)

ioc.close()
