import sys
sys.path.insert(0, 'src')
from metadata.ioc_manager import IOCManager
import json

ioc = IOCManager('data/db/wingscribe.db')
tree = ioc.get_taxonomy_tree(include_empty=True)

# Save to file for inspection (no console output)
with open('data/taxonomy_debug.json', 'w', encoding='utf-8') as f:
    json.dump(tree, f, ensure_ascii=False, indent=2)

# Check coverage
order_cn = sum(1 for o in tree if o['order_cn'] and not o['order_cn'].isupper())
family_cn = sum(1 for o in tree for f in o.get('families', []) if f.get('family_cn') and not f.get('family_cn').isupper())
genus_cn = sum(1 for o in tree for f in o.get('families', []) for g in f.get('genera', []) if g.get('genus_cn') and not g.get('genus_cn').isupper())

total_orders = len(tree)
total_families = sum(len(o.get('families', [])) for o in tree)
total_genera = sum(len(f.get('genera', [])) for o in tree for f in o.get('families', []))

# Write coverage report to file
with open('data/coverage_report.txt', 'w', encoding='utf-8') as f:
    f.write(f"Total orders: {total_orders}\n")
    f.write(f"Total families: {total_families}\n")
    f.write(f"Total genera: {total_genera}\n\n")
    f.write(f"Orders with Chinese names: {order_cn}/{total_orders} ({order_cn/total_orders*100:.1f}%)\n")
    f.write(f"Families with Chinese names: {family_cn}/{total_families} ({family_cn/total_families*100:.1f}%)\n")
    f.write(f"Genera with Chinese names: {genus_cn}/{total_genera} ({genus_cn/total_genera*100:.1f}%)\n\n")

    # Show orders without Chinese names
    orders_without_cn = [o['order_cn'] for o in tree if o['order_cn'].isupper()]
    if orders_without_cn:
        f.write("Orders without Chinese names:\n")
        for o in orders_without_cn:
            f.write(f"  {o}\n")

    # Show some samples
    f.write("\nSample taxonomy:\n")
    for o in tree[:5]:
        f.write(f"{o['order_cn']} ({o['order_sci']})\n")
        for fam in o.get('families', [])[:2]:
            f.write(f"  {fam['family_cn']} ({fam['family_sci']})\n")
            for gen in fam.get('genera', [])[:2]:
                f.write(f"    {gen['genus_cn']} ({gen['genus_sci']})\n")

print("Coverage report saved to data/coverage_report.txt")
print("Taxonomy tree saved to data/taxonomy_debug.json")

ioc.close()
