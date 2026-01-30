import zipfile
import re
from pathlib import Path
from collections import defaultdict

excel_path = Path("data/references/动物界-脊索动物门-2025-10626.xlsx")

# 加载shared_strings
print("Loading shared strings...")
with zipfile.ZipFile(excel_path, 'r') as zf:
    with zf.open('xl/sharedStrings.xml') as f:
        content = f.read()
        t_tags = re.findall(rb'<t[^>]*>([^<]*)</t>', content)
        shared_strings = [tag.decode('utf-8') for tag in t_tags]

print(f"Loaded {len(shared_strings)} shared strings")

# 查找Aves和鸟纲的索引
aves_idx = str(15144)  # 字符串形式用于比较
print(f"Aves index: {aves_idx}")

# 加载行数据并查找鸟纲相关行
print("\nLoading row data and finding bird rows...")
bird_rows = []

with zipfile.ZipFile(excel_path, 'r') as zf:
    with zf.open('xl/worksheets/sheet1.xml') as f:
        content = f.read()
        row_pattern = rb'<row[^>]*r="(\d+)"[^>]*>(.*?)</row>'
        cell_pattern = rb'<c[^>]*r="([A-Z]+\d+)"[^>]*(?:t="(\w+)"|)[^>]*>(.*?)</c>'
        v_pattern = rb'<v[^>]*>(\d+)</v>'

        for row_match in re.finditer(row_pattern, content, re.DOTALL):
            row_num = int(row_match.group(1))
            row_content = row_match.group(2)

            cells_dict = {}
            for cell_match in re.finditer(cell_pattern, row_content):
                cell_ref = cell_match.group(1).decode('utf-8', errors='ignore')
                cell_type = cell_match.group(2).decode('utf-8', errors='ignore') if cell_match.group(2) else ''
                cell_inner = cell_match.group(3)

                v_match = re.search(v_pattern, cell_inner)
                if v_match:
                    value_idx = int(v_match.group(1))
                    # 存储索引，稍后转换
                    if cell_type == 's':
                        cells_dict[cell_ref] = str(value_idx)
                    else:
                        cells_dict[cell_ref] = str(value_idx)

            sorted_cells = sorted(cells_dict.items(), key=lambda x: x[0])
            row_values = [v for ref, v in sorted_cells]

            # 检查第6列（索引从0开始）是否是Aves索引
            if len(row_values) >= 8 and row_values[6] == aves_idx:
                bird_rows.append((row_num, row_values))

print(f"Found {len(bird_rows)} bird rows")

if bird_rows:
    # 转换为实际值并提取分类信息
    orders = {}
    for row_num, values in bird_rows:
        # 转换索引为实际值
        if len(values) >= 14:
            species_sci = shared_strings[int(values[0])] if values[0].isdigit() and int(values[0]) < len(shared_strings) else values[0]
            species_cn = shared_strings[int(values[1])] if values[1].isdigit() and int(values[1]) < len(shared_strings) else values[1]
            order_sci = shared_strings[int(values[8])] if values[8].isdigit() and int(values[8]) < len(shared_strings) else values[8]
            order_cn = shared_strings[int(values[9])] if values[9].isdigit() and int(values[9]) < len(shared_strings) else values[9]
            family_sci = shared_strings[int(values[10])] if values[10].isdigit() and int(values[10]) < len(shared_strings) else values[10]
            family_cn = shared_strings[int(values[11])] if values[11].isdigit() and int(values[11]) < len(shared_strings) else values[11]
            genus_sci = shared_strings[int(values[12])] if values[12].isdigit() and int(values[12]) < len(shared_strings) else values[12]
            genus_cn = shared_strings[int(values[13])] if values[13].isdigit() and int(values[13]) < len(shared_strings) else values[13]

            if order_sci and order_cn:
                if order_cn not in orders:
                    orders[order_cn] = {
                        'sci': order_sci,
                        'families': {}
                    }
                if family_sci and family_cn:
                    if family_cn not in orders[order_cn]['families']:
                        orders[order_cn]['families'][family_cn] = {
                            'sci': family_sci,
                            'genera': {}
                        }
                    if genus_sci and genus_cn:
                        if genus_cn not in orders[order_cn]['families'][family_cn]['genera']:
                            orders[order_cn]['families'][family_cn]['genera'][genus_cn] = genus_sci

    print(f"\n\n=== 鸟纲分类统计 ===")
    print(f"目数: {len(orders)}")
    total_families = sum(len(o['families']) for o in orders.values())
    print(f"科数: {total_families}")
    total_genera = sum(len(f['genera']) for o in orders.values() for f in o['families'].values())
    print(f"属数: {total_genera}")

    print(f"\n=== 目列表 ===")
    for order_cn, order_data in sorted(orders.items()):
        print(f"\n{order_cn} ({order_data['sci']})")
        print(f"  {len(order_data['families'])} 科:")
        for family_cn, family_data in sorted(order_data['families'].items()):
            print(f"    {family_cn} ({family_data['sci']}) - {len(family_data['genera'])} 属")

    # 保存到CSV
    print("\n\nSaving to bird_taxonomy_full.csv...")
    with open('bird_taxonomy_full.csv', 'w', encoding='utf-8-sig', newline='') as f:
        import csv
        writer = csv.writer(f)
        writer.writerow(['Order_CN', 'Order_SCI', 'Family_CN', 'Family_SCI', 'Genus_CN', 'Genus_SCI'])

        for order_cn, order_data in sorted(orders.items()):
            for family_cn, family_data in sorted(order_data['families'].items()):
                for genus_cn, genus_sci in sorted(family_data['genera'].items()):
                    writer.writerow([order_cn, order_data['sci'], family_cn, family_data['sci'], genus_cn, genus_sci])

    print("Saved to bird_taxonomy_full.csv")

    # 保存完整的原始数据
    print("\nSaving complete bird data to bird_complete_data.csv...")
    with open('bird_complete_data.csv', 'w', encoding='utf-8-sig', newline='') as f:
        import csv
        writer = csv.writer(f)
        writer.writerow(['Row', 'Species_SCI', 'Species_CN', 'Kingdom_SCI', 'Kingdom_CN',
                        'Phylum_SCI', 'Phylum_CN', 'Class_SCI', 'Class_CN',
                        'Order_SCI', 'Order_CN', 'Family_SCI', 'Family_CN',
                        'Genus_SCI', 'Genus_CN'])

        for row_num, values in bird_rows:
            row = [row_num]
            # 转换所有索引为实际值
            for i in range(14):
                if len(values) > i and values[i].isdigit():
                    idx = int(values[i])
                    if idx < len(shared_strings):
                        row.append(shared_strings[idx])
                    else:
                        row.append('')
                else:
                    row.append('' if len(values) <= i else values[i])
            writer.writerow(row)

    print(f"Saved to bird_complete_data.csv ({len(bird_rows)} rows)")

    print("\nDone!")
else:
    print("No bird rows found!")
