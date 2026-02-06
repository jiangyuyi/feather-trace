"""
Generate complete Chinese mapping for orders, families, and genera
using a more careful approach based on species Chinese names.
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
ioc = IOCManager('data/db/wingscribe.db')

existing_genus = ioc.load_csv_mapping('data/references/bird_genus_mapping.csv', 'Genus_SCI', 'Genus_CN')
existing_family = ioc.load_csv_mapping('data/references/bird_family_mapping.csv', 'Family_SCI', 'Family_CN')
existing_order = ioc.load_csv_mapping('data/references/bird_order_mapping.csv', 'Order_SCI', 'Order_CN')

print(f"Existing genus mapping: {len(existing_genus)}")
print(f"Existing family mapping: {len(existing_family)}")
print(f"Existing order mapping: {len(existing_order)}")

# Build genus mapping from species Chinese names
# Pattern: species Chinese names often end with the genus name + specific suffix
# e.g., "灰头鸦雀" -> genus: 鸦雀属

genus_candidates = defaultdict(list)  # genus_sci -> list of chinese names

for _, row in df.iterrows():
    parts = str(row.get('IOC_15.1', '')).split()
    if parts:
        genus_sci = parts[0]
        chinese_name = str(row.get('Chinese', ''))
        if chinese_name and chinese_name != 'nan':
            genus_candidates[genus_sci].append(chinese_name)

# For each genus, find the common pattern in species names
def extract_genus_cn(species_names, genus_sci):
    """Extract genus Chinese name from species Chinese names"""
    if not species_names:
        return genus_sci

    # Common genus name patterns:
    # 1. Species name ends with "属" -> use that
    # 2. Species name ends with pattern like "X鸟", "X鸦", etc. -> extract common prefix
    # 3. Find longest common prefix/suffix

    # Check if any species name already has "属"
    for name in species_names:
        if name.endswith('属'):
            return name[:-1]  # Remove trailing "属"

    # Find common prefix
    if len(species_names) >= 2:
        common_prefix = species_names[0]
        for name in species_names[1:]:
            while not name.startswith(common_prefix) and len(common_prefix) > 1:
                common_prefix = common_prefix[:-1]
            if not name.startswith(common_prefix):
                common_prefix = ''
                break

        if len(common_prefix) >= 2:
            # Clean up common prefix (remove trailing characters that might be specific epithet)
            # Common endings to strip: numbers, specific bird names
            common_prefix = re.sub(r'[的小大白灰黑红黄绿蓝紫金银]$', '', common_prefix)
            if len(common_prefix) >= 2:
                return common_prefix + '属'

    # For single species, try to infer from the name
    if len(species_names) == 1:
        name = species_names[0]
        # Try common patterns
        # "X鹰" -> "鹰属"
        if name.endswith('鹰'):
            return '鹰属'
        # "X鸦" -> "鸦属"
        if name.endswith('鸦'):
            return '鸦属'
        # "X雀" -> "雀属"
        if name.endswith('雀'):
            return '雀属'
        # "X燕" -> "燕属"
        if name.endswith('燕'):
            return '燕属'
        # "X鸠" -> "鸠属"
        if name.endswith('鸠'):
            return '鸠属'
        # "X雉" -> "雉属"
        if name.endswith('雉'):
            return '雉属'
        # "X鹤" -> "鹤属"
        if name.endswith('鹤'):
            return '鹤属'
        # "X鹛" -> "鹛属"
        if name.endswith('鹛'):
            return '鹛属'
        # "X莺" -> "莺属"
        if name.endswith('莺'):
            return '莺属'
        # "X鸫" -> "鸫属"
        if name.endswith('鸫'):
            return '鸫属'
        # "X鹟" -> "鹟属"
        if name.endswith('鹟'):
            return '鹟属'
        # "X鹭" -> "鹭属"
        if name.endswith('鹭'):
            return '鹭属'
        # "X鸭" -> "鸭属"
        if name.endswith('鸭'):
            return '鸭属'
        # "X雁" -> "雁属"
        if name.endswith('雁'):
            return '雁属'

    return genus_sci  # Fallback to Latin name

# Build complete genus mapping
complete_genus = dict(existing_genus)

for genus_sci, species_names in genus_candidates.items():
    if genus_sci not in complete_genus:
        genus_cn = extract_genus_cn(species_names, genus_sci)
        complete_genus[genus_sci] = genus_cn

print(f"\nComplete genus mapping: {len(complete_genus)}")

# Order mapping - complete translation
order_translations = {
    'PASSERIFORMES': '雀形目',
    'GALLIFORMES': '鸡形目',
    'ANSERIFORMES': '雁形目',
    'COLUMBIFORMES': '鸽形目',
    'CHARADRIIFORMES': '鸻形目',
    'CICONIIFORMES': '鹳形目',
    'ACCIPITRIFORMES': '鹰形目',
    'FALCONIFORMES': '隼形目',
    'STRIGIFORMES': '鸮形目',
    'CAPRIMULGIFORMES': '夜鹰目',
    'APODIFORMES': '雨燕目',
    'CORACIIFORMES': '佛法僧目',
    'BUCEROTIFORMES': '犀鸟目',
    'CUCULIFORMES': '鹃形目',
    'PSITTACIFORMES': '鹦鹉目',
    'GRUIFORMES': '鹤形目',
    'PODICIPEDIFORMES': '鸊鷉目',
    'GAVIIFORMES': '潜鸟目',
    'SPHENISCIFORMES': '企鹅目',
    'PROCELLARIIFORMES': '鹱形目',
    'SULIFORMES': '鹲形目',
    'PHOENICOPTERIFORMES': '红鹳目',
    'PICIFORMES': '鴷形目',
    'TROGONIFORMES': '咬鹃目',
    'COLIIFORMES': '鼠鸟目',
    'OPHTHULGIFORMES': '裸眉鸫目',
    'EURYPYGIFORMES': '日鳽目',
    'MESITORNITHIFORMES': '拟鹑目',
    'MUSOPHAGIFORMES': '蕉鹃目',
    'OTIDIFORMES': '鸨形目',
    'CARIAMIFORMES': '鹤鸵目',
    'APTERYGIFORMES': '无翼鸟目',
    'CASUARIIFORMES': '鹤鸵目',
    'AEGOTHELIFORMES': '袋鼬目',
    'LEPTOSOMIFORMES': '鹃鴗目',
    'GALBULIFORMES': '鴷雀目',
    'BUCEROTIFORMES': '犀鸟目',
    'NYCTIBIIFORMES': '油鸱目',
    'OPISTHOCOMIFORMES': '麝雉目',
    'PODARGIFORMES': '蛙口夜鹰目',
    'STEATORNITHIFORMES': '油鸱目',
}

complete_order = dict(existing_order)
for order_sci in df['Order'].unique():
    if order_sci not in complete_order:
        if order_sci in order_translations:
            complete_order[order_sci] = order_translations[order_sci]
        else:
            complete_order[order_sci] = order_sci

print(f"Complete order mapping: {len(complete_order)}")

# Family mapping - complete translation
family_translations = {
    'Struthionidae': '鸵鸟科',
    'Rheidae': '美洲鸵科',
    'Apterygidae': '几维科',
    'Casuariidae': '鹤鸵科',
    'Spheniscidae': '企鹅科',
    'Diomedeidae': '信天翁科',
    'Procellariidae': '鹱科',
    'Hydrobatidae': '海燕科',
    'Pelecanoididae': '鹲科',
    'Fregatidae': '军舰鸟科',
    'Sulidae': '鲣鸟科',
    'Phalacrocoracidae': '鸬鹚科',
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
    'Momotidae': '咬鹃科',
    'Meropidae': '蜂虎科',
    'Coraciidae': '佛法僧科',
    'Brachypteraciidae': '地佛法僧科',
    'Leptosomatidae': '鹃鴗科',
    'Upupidae': '戴胜科',
    'Phoeniculidae': '林戴胜科',
    'Bucerotidae': '犀鸟科',
    'Picidae': '啄木鸟科',
    'Ramphastidae': '巨嘴鸟科',
    'Nyctibiidae': '油鸱科',
    'Podargidae': '蛙口夜鹰科',
    'Opisthocomidae': '麝雉科',
    'Steatornithidae': '油鸱科',
}

complete_family = dict(existing_family)
for fam_sci in df['Family'].unique():
    if fam_sci not in complete_family:
        if fam_sci in family_translations:
            complete_family[fam_sci] = family_translations[fam_sci]
        else:
            complete_family[fam_sci] = fam_sci

print(f"Complete family mapping: {len(complete_family)}")

# Save complete mappings
print("\nSaving complete mappings...")

# Save genus mapping
with open('data/references/bird_genus_mapping_complete.csv', 'w', encoding='utf-8-sig') as f:
    f.write('Genus_SCI,Genus_CN\n')
    for sci, cn in sorted(complete_genus.items()):
        f.write(f'{sci},{cn}\n')
print(f"Saved genus mapping: {len(complete_genus)} entries")

# Save family mapping
with open('data/references/bird_family_mapping_complete.csv', 'w', encoding='utf-8-sig') as f:
    f.write('Family_SCI,Family_CN\n')
    for sci, cn in sorted(complete_family.items()):
        f.write(f'{sci},{cn}\n')
print(f"Saved family mapping: {len(complete_family)} entries")

# Save order mapping
with open('data/references/bird_order_mapping_complete.csv', 'w', encoding='utf-8-sig') as f:
    f.write('Order_SCI,Order_CN\n')
    for sci, cn in sorted(complete_order.items()):
        f.write(f'{sci},{cn}\n')
print(f"Saved order mapping: {len(complete_order)} entries")

ioc.close()
print("\nDone! Complete mappings generated.")
