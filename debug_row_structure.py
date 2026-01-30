import zipfile
import re
from pathlib import Path

excel_path = Path("data/references/动物界-脊索动物门-2025-10626.xlsx")

# 加载shared_strings
print("Loading shared strings...")
with zipfile.ZipFile(excel_path, 'r') as zf:
    with zf.open('xl/sharedStrings.xml') as f:
        content = f.read()
        t_tags = re.findall(rb'<t[^>]*>([^<]*)</t>', content)
        shared_strings = [tag.decode('utf-8') for tag in t_tags]

print(f"Loaded {len(shared_strings)} shared strings")

# 打印header索引
print("\nHeader indices:")
print("[2]:", shared_strings[2])
print("[3]:", shared_strings[3])
print("[4]:", shared_strings[4])
print("[5]:", shared_strings[5])
print("[6]:", shared_strings[6])
print("[7]:", shared_strings[7])
print("[8]:", shared_strings[8])
print("[9]:", shared_strings[9])
print("[10]:", shared_strings[10])
print("[11]:", shared_strings[11])
print("[12]:", shared_strings[12])
print("[13]:", shared_strings[13])

# 查找Aves和鸟纲的索引
print("\nAves和鸟纲的索引:")
for i, s in enumerate(shared_strings):
    if 'Aves' in s or s == '鸟纲':
        print(f"[{i}]: {s}")

# 加载行数据
print("\nLoading row data...")
rows_data = []
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
                    if cell_type == 's':
                        if value_idx < len(shared_strings):
                            cells_dict[cell_ref] = shared_strings[value_idx]
                    else:
                        cells_dict[cell_ref] = str(value_idx)

            sorted_cells = sorted(cells_dict.items(), key=lambda x: x[0])
            row_values = [v for ref, v in sorted_cells]

            if row_values:
                rows_data.append((row_num, row_values))

print(f"Loaded {len(rows_data)} rows")

# 打印前10行
print("\n\nFirst 10 rows:")
for row_num, values in rows_data[:10]:
    print(f"Row {row_num}: {values[:15]}")

# 查找包含索引15144（Aves）的行
print("\nSearching for rows containing Aves (index 15144)...")
aves_value = shared_strings[15144]
print(f"Aves value: {aves_value}")

for row_num, values in rows_data:
    for i, val in enumerate(values):
        if val == aves_value:
            print(f"\nFound Aves at row {row_num}, column {i}")
            print(f"Row values: {values[:15]}")
            break
