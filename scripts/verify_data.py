import sys
sys.path.insert(0, 'src')
from metadata.ioc_manager import IOCManager
import json

ioc = IOCManager('data/db/wingscribe.db')

# Get taxonomy tree and save to file for verification
tree = ioc.get_taxonomy_tree(include_empty=True)

# Save to file
with open('data/taxonomy_debug.json', 'w', encoding='utf-8') as f:
    json.dump(tree, f, ensure_ascii=False, indent=2)

print("Taxonomy tree saved to data/taxonomy_debug.json")
print(f"Total orders: {len(tree)}")

# Show first 3 orders
for order in tree[:3]:
    print(f"\nOrder: {order['order_cn']} ({order['order_sci']})")
    print(f"  Families: {len(order.get('families', []))}")
    for fam in order.get('families', [])[:2]:
        print(f"    Family: {fam['family_cn']} ({fam['family_sci']})")
        for gen in fam.get('genera', [])[:2]:
            print(f"      Genus: {gen['genus_cn']} ({gen['genus_sci']})")

ioc.close()
