import pandas as pd
import os

file_path = "config/Multiling IOC 15.1_d.xlsx"

try:
    # Read the first few rows to inspect columns
    df = pd.read_excel(file_path, nrows=5)
    print("Columns:", df.columns.tolist())
    print("\nFirst row sample:")
    print(df.iloc[0])
except Exception as e:
    print(f"Error reading excel: {e}")
