import sys
import pandas as pd

file_path = sys.argv[1]
print(f"Inspecting: {file_path}")

try:
    df = pd.read_excel(file_path, nrows=5) # Read only first 5 rows
    print("Columns:", list(df.columns))
    print("First Row:", df.iloc[0].to_dict())
except Exception as e:
    print(f"Error reading excel: {e}")
