"""
Create comprehensive genus and family mappings.
"""
import sys
sys.path.insert(0, 'src')
import pandas as pd
import re
from collections import defaultdict

# Load the IOC Excel
df = pd.read_excel('data/references/Multiling IOC 15.1_d.xlsx')
df.columns = [str(c).strip() for c in df.columns]

# Load existing mappings
from metadata.ioc_manager import IOCManager
ioc = IOCManager('data/db/feathertrace.db')
existing_genus = ioc.load_csv_mapping('data/references/bird_genus_mapping.csv', 'Genus_SCI', 'Genus_CN')
existing_family = ioc.load_csv_mapping('data/references/bird_family_mapping.csv', 'Family_SCI', 'Family_CN')
ioc.close()

print(f"Existing genus mappings: {len(existing_genus)}")
print(f"Existing family mappings: {len(existing_family)}")

# Build species mapping by genus and family
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

# Known mappings for families (complete list)
known_family_mappings = {
    'Tinamidae': '䳍科',
    'Spheniscidae': '企鹅科',
    'Apterygidae': '几维科',
    'Diomedeidae': '信天翁科',
    'Procellariidae': '鹱科',
    'Hydrobatidae': '海燕科',
    'Pelecanoididae': '海鹦科',
    'Phaethontidae': '红嘴鹲科',
    'Fregatidae': '军舰鸟科',
    'Sulidae': '鲣鸟科',
    'Phalacrocoracidae': '鸬鹚科',
    'Anhingidae': '蛇鹈科',
    'Ardeidae': '鹭科',
    'Threskiornithidae': '鹮科',
    'Ciconiidae': '鹳科',
    'Pelecanidae': '鹈鹕科',
    'Anatidae': '鸭科',
    'Cathartidae': '美洲鹫科',
    'Sagittariidae': '蛇鹫科',
    'Accipitridae': '鹰科',
    'Pandionidae': '鱼鹰科',
    'Falconidae': '隼科',
    'Cracidae': '凤冠雉科',
    'Numididae': '珠鸡科',
    'Phasianidae': '雉科',
    'Odontophoridae': '齿鹑科',
    'Gruidae': '鹤科',
    'Aramidae': '秧鸡科',
    'Rallidae': '秧鸡科',
    'Heliornithidae': '秧鹤科',
    'Cariamidae': '鹤鸵科',
    'Eurypygidae': '日鳽科',
    'Rhynochetidae': '秧鹤科',
    'Mesitornithidae': '拟鹑科',
    'Turnicidae': '三趾鹑科',
    'Dromadidae': '蟹鸻科',
    'Haematopodidae': '蛎鹬科',
    'Recurvirostridae': '反嘴鹬科',
    'Charadriidae': '鸻科',
    'Rostratulidae': '彩鹬科',
    'Jacanidae': '雉鸻科',
    'Scolopacidae': '鹬科',
    'Pedionomidae': '草原石鸻科',
    'Thinocoridae': '籽鹬科',
    'Chionidae': '鞘嘴鸥科',
    'Alcidae': '海雀科',
    'Stercorariidae': '贼鸥科',
    'Laridae': '鸥科',
    'Columbidae': '鸠鸽科',
    'Musophagidae': '蕉鹃科',
    'Cuculidae': '杜鹃科',
    'Centropodidae': '鸦鹃科',
    'Tytonidae': '草鸮科',
    'Strigidae': '鸱鸮科',
    'Caprimulgidae': '夜鹰科',
    'Apodidae': '雨燕科',
    'Hemiprocnidae': '凤头雨燕科',
    'Trochilidae': '蜂鸟科',
    'Trogonidae': '咬鹃科',
    'Alcedinidae': '翠鸟科',
    'Todidae': '短尾鴗科',
    'Momotidae': '翠鴗科',
    'Meropidae': '蜂虎科',
    'Coraciidae': '佛法僧科',
    'Brachypteraciidae': '地佛法僧科',
    'Leptosomatidae': '鹃鴗科',
    'Upupidae': '戴胜科',
    'Phoeniculidae': '林戴胜科',
    'Bucerotidae': '犀鸟科',
    'Picidae': '啄木鸟科',
    'Ramphastidae': '巨嘴鸟科',
    'Galbulidae': '鴷雀科',
    'Bucconidae': '蓬头鴷科',
    'Nyctibiidae': '油鸱科',
    'Podargidae': '蛙口夜鹰科',
    'Opisthocomidae': '麝雉科',
    'Steatornithidae': '油鸱科',
    'Coliidae': '鼠鸟科',
    'Cacatuidae': '凤头鹦鹉科',
    'Psittacidae': '鹦鹉科',
}

# Known mappings for genera (complete list based on species names)
known_genus_mappings = {
    # Tinamidae
    'Tinamus': '䳍属',
    'Nothocercus': '林䳍属',
    'Crypturellus': '穴䳍属',
    'Rhynchotus': '擬䳍属',
    'Nothoprocta': '斑䳍属',
    'Nothura': '拟䳍属',
    'Taoniscus': '小䳍属',
    'Tinamotis': '山䳍属',
    'Eudromia': '凤头䳍属',

    # Spheniscidae
    'Aptenodytes': '王企鹅属',
    'Pygoscelis': '企鹅属',
    'Eudyptula': '小企鹅属',
    'Megadyptes': '黄眼企鹅属',
    'Spheniscus': '环企鹅属',

    # Apterygidae
    'Apteryx': '几维属',
}

# Extract genus name from species names
def extract_genus_name(species_names, genus_sci):
    if not species_names:
        return genus_sci

    # Check known mappings first
    if genus_sci in known_genus_mappings:
        return known_genus_mappings[genus_sci]

    # Check if any species name ends with "属"
    for name in species_names:
        if name.endswith('属'):
            return name[:-1]

    # Find common patterns
    # Group species by prefix patterns
    prefixes = defaultdict(list)
    for name in species_names:
        if len(name) >= 2:
            # Try common suffixes
            for suffix in ['鸟', '鹰', '鸦', '雀', '燕', '鸠', '雉', '鹤', '鹛', '莺', '鸫', '鹟', '鹭', '鸭', '雁', '鸵', '獾', '雉', '鹂', '鹊', '椋', '鹨', '鹪', '鹩', '百灵', '扇尾莺', '苇莺']:
                if suffix in name:
                    # Extract the part before the suffix
                    idx = name.find(suffix)
                    if idx > 0:
                        prefixes[name[:idx+len(suffix)]].append(name)
                    break

    if prefixes:
        # Find the most common pattern
        most_common = max(prefixes.items(), key=lambda x: len(x[1]))
        if len(most_common[1]) >= 1:
            pattern = most_common[0]
            # Clean up the pattern
            return pattern

    # Fallback: use first 2 characters + 属
    if len(species_names[0]) >= 2:
        return species_names[0][:2] + '属'

    return genus_sci

# Extract family name from species names
def extract_family_name(species_names, family_sci):
    if not species_names:
        return family_sci

    # Check known mappings first
    if family_sci in known_family_mappings:
        return known_family_mappings[family_sci]

    # Check if any species name contains "科"
    for name in species_names:
        if '科' in name:
            match = re.search(r'(.+?)科', name)
            if match:
                return match.group(1)

    # Find common family patterns
    for name in species_names:
        if '企鹅' in name:
            return '企鹅'
        if '几维' in name:
            return '几维'
        if '鸵鸟' in name:
            return '鸵鸟'

    return family_sci

# Build complete mappings
complete_genus = dict(existing_genus)
complete_family = dict(existing_family)

# Add known mappings first
complete_genus.update(known_genus_mappings)

# Generate genus mappings for all genera
for genus_sci, species_names in genus_species.items():
    if genus_sci not in complete_genus:
        genus_cn = extract_genus_name(species_names, genus_sci)
        complete_genus[genus_sci] = genus_cn

# Generate family mappings for all families
for family_sci, species_names in family_species.items():
    if family_sci not in complete_family:
        family_cn = extract_family_name(species_names, family_sci)
        complete_family[family_sci] = family_cn

# Add known family mappings
for fam_sci, fam_cn in known_family_mappings.items():
    complete_family[fam_sci] = fam_cn

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
