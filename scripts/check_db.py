import sys
sys.path.insert(0, 'src')
from metadata.ioc_manager import IOCManager
import json

ioc = IOCManager('data/db/feathertrace.db')

# Check Tinamidae
print("=== Tinamidae family ===")
cur = ioc.conn.execute("SELECT DISTINCT family_cn, family_sci FROM taxonomy WHERE family_sci='Tinamidae'")
for r in cur.fetchall():
    print(f"  family_cn: {r['family_cn']}, family_sci: {r['family_sci']}")

# Check genera in Tinamidae
print("\n=== Genera in Tinamidae ===")
cur = ioc.conn.execute("SELECT DISTINCT genus_cn, genus_sci FROM taxonomy WHERE family_sci='Tinamidae' LIMIT 20")
for r in cur.fetchall():
    print(f"  genus_cn: {r['genus_cn']}, genus_sci: {r['genus_sci']}")

# Count total genera in Tinamidae
cur = ioc.conn.execute("SELECT COUNT(DISTINCT genus_sci) FROM taxonomy WHERE family_sci='Tinamidae'")
count = cur.fetchone()[0]
print(f"\nTotal genera in Tinamidae: {count}")

# Check Spheniscidae
print("\n=== Spheniscidae family ===")
cur = ioc.conn.execute("SELECT DISTINCT family_cn, family_sci FROM taxonomy WHERE family_sci='Spheniscidae'")
for r in cur.fetchall():
    print(f"  family_cn: {r['family_cn']}, family_sci: {r['family_sci']}")

# Check some common families
print("\n=== Sample families ===")
cur = ioc.conn.execute("SELECT DISTINCT family_cn, family_sci FROM taxonomy WHERE family_sci IN ('Accipitridae', 'Corvidae', 'Sturnidae')")
for r in cur.fetchall():
    print(f"  family_cn: {r['family_cn']}, family_sci: {r['family_sci']}")

# Check some common genera
print("\n=== Sample genera ===")
cur = ioc.conn.execute("SELECT DISTINCT genus_cn, genus_sci FROM taxonomy WHERE genus_sci IN ('Accipiter', 'Corvus', 'Sturnus')")
for r in cur.fetchall():
    print(f"  genus_cn: {r['genus_cn']}, genus_sci: {r['genus_sci']}")

# Check taxonomy tree for Tinamiformes (should be Tinamidae)
print("\n=== Tinamiformes order ===")
cur = ioc.conn.execute("SELECT DISTINCT order_cn, order_sci FROM taxonomy WHERE order_sci='TINAMIFORMES'")
for r in cur.fetchall():
    print(f"  order_cn: {r['order_cn']}, order_sci: {r['order_sci']}")

ioc.close()
