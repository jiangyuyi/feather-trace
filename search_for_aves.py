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

# 查找Aves和鸟纲的索引
aves_idx = None
aves_cn_idx = None
for i, s in enumerate(shared_strings):
    if s == 'Aves':
        aves_idx = i
        print(f"Aves index: {i}")
    if s == '鸟纲':
        aves_cn_idx = i
        print(f"鸟纲 index: {i}")

# 直接在sheet1.xml中搜索这些索引
print("\nSearching in sheet1.xml for index 15144...")
with zipfile.ZipFile(excel_path, 'r') as zf:
    with zf.open('xl/worksheets/sheet1.xml') as f:
        content = f.read()

        # 搜索索引15144
        idx_15144_bytes = f'<v>15144</v>'.encode('utf-8')
        if idx_15144_bytes in content:
            print("Found index 15144 in sheet1.xml!")
            # 找到上下文
            pos = content.find(idx_15144_bytes)
            context = content[max(0, pos-200):pos+200].decode('utf-8', errors='ignore')
            print(f"Context:\n{context}")
        else:
            print("Index 15144 NOT found in sheet1.xml")

        print("\nSearching in sheet1.xml for index 15145...")
        idx_15145_bytes = f'<v>15145</v>'.encode('utf-8')
        if idx_15145_bytes in content:
            print("Found index 15145 in sheet1.xml!")
            # 找到上下文
            pos = content.find(idx_15145_bytes)
            context = content[max(0, pos-200):pos+200].decode('utf-8', errors='ignore')
            print(f"Context:\n{context}")
        else:
            print("Index 15145 NOT found in sheet1.xml")

# 查看shared_strings中15144附近的值
print("\n\nValues around index 15144:")
for i in range(15130, 15160):
    print(f"[{i}]: {shared_strings[i]}")

# 查看是否有鸟纲相关的其他索引（鹰形目、雀形目等）
print("\n\nLooking for bird-related keywords in shared strings...")
bird_keywords = ['雁形目', '雀形目', '鹰形目', '鸻形目', '鸽形目', '雁科', '雀科', '鹰科', '隼科', '鸭科', '鸻科']
for keyword in bird_keywords:
    for i, s in enumerate(shared_strings):
        if s == keyword:
            print(f"{keyword} found at index {i}")
            break

# 检查是否有包含鸟纲分类的行
print("\n\nSearching for ACCIPITRIFORMES or other bird order latin names...")
bird_orders = ['ACCIPITRIFORMES', 'PASSERIFORMES', 'ANSERIFORMES', 'CHARADRIIFORMES',
               'COLUMBIFORMES', 'PICIFORMES', 'GALLIFORMES']
for order in bird_orders:
    for i, s in enumerate(shared_strings):
        if order in s.upper():
            print(f"{order} found at index {i}: {s}")
            break
