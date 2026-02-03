import sys
sys.path.insert(0, 'src')
import pandas as pd
from metadata.ioc_manager import IOCManager

# Load the IOC Excel
df = pd.read_excel('data/references/Multiling IOC 15.1_d.xlsx')
df.columns = [str(c).strip() for c in df.columns]

with open('data/species_check.txt', 'w', encoding='utf-8') as f:
    # Check Tinamidae species
    f.write("=== Tinamidae species ===\n")
    tinamidae = df[df['Family'] == 'Tinamidae']
    for _, row in tinamidae.head(15).iterrows():
        f.write(f"  {row['IOC_15.1']} -> {row['Chinese']}\n")

    # Check Spheniscidae species
    f.write("\n=== Spheniscidae species ===\n")
    spheniscidae = df[df['Family'] == 'Spheniscidae']
    for _, row in spheniscidae.head(10).iterrows():
        f.write(f"  {row['IOC_15.1']} -> {row['Chinese']}\n")

    # Check Apterygidae species
    f.write("\n=== Apterygidae species ===\n")
    apterygidae = df[df['Family'] == 'Apterygidae']
    for _, row in apterygidae.head(10).iterrows():
        f.write(f"  {row['IOC_15.1']} -> {row['Chinese']}\n")

print("Saved to data/species_check.txt")
