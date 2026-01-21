import pandas as pd
import sys

try:
    df = pd.read_excel("config/Multiling IOC 15.1_d.xlsx")
    # Find the row for Pycnonotus sinensis
    # The column names might need adjustment based on previous findings, but let's look for the row directly
    
    # Try to find columns
    print("Columns:", df.columns.tolist())
    
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
