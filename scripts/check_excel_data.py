import sys
sys.path.insert(0, 'src')
import pandas as pd

# Check the main IOC Excel
df = pd.read_excel('data/references/Multiling IOC 15.1_d.xlsx')
print("Columns in Multiling IOC 15.1_d.xlsx:")
print([c for c in df.columns if 'order' in c.lower() or 'family' in c.lower() or 'genus' in c.lower() or 'chinese' in c.lower()])

# Check if there are Chinese columns for Order/Family/Genus
print("\nChecking for Chinese translations in Order/Family columns:")
print(df[['Order', 'Family']].head(10))

# Check the other Excel file mentioned by user
import os
excel_path = 'data/references/动物界-脊索动物门-2025-10626.xlsx'
if os.path.exists(excel_path):
    df2 = pd.read_excel(excel_path)
    print(f"\n\nColumns in 动物界-脊索动物门-2025-10626.xlsx:")
    print(list(df2.columns))
    print("\nSample rows:")
    print(df2.head(3))
else:
    print(f"\nFile not found: {excel_path}")
