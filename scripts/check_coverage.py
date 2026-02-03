import sys
sys.path.insert(0, 'src')
import json
from metadata.ioc_manager import IOCManager

ioc = IOCManager('data/db/feathertrace.db')
tree = ioc.get_taxonomy_tree(include_empty=True)

# Count how many are Chinese vs Latin
order_cn_count = sum(1 for o in tree if o['order_cn'] and not o['order_cn'].isupper())
family_cn_count = 0
genus_cn_count = 0

for order in tree:
    for fam in order.get('families', []):
        if fam.get('family_cn') and not fam.get('family_cn').isupper():
            family_cn_count += 1
        for gen in fam.get('genera', []):
            if gen.get('genus_cn') and not gen.get('genus_cn').isupper():
                genus_cn_count += 1

total_orders = len(tree)
total_families = sum(len(o.get('families', [])) for o in tree)
total_genera = sum(len(f.get('genera', [])) for o in tree for f in o.get('families', []))

print(f"Orders: {order_cn_count}/{total_orders} have Chinese names")
print(f"Families: {family_cn_count}/{total_families} have Chinese names")
print(f"Genera: {genus_cn_count}/{total_genera} have Chinese names")

# Show orders without Chinese names
print("\nOrders without Chinese names:")
for o in tree:
    if o['order_cn'].isupper():
        print(f"  {o['order_cn']}")

# Show some sample families without Chinese names
print("\nSample families without Chinese names:")
count = 0
for order in tree:
    for fam in order.get('families', []):
        if fam.get('family_cn').isupper() and count < 10:
            print(f"  {fam['family_cn']} ({fam['order_cn']})")
            count += 1

# Show some sample genera without Chinese names
print("\nSample genera without Chinese names:")
count = 0
for order in tree:
    for fam in order.get('families', []):
        for gen in fam.get('genera', []):
            if gen.get('genus_cn').isupper() and count < 15:
                print(f"  {gen['genus_cn']} ({gen['family_cn']})")
                count += 1

ioc.close()
