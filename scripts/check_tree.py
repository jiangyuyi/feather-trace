import sys
sys.path.insert(0, 'src')
from metadata.ioc_manager import IOCManager
import json

ioc = IOCManager('data/db/wingscribe.db')
tree = ioc.get_taxonomy_tree(include_empty=True)

# Find Passeriformes
passeriformes = [o for o in tree if 'PASSER' in o['order_sci']][0]

# Save to file
with open('data/passeriformes.json', 'w', encoding='utf-8') as f:
    json.dump(passeriformes, f, ensure_ascii=False, indent=2)

# Count coverage
def has_chinese(s):
    if not s:
        return False
    for char in str(s):
        code = ord(char)
        if 0x4e00 <= code <= 0x9fff or 0x3400 <= code <= 0x4dbf:
            return True
    return False

order_cn = has_chinese(passeriformes.get('order_cn', ''))
families_with_cn = sum(1 for f in passeriformes['families'] if has_chinese(f.get('family_cn', '')))
genera_with_cn = sum(1 for o in tree for f in o.get('families', []) for g in f.get('genera', []) if has_chinese(g.get('genus_cn', '')))

print(f"Order: {passeriformes['order_cn']} ({passeriformes['order_sci']})")
print(f"Has Chinese order name: {order_cn}")
print(f"Families in Passeriformes: {len(passeriformes['families'])}")
print(f"Families with Chinese names: {families_with_cn}")

# Show some families
print("\nSample families:")
for fam in passeriformes['families'][:10]:
    print(f"  {fam['family_cn']} ({fam['family_sci']})")

# Save overall taxonomy
with open('data/taxonomy_debug.json', 'w', encoding='utf-8') as f:
    json.dump(tree, f, ensure_ascii=False, indent=2)

print("\nSaved to data/passeriformes.json and data/taxonomy_debug.json")

ioc.close()
