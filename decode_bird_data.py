import zipfile
import re
from pathlib import Path
import csv

excel_path = Path("data/references/动物界-脊索动物门-2025-10626.xlsx")

# 读取sharedStrings并保存到文件查看
def load_shared_strings():
    print("Loading shared strings...")
    with zipfile.ZipFile(excel_path, 'r') as zf:
        with zf.open('xl/sharedStrings.xml') as f:
            content = f.read()
            # 直接用正则提取所有<t>标签内容
            t_tags = re.findall(rb'<t[^>]*>([^<]*)</t>', content)
            # 解码
            strings = []
            for tag in t_tags:
                try:
                    strings.append(tag.decode('utf-8'))
                except:
                    strings.append('')
            return strings

# 读取行数据
def load_all_rows(shared_strings):
    print("Loading all rows...")
    rows_data = []
    with zipfile.ZipFile(excel_path, 'r') as zf:
        with zf.open('xl/worksheets/sheet1.xml') as f:
            content = f.read()

            # 提取行
            row_pattern = rb'<row[^>]*r="(\d+)"[^>]*>(.*?)</row>'
            cell_pattern = rb'<c[^>]*r="([A-Z]+\d+)"[^>]*(?:t="(\w+)"|)[^>]*>(.*?)</c>'
            v_pattern = rb'<v[^>]*>(\d+)</v>'

            for row_match in re.finditer(row_pattern, content, re.DOTALL):
                row_num = row_match.group(1).decode('utf-8', errors='ignore')
                row_content = row_match.group(2)

                cells_dict = {}

                for cell_match in re.finditer(cell_pattern, row_content):
                    cell_ref = cell_match.group(1).decode('utf-8', errors='ignore')
                    cell_type = cell_match.group(2).decode('utf-8', errors='ignore') if cell_match.group(2) else ''
                    cell_inner = cell_match.group(3)

                    v_match = re.search(v_pattern, cell_inner)
                    if v_match:
                        value_idx = int(v_match.group(1))
                        if cell_type == 's':
                            if value_idx < len(shared_strings):
                                cells_dict[cell_ref] = shared_strings[value_idx]
                        else:
                            cells_dict[cell_ref] = str(value_idx)

                sorted_cells = sorted(cells_dict.items(), key=lambda x: x[0])
                row_values = [v for ref, v in sorted_cells]

                if row_values:
                    rows_data.append((row_num, row_values))

    return rows_data

# 主流程
print("Step 1: Loading shared strings...")
shared_strings = load_shared_strings()
print(f"Loaded {len(shared_strings)} shared strings")

# 保存所有shared strings到文件用于检查
print("\nStep 2: Saving shared strings to file...")
with open('shared_strings_dump.txt', 'w', encoding='utf-8') as f:
    for i, s in enumerate(shared_strings):
        f.write(f"[{i}]: {s}\n")
print("Saved to shared_strings_dump.txt")

# 查找鸟纲相关的索引
print("\nStep 3: Finding bird-related strings...")
bird_related_indices = []
bird_keywords_utf8 = [
    '鸟纲'.encode('utf-8'),
    '雁形目'.encode('utf-8'),
    '雀形目'.encode('utf-8'),
    '鹰形目'.encode('utf-8'),
    '鸽形目'.encode('utf-8'),
    '雁'.encode('utf-8'),
    '雀'.encode('utf-8'),
    '鹰'.encode('utf-8'),
    '隼'.encode('utf-8'),
    '鸭'.encode('utf-8'),
    '鸻'.encode('utf-8'),
]

# 直接读取原始字节查找
with zipfile.ZipFile(excel_path, 'r') as zf:
    with zf.open('xl/sharedStrings.xml') as f:
        ss_content = f.read()

for keyword_bytes in bird_keywords_utf8:
    if keyword_bytes in ss_content:
        print(f"Found keyword: {keyword_bytes.decode('utf-8', errors='ignore')}")

# 查找Aves和bird order拉丁名
print("\nStep 4: Finding bird orders and families...")
latin_keywords = ['Aves', 'Passeriformes', 'Anseriformes', 'Falconiformes', 'Accipitriformes',
                  'Charadriiformes', 'Columbiformes', 'Piciformes', 'Galliformes']
latin_indices = []
for i, s in enumerate(shared_strings):
    for latin in latin_keywords:
        if latin in str(s):
            latin_indices.append((i, latin, s))
            print(f"Found '{latin}' at index {i}: {s}")

print("\nStep 5: Loading rows...")
all_rows = load_all_rows(shared_strings)
print(f"Loaded {len(all_rows)} rows")

# 找出包含鸟纲相关索引的行
bird_row_indices = set()
for idx, latin, s in latin_indices:
    print(f"Searching for index {idx} in rows...")
    for row_num, values in all_rows:
        for v in values:
            if v == s or v == latin:
                bird_row_indices.add(int(row_num))
                print(f"  Found at row {row_num}: {values[:8]}")
                if len(bird_row_indices) >= 5:
                    break
        if len(bird_row_indices) >= 5:
            break
    if len(bird_row_indices) >= 5:
        break

# 保存包含鸟纲数据的行
print(f"\nStep 6: Saving bird rows (found {len(bird_row_indices)} rows)...")
if bird_row_indices:
    bird_rows_data = [(rn, vals) for rn, vals in all_rows if int(rn) in bird_row_indices]

    with open('bird_rows_raw.csv', 'w', encoding='utf-8-sig', newline='') as f:
        writer = csv.writer(f)
        writer.writerow(['Row', 'Col0', 'Col1', 'Col2', 'Col3', 'Col4', 'Col5', 'Col6', 'Col7', 'Col8', 'Col9', 'Col10', 'Col11', 'Col12', 'Col13', 'Col14'])
        for row_num, values in bird_rows_data:
            row = [row_num] + values[:15]
            writer.writerow(row)
    print("Saved to bird_rows_raw.csv")
else:
    print("No bird rows found with Latin keywords")

# 分析所有行的结构
print("\nStep 7: Analyzing row structure...")
print("Rows 1-10:")
for row_num, values in all_rows[:10]:
    print(f"Row {row_num}: {values[:10]}")

print("\nRows 100-110:")
for row_num, values in all_rows[99:110]:
    print(f"Row {row_num}: {values[:10]}")
