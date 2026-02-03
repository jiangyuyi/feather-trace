"""
Improve genus and family mappings using species Chinese names.
"""
import sys
sys.path.insert(0, 'src')
import pandas as pd
import re
from collections import defaultdict
from metadata.ioc_manager import IOCManager

# Load the IOC Excel
df = pd.read_excel('data/references/Multiling IOC 15.1_d.xlsx')
df.columns = [str(c).strip() for c in df.columns]

# Load existing mappings
ioc = IOCManager('data/db/feathertrace.db')
existing_genus = ioc.load_csv_mapping('data/references/bird_genus_mapping.csv', 'Genus_SCI', 'Genus_CN')
existing_family = ioc.load_csv_mapping('data/references/bird_family_mapping.csv', 'Family_SCI', 'Family_CN')
ioc.close()

print(f"Existing genus mappings: {len(existing_genus)}")
print(f"Existing family mappings: {len(existing_family)}")

# Group species by genus and family
genus_species = defaultdict(list)
family_species = defaultdict(list)

for _, row in df.iterrows():
    parts = str(row.get('IOC_15.1', '')).split()
    if parts:
        genus_sci = parts[0]
        chinese_name = str(row.get('Chinese', ''))
        family_sci = str(row.get('Family', ''))
        if chinese_name and chinese_name != 'nan' and genus_sci:
            genus_species[genus_sci].append(chinese_name)
            if family_sci:
                family_species[family_sci].append(chinese_name)

# Extract genus Chinese name from species names
def extract_genus_name(species_names, genus_sci):
    """Extract genus Chinese name from species Chinese names."""
    if not species_names:
        return genus_sci

    # Check if species names already contain "属"
    for name in species_names:
        if name.endswith('属'):
            return name[:-1]  # Return without trailing "属"

    # Find common patterns
    # For bird names, common suffixes include: 鸟, 鹰, 鸦, 雀, 燕, 鸠, 雉, 鹤, 鹛, 莺, 鸫, 鹟, 鹭, 鸭, 雁, 鸵, 企鹅, etc.

    # Try to find the longest common prefix
    if len(species_names) >= 2:
        prefix = species_names[0]
        for name in species_names[1:]:
            while prefix and not name.startswith(prefix):
                prefix = prefix[:-1]
            if not prefix:
                break

        if len(prefix) >= 2:
            # Clean up the prefix
            # Remove common modifiers
            prefix = re.sub(r'^[大小黑白红黄绿蓝紫金银灰棕淡深赤]$', '', prefix)
            if prefix:
                return prefix

    # For single species, infer from the name
    if len(species_names) == 1:
        name = species_names[0]

        # Common patterns
        patterns = [
            (r'(.+?)鹰', '鹰'),
            (r'(.+?)鸦', '鸦'),
            (r'(.+?)雀', '雀'),
            (r'(.+?)燕', '燕'),
            (r'(.+?)鸠', '鸠'),
            (r'(.+?)雉', '雉'),
            (r'(.+?)鹤', '鹤'),
            (r'(.+?)鹛', '鹛'),
            (r'(.+?)莺', '莺'),
            (r'(.+?)鸫', '鸫'),
            (r'(.+?)鹟', '鹟'),
            (r'(.+?)鹭', '鹭'),
            (r'(.+?)鸭', '鸭'),
            (r'(.+?)雁', '雁'),
            (r'(.+?)鸟', '鸟'),
            (r'(.+?)雁', '雁'),
            (r'(.+?)獾', '獾'),
        ]

        for pattern, suffix in patterns:
            match = re.search(pattern, name)
            if match:
                return match.group(1) + suffix

        # If no pattern matches, return the name + 属
        if len(name) >= 2:
            return name[:2] + '属'

    return genus_sci

# Extract family Chinese name from species names
def extract_family_name(species_names, family_sci):
    """Extract family Chinese name from species Chinese names."""
    if not species_names:
        return family_sci

    # Check if species names already contain "科"
    for name in species_names:
        if '科' in name:
            # Extract the family name
            match = re.search(r'(.+?)科', name)
            if match:
                return match.group(1)
            return name.replace('科', '')

    # Find common family suffixes
    if len(species_names) >= 2:
        # Look for common family patterns
        for name in species_names:
            if '科' in name:
                match = re.search(r'(.+?)科', name)
                if match:
                    return match.group(1)

    # For families, often the name ends with: 科 (implied), or common family names
    # Try to infer from genus names
    if len(species_names) >= 1:
        name = species_names[0]
        # Common family patterns
        if '鸵' in name:
            return '鸵鸟'
        if '企鹅' in name:
            return '企鹅'
        if '几维' in name:
            return '几维'

    return family_sci

# Build complete mappings
complete_genus = dict(existing_genus)
complete_family = dict(existing_family)

# Generate genus mappings
for genus_sci, species_names in genus_species.items():
    if genus_sci not in complete_genus:
        genus_cn = extract_genus_name(species_names, genus_sci)
        complete_genus[genus_sci] = genus_cn

# Generate family mappings
for family_sci, species_names in family_species.items():
    if family_sci not in complete_family:
        family_cn = extract_family_name(species_names, family_sci)
        complete_family[family_sci] = family_cn

print(f"\nComplete genus mappings: {len(complete_genus)}")
print(f"Complete family mappings: {len(complete_family)}")

# Save the mappings
with open('data/references/bird_genus_mapping_complete.csv', 'w', encoding='utf-8-sig') as f:
    f.write('Genus_SCI,Genus_CN\n')
    for sci, cn in sorted(complete_genus.items()):
        f.write(f'{sci},{cn}\n')
print(f"Saved genus mapping to bird_genus_mapping_complete.csv")

with open('data/references/bird_family_mapping_complete.csv', 'w', encoding='utf-8-sig') as f:
    f.write('Family_SCI,Family_CN\n')
    for sci, cn in sorted(complete_family.items()):
        f.write(f'{sci},{cn}\n')
print(f"Saved family mapping to bird_family_mapping_complete.csv")

print("\nDone!")
