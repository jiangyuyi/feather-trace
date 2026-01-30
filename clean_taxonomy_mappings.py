import csv
from pathlib import Path

# 清理属映射：移除"雷富民"等非属名的值
print("Cleaning genus mapping...")
genus_mapping = {}
problem_patterns = ['雷富民']  # 可以添加更多需要过滤的模式

with open('bird_genus_mapping.csv', 'r', encoding='utf-8-sig') as f:
    reader = csv.DictReader(f)
    for row in reader:
        genus_sci = row.get('Genus_SCI', '')
        genus_cn = row.get('Genus_CN', '')

        # 跳过无效的属中文名
        is_valid = True
        for pattern in problem_patterns:
            if pattern in genus_cn:
                is_valid = False
                break

        # 只保存有效的映射
        if is_valid and genus_sci:
            genus_mapping[genus_sci] = genus_cn

print(f"Original: 504 genera")
print(f"Cleaned: {len(genus_mapping)} genera")
print(f"Removed: {504 - len(genus_mapping)} invalid entries")

# 保存清理后的映射
with open('bird_genus_mapping_cleaned.csv', 'w', encoding='utf-8-sig', newline='') as f:
    writer = csv.writer(f)
    writer.writerow(['Genus_SCI', 'Genus_CN'])
    for sci, cn in sorted(genus_mapping.items()):
        writer.writerow([sci, cn])

print("Saved to bird_genus_mapping_cleaned.csv")

# 替换旧文件
import shutil
shutil.copy('bird_genus_mapping_cleaned.csv', 'data/references/bird_genus_mapping.csv')
print("Updated data/references/bird_genus_mapping.csv")
