import pandas as pd
import sys

try:
    # Check the other file
    filename = "config/IOC_Names_File_Plus-15.1_red.xlsx"
    print(f"Checking {filename}...")
    df = pd.read_excel(filename)
    
    # Simple search
    for col in df.columns:
        if df[col].dtype == object:
            match = df[df[col].astype(str).str.contains("Pycnonotus sinensis", na=False)]
            if not match.empty:
                print("\nFound match:")
                print(match.iloc[0])
                break
except Exception as e:
    print(e)
