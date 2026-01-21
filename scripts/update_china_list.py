import pandas as pd
import sys
import re
from pathlib import Path

def clean_latin_name(name):
    """
    Clean the scientific name:
    1. Trim whitespace.
    2. Remove 'subsp.' and subsequent text (or just take first two words).
    3. Ensure exactly two words (Binomial).
    """
    if not isinstance(name, str):
        return None
        
    name = name.strip()
    
    # Normalize spaces
    parts = re.split(r'\s+', name)
    
    if len(parts) < 2:
        return None
        
    # User requirement: "Correct latin name should have only two words"
    # So we take the first two.
    # This effectively removes 'subsp. xxx' which usually appears after the species epithet.
    genus = parts[0]
    species = parts[1]
    
    # Sanity check: ensure species doesn't contain '.' unless it's valid?
    # Usually strictly alphabetic.
    
    return f"{genus} {species}"

def main():
    source_file = Path("data/references/动物界-脊索动物门-2025-10626.xlsx")
    target_file = Path("config/dictionaries/china_bird_list.txt")
    
    if not source_file.exists():
        print(f"Error: Source file {source_file} not found.")
        return

    print(f"Reading {source_file}...")
    try:
        # Load Excel with 'calamine' engine which is more robust
        try:
            df = pd.read_excel(source_file, engine='calamine')
        except ImportError:
            print("Warning: 'python-calamine' not found. Falling back to default engine.")
            df = pd.read_excel(source_file)
        except Exception as e:
            print(f"Calamine engine failed: {e}. Trying default...")
            df = pd.read_excel(source_file)
        
        # Identify columns
        # We need to find '纲中文名' and the Scientific Name column.
        print("Columns found:", list(df.columns))
        
        # 1. Filter for '鸟纲'
        if '纲中文名' in df.columns:
            birds_df = df[df['纲中文名'] == '鸟纲']
            print(f"Filtered {len(birds_df)} records with 纲中文名='鸟纲'.")
        else:
            print("Warning: Column '纲中文名' not found. Using all records (assuming file is already filtered).")
            birds_df = df

        # 2. Identify Scientific Name column
        # Common names: 'scientificName', 'Scientific Name', '科学名', '拉丁名'
        sci_col = None
        candidates = ['scientificName', 'Scientific Name', '科学名', '拉丁名', 'ScientificName', 'Accepted Name', '中文名'] # Added 中文名 just in case user meant that? No, user said Latin.
        
        for col in df.columns:
            if col in candidates:
                sci_col = col
                break
            # Fuzzy match
            if 'latin' in col.lower() or 'scientific' in col.lower():
                sci_col = col
                break
        
        if not sci_col:
            # Fallback: Try to find a column that looks like Latin (2 words, ascii)
            print("Could not identify Scientific Name column by name. Analyzing content...")
            for col in df.columns:
                sample = str(birds_df.iloc[0][col])
                if re.match(r'^[A-Z][a-z]+ [a-z]+', sample):
                    sci_col = col
                    print(f"Guessing column '{col}' contains Scientific Names.")
                    break
        
        if not sci_col:
            print("Error: Could not identify Scientific Name column.")
            return

        print(f"Using column '{sci_col}' for Latin names.")
        
        # 3. Process Names
        cleaned_names = set()
        for raw_name in birds_df[sci_col]:
            clean = clean_latin_name(raw_name)
            if clean:
                cleaned_names.add(clean)
                
        print(f"Extracted {len(cleaned_names)} unique species.")
        
        # 4. Write to file
        sorted_names = sorted(list(cleaned_names))
        with open(target_file, 'w', encoding='utf-8') as f:
            for name in sorted_names:
                f.write(name + '\n')
                
        print(f"Successfully updated {target_file}")
        
        # Verify
        with open(target_file, 'r', encoding='utf-8') as f:
            lines = f.readlines()
            print(f"Verification: {target_file} now has {len(lines)} lines.")
            print("First 5 lines:")
            for line in lines[:5]:
                print(f"  - {line.strip()}")

    except Exception as e:
        print(f"An error occurred: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()
