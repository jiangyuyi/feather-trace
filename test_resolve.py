import sys
sys.stdout.reconfigure(encoding='utf-8')
import os
from pathlib import Path
import yaml

BASE_DIR = Path('D:/Code/gemini/feather_trace')
config_path = BASE_DIR / 'config/settings.yaml'

with open(config_path, 'r', encoding='utf-8') as f:
    config = yaml.safe_load(f)

processed_dir = (BASE_DIR / config['paths']['output']['root_dir']).resolve()
print(f'processed_dir: {processed_dir}')
print(f'processed_dir type: {type(processed_dir)}')

# 从数据库获取一个实际的 file_path
import sqlite3
conn = sqlite3.connect(BASE_DIR / config['paths']['db_path'])
cursor = conn.cursor()
cursor.execute('SELECT id, file_path FROM photos LIMIT 1')
row = cursor.fetchone()
conn.close()

if row:
    file_path_str = row[1]
    print(f'\nTesting file_path: {file_path_str}')
    print(f'file_path type: {type(file_path_str)}')

    # 模拟 resolve_processed_web_path 函数的逻辑
    if not file_path_str:
        print('Result: None (empty path)')
    else:
        try:
            abs_path = Path(file_path_str).resolve()
            print(f'abs_path: {abs_path}')
            print(f'abs_path exists: {abs_path.exists()}')
            print(f'abs_path parents: {list(abs_path.parents)}')

            # 检查 processed_dir 是否在 parents 中
            in_parents = processed_dir in abs_path.parents
            print(f'processed_dir in parents: {in_parents}')

            # 尝试比较
            for p in abs_path.parents:
                print(f'  comparing: {p} == {processed_dir} -> {p == processed_dir}')

            if in_parents:
                rel = abs_path.relative_to(processed_dir)
                url = f"/static/processed/{str(rel).replace(os.sep, '/')}"
                print(f'Result: {url}')
            else:
                print('Result: None (not in processed_dir)')
        except Exception as e:
            print(f'Result: None (exception: {e})')
