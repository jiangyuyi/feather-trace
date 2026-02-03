import sys
sys.path.insert(0, 'src')
from metadata.ioc_manager import IOCManager
import json

def has_chinese(s):
    if not s:
        return False
    for char in str(s):
        code = ord(char)
        if 0x4e00 <= code <= 0x9fff or 0x3400 <= code <= 0x4dbf:
            return True
    return False

ioc = IOCManager('data/db/feathertrace.db')
tree = ioc.get_taxonomy_tree(include_empty=True)

# Count coverage
order_cn = sum(1 for o in tree if has_chinese(o.get('order_cn', '')))
family_cn = sum(1 for o in tree for f in o.get('families', []) if has_chinese(f.get('family_cn', '')))
genus_cn = sum(1 for o in tree for f in o.get('families', []) for g in f.get('genera', []) if has_chinese(g.get('genus_cn', '')))

total_orders = len(tree)
total_families = sum(len(o.get('families', [])) for o in tree)
total_genera = sum(len(f.get('genera', [])) for o in tree for f in o.get('families', []))

# Save report
with open('data/coverage_report.txt', 'w', encoding='utf-8') as f:
    f.write("=== 分类树中文名覆盖率报告 ===\n\n")
    f.write(f"目 (Orders): {order_cn}/{total_orders} ({order_cn/total_orders*100:.1f}%)\n")
    f.write(f"科 (Families): {family_cn}/{total_families} ({family_cn/total_families*100:.1f}%)\n")
    f.write(f"属 (Genera): {genus_cn}/{total_genera} ({genus_cn/total_genera*100:.1f}%)\n\n")

    # Show families without Chinese names
    f.write("=== 缺少中文名的科 (前20个) ===\n")
    count = 0
    for order in tree:
        order_cn = order.get('order_cn', '')
        for fam in order.get('families', []):
            if not has_chinese(fam.get('family_cn', '')) and count < 20:
                f.write(f"  {fam['family_cn']} ({order_cn})\n")
                count += 1

    # Show sample taxonomy
    f.write("\n=== 样本分类树 (前5个目) ===\n")
    for order in tree[:5]:
        f.write(f"{order['order_cn']} ({order['order_sci']})\n")
        for fam in order.get('families', [])[:2]:
            cn_status = "✓" if has_chinese(fam.get('family_cn', '')) else "✗"
            f.write(f"  {cn_status} {fam['family_cn']} ({fam['family_sci']})\n")
            for gen in fam.get('genera', [])[:2]:
                gen_cn_status = "✓" if has_chinese(gen.get('genus_cn', '')) else "✗"
                f.write(f"    {gen_cn_status} {gen['genus_cn']} ({gen['genus_sci']})\n")

print("Coverage report saved to data/coverage_report.txt")

# Save taxonomy
with open('data/taxonomy_debug.json', 'w', encoding='utf-8') as f:
    json.dump(tree, f, ensure_ascii=False, indent=2)

print("Taxonomy saved to data/taxonomy_debug.json")

ioc.close()
