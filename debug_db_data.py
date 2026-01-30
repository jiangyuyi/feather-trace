import sqlite3
from pathlib import Path

db_path = Path("data/db/feathertrace.db")
conn = sqlite3.connect(db_path)
cursor = conn.cursor()

# 查找属中文名为"雷富民"的记录
cursor.execute("""
    SELECT scientific_name, chinese_name, genus_cn, genus_sci, family_cn, family_sci, order_cn, order_sci
    FROM taxonomy
    WHERE genus_cn = '雷富民'
    LIMIT 10
""")
print("属中文名为'雷富民'的记录:")
for row in cursor.fetchall():
    print(row)

# 查找前10条记录查看列内容
print("\n前10条记录:")
cursor.execute("""
    SELECT scientific_name, chinese_name,
           genus_cn, genus_sci,
           family_cn, family_sci,
           order_cn, order_sci
    FROM taxonomy
    LIMIT 10
""")
for row in cursor.fetchall():
    print(f"{row[1]} ({row[0]})")
    print(f"  属: {row[3]} ({row[2]})")
    print(f"  科: {row[5]} ({row[4]})")
    print(f"  目: {row[7]} ({row[6]})")
    print()

# 检查列索引是否正确
print("\n检查索引:")
cursor.execute("PRAGMA table_info(taxonomy)")
for col in cursor.fetchall():
    print(col)

conn.close()
