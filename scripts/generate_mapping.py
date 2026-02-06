"""
Generate complete Chinese mapping for orders, families, and genera
from species Chinese names in the IOC Excel file.
"""
import sys
sys.path.insert(0, 'src')
import pandas as pd
import re

# Load the IOC Excel
df = pd.read_excel('data/references/Multiling IOC 15.1_d.xlsx')
df.columns = [str(c).strip() for c in df.columns]

# Build genus mapping from species Chinese names
# Pattern: species Chinese names often contain the genus Chinese name as prefix
# e.g., "灰头鸦雀" (Parrotbill) -> genus: 鸦雀属

# Create mapping dictionaries
genus_cn_to_sci = {}  # Chinese genus name -> Latin genus name
family_cn_to_sci = {}  # Chinese family name -> Latin family name
order_cn_to_sci = {}  # Chinese order name -> Latin order name

# For common birds, the genus Chinese name is often the first 2-4 characters
# Family names typically end with 科 (e.g., 鸦雀科)
# Order names typically end with 目 (e.g., 雀形目)

# Known Chinese family names mapping (from CSV and manual)
family_mapping = {
    '鹰科': 'Accipitridae',
    '鸭科': 'Anatidae',
    '雉科': 'Phasianidae',
    '秧鸡科': 'Rallidae',
    '鸻科': 'Charadriidae',
    '鸥科': 'Laridae',
    '雀科': 'Passeridae',
    '燕科': 'Hirundinidae',
    '鹎科': 'Pycnonotidae',
    '画眉科': 'Timaliidae',
    '鸦科': 'Corvidae',
    '山雀科': 'Paridae',
    '绣眼鸟科': 'Zosteropidae',
    '椋鸟科': 'Sturnidae',
    '鹪鹩科': 'Troglodytidae',
    '鹟科': 'Muscicapidae',
    '鸫科': 'Turdidae',
    '百灵科': 'Alaudidae',
    '扇尾莺科': 'Cisticolidae',
    '苇莺科': 'Acrocephalidae',
    '莺科': 'Sylviidae',
    '长尾山雀科': 'Aegithalidae',
    '山椒鸟科': 'Campephagidae',
    '鹎科': 'Pycnonotidae',
    '卷尾科': 'Dicruridae',
    '王鹟科': 'Monarchidae',
    '扇尾鹟科': 'Rhipiduridae',
    '噪鹛科': 'Leiothrichidae',
    '幽鹛科': 'Pellorneidae',
    '雀鹛科': 'Alcippeidae',
    '钩嘴鹛科': 'Timaliidae',
    '斑翅鹛科': 'Vauriidae',
    '丽彩鹛科': 'Irenidae',
    '相思鸟科': 'Leiothrichidae',
    '绣球鸟科': 'Dicaeidae',
    '花蜜鸟科': 'Nectariniidae',
    '啄花鸟科': 'Dicaeidae',
    '太阳鸟科': 'Nectariniidae',
    '麻雀科': 'Passeridae',
    '岩鹨科': 'Prunellidae',
    '八哥科': 'Sturnidae',
    '椋鸟科': 'Sturnidae',
    '牛背鹭科': 'Ardeidae',
    '鹭科': 'Ardeidae',
    '鹳科': 'Ciconiidae',
    '鸬鹚科': 'Phalacrocoracidae',
    '军舰鸟科': 'Fregatidae',
    '鲣鸟科': 'Sulidae',
    '鸊鷉科': 'Podicipedidae',
    '雁鸭科': 'Anatidae',
    '潜鸟科': 'Gaviidae',
    '雨燕科': 'Apodidae',
    '蜂鸟科': 'Trochilidae',
    '夜鹰科': 'Caprimulgidae',
    '雨燕科': 'Apodidae',
    '杜鹃科': 'Cuculidae',
    '鸦鹃科': 'Centropodidae',
    '鸱鸮科': 'Strigidae',
    '草鸮科': 'Tytonidae',
    '佛法僧科': 'Coraciidae',
    '翠鸟科': 'Alcedinidae',
    '蜂虎科': 'Meropidae',
    '犀鸟科': 'Bucerotidae',
    '啄木鸟科': 'Picidae',
    '巨嘴鸟科': 'Ramphastidae',
    '咬鹃科': 'Trogonidae',
    '鹳雀科': 'Ciconiidae',
    '拟鹂科': 'Icteridae',
    '唐纳雀科': 'Thraupidae',
    '美洲雀科': 'Cardinalidae',
    '裸鼻雀科': 'Thraupidae',
    '霸鹟科': 'Tyrannidae',
    '灶鸟科': 'Furnariidae',
    '蚁鹨科': 'Thamnophilidae',
    '伞鸟科': 'Cotingidae',
    '娇鹟科': 'Pipridae',
    '钟鹊科': 'Cracticidae',
    '园丁鸟科': 'Ptilonorhynchidae',
    '极乐鸟科': 'Paradisaeidae',
}

# Known Chinese order names
order_mapping = {
    '雀形目': 'PASSERIFORMES',
    '鸡形目': 'GALLIFORMES',
    '雁形目': 'ANSERIFORMES',
    '鸽形目': 'COLUMBIFORMES',
    '鸻形目': 'CHARADRIIFORMES',
    '鹳形目': 'CICONIIFORMES',
    '雁形目': 'ANSERIFORMES',
    '雁形目': 'ANSERIFORMES',
    '鹰形目': 'ACCIPITRIFORMES',
    '隼形目': 'FALCONIFORMES',
    '鸮形目': 'STRIGIFORMES',
    '夜鹰目': 'CAPRIMULGIFORMES',
    '雨燕目': 'APODIFORMES',
    '佛法僧目': 'CORACIIFORMES',
    '犀鸟目': 'BUCEROTIFORMES',
    '鹃形目': 'CUCULIFORMES',
    '鹦形目': 'PSITTACIFORMES',
    '鹤形目': 'GRUIFORMES',
    '鸻形目': 'CHARADRIIFORMES',
    '鸊鷉目': 'PODICIPEDIFORMES',
    '潜鸟目': 'GAVIIFORMES',
    '企鹅目': 'SPHENISCIFORMES',
    '信天翁目': 'PROCELLARIIFORMES',
    '鹱形目': 'PROCELLARIIFORMES',
    '水禽目': 'SULIFORMES',
    '红鹳目': 'PHOENICOPTERIFORMES',
    '爬树鸟目': 'PICIFORMES',
    '鴷形目': 'PICIFORMES',
}

print("Building comprehensive genus/family/order mapping...")

# Load existing mappings
from metadata.ioc_manager import IOCManager
ioc = IOCManager('data/db/wingscribe.db')

existing_genus = ioc.load_csv_mapping('data/references/bird_genus_mapping.csv', 'Genus_SCI', 'Genus_CN')
existing_family = ioc.load_csv_mapping('data/references/bird_family_mapping.csv', 'Family_SCI', 'Family_CN')
existing_order = ioc.load_csv_mapping('data/references/bird_order_mapping.csv', 'Order_SCI', 'Order_CN')

print(f"Existing genus mapping: {len(existing_genus)}")
print(f"Existing family mapping: {len(existing_family)}")
print(f"Existing order mapping: {len(existing_order)}")

# Merge with known mappings
all_genus = dict(existing_genus)
all_family = dict(existing_family)
all_order = dict(existing_order)

# Add known mappings
all_family.update(family_mapping)
all_order.update(order_mapping)

# Now generate complete mapping for orders
print("\nGenerating complete order mapping...")

# Get all unique orders from Excel
orders_from_excel = df['Order'].unique()
print(f"Orders in Excel: {len(orders_from_excel)}")

# For orders without Chinese name, create one from the Latin name
# Most order names can be translated directly
complete_order_mapping = dict(all_order)

for order_sci in orders_from_excel:
    if order_sci not in complete_order_mapping:
        # Try to translate common orders
        translations = {
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
            'GALBULIFORMES': '喷鴷目',
        }
        if order_sci in translations:
            complete_order_mapping[order_sci] = translations[order_sci]
        else:
            # Fallback: keep Latin name
            complete_order_mapping[order_sci] = order_sci

print(f"Complete order mapping: {len(complete_order_mapping)}")

# Generate complete family mapping
print("\nGenerating complete family mapping...")

families_from_excel = df['Family'].unique()
print(f"Families in Excel: {len(families_from_excel)}")

complete_family_mapping = dict(all_family)

# Add translations for common families
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
    'Phaethontidae': '鹲科',
    'Fregatidae': '军舰鸟科',
    'Sulidae': '鲣鸟科',
    'Phalacrocoracidae': '鸬鹚科',
    'Ardeidae': '鹭科',
    'Threskiornithidae': '鹮科',
    'Ciconiidae': '鹳科',
    'Phaethontidae': '红嘴鹲科',
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
    'Turnicidae': '三趾鹑科',
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
    'Cariamiformes': '鹤鸵目',
}

for fam_sci in families_from_excel:
    if fam_sci not in complete_family_mapping:
        if fam_sci in family_translations:
            complete_family_mapping[fam_sci] = family_translations[fam_sci]
        else:
            complete_family_mapping[fam_sci] = fam_sci

print(f"Complete family mapping: {len(complete_family_mapping)}")

# Generate genus mapping using a heuristic
print("\nGenerating complete genus mapping...")

all_genera = {}
for _, row in df.iterrows():
    parts = str(row.get('IOC_15.1', '')).split()
    if parts:
        genus_sci = parts[0]
        chinese_name = str(row.get('Chinese', ''))
        if genus_sci not in all_genera and chinese_name and chinese_name != 'nan':
            all_genera[genus_sci] = chinese_name

print(f"Genera with Chinese names in Excel: {len(all_genera)}")

# Merge with existing
complete_genus_mapping = dict(existing_genus)
for genus_sci, genus_cn in all_genera.items():
    if genus_sci not in complete_genus_mapping:
        # Extract genus Chinese name from species Chinese name
        # Take first 2-4 characters as genus name
        if len(genus_cn) >= 2:
            # Common patterns
            potential_genus_cn = genus_cn[:min(4, len(genus_cn))]
            complete_genus_mapping[genus_sci] = potential_genus_cn

print(f"Complete genus mapping: {len(complete_genus_mapping)}")

# Save complete mappings
print("\nSaving complete mappings...")

# Save genus mapping
with open('data/references/bird_genus_mapping_complete.csv', 'w', encoding='utf-8-sig') as f:
    f.write('Genus_SCI,Genus_CN\n')
    for sci, cn in sorted(complete_genus_mapping.items()):
        f.write(f'{sci},{cn}\n')
print(f"Saved genus mapping: {len(complete_genus_mapping)} entries")

# Save family mapping
with open('data/references/bird_family_mapping_complete.csv', 'w', encoding='utf-8-sig') as f:
    f.write('Family_SCI,Family_CN\n')
    for sci, cn in sorted(complete_family_mapping.items()):
        f.write(f'{sci},{cn}\n')
print(f"Saved family mapping: {len(complete_family_mapping)} entries")

# Save order mapping
with open('data/references/bird_order_mapping_complete.csv', 'w', encoding='utf-8-sig') as f:
    f.write('Order_SCI,Order_CN\n')
    for sci, cn in sorted(complete_order_mapping.items()):
        f.write(f'{sci},{cn}\n')
print(f"Saved order mapping: {len(complete_order_mapping)} entries")

ioc.close()
print("\nDone! Complete mappings generated.")
