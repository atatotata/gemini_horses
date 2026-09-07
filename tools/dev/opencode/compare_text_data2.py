#!/usr/bin/env python3
"""Compare JP and Global text_data - fixed column names."""
import apsw

global_db = r"G:\Games\steamapps\common\UmamusumePrettyDerby\UmamusumePrettyDerby_Data\Persistent\master\master.mdb"
jp_db = r"G:\Games\steamapps\common\UmamusumePrettyDerby_Jpn\UmamusumePrettyDerby_Jpn_Data\Persistent\master\master.mdb"

gconn = apsw.Connection(global_db)
jconn = apsw.Connection(jp_db)

# Get actual column names
print("=== Global text_data columns ===")
desc = gconn.execute("PRAGMA table_info(text_data)").fetchall()
for d in desc:
    print(f"  {d}")

print("\n=== JP text_data columns ===")
desc = jconn.execute("PRAGMA table_info(text_data)").fetchall()
for d in desc:
    print(f"  {d}")

print("\n=== Global character_system_text columns ===")
desc = gconn.execute("PRAGMA table_info(character_system_text)").fetchall()
for d in desc:
    print(f"  {d}")

print("\n=== JP character_system_text columns ===")
desc = jconn.execute("PRAGMA table_info(character_system_text)").fetchall()
for d in desc:
    print(f"  {d}")

# Now do the key overlap comparison with correct column names
# From the schema, text_data likely has: category, index, sub_index (or similar)
print("\n" + "=" * 70)
print("text_data KEY OVERLAP")
print("=" * 70)

# Use the first row sample to determine column names
sample = gconn.execute("SELECT * FROM text_data LIMIT 1").fetchone()
print(f"Global sample row: {sample}")
sample_j = jconn.execute("SELECT * FROM text_data LIMIT 1").fetchone()
print(f"JP sample row: {sample_j}")

# Get column names from PRAGMA
g_cols = [d[1] for d in gconn.execute("PRAGMA table_info(text_data)").fetchall()]
j_cols = [d[1] for d in jconn.execute("PRAGMA table_info(text_data)").fetchall()]
print(f"Global columns: {g_cols}")
print(f"JP columns: {j_cols}")

# Build key query using actual column names
# Usually: category, idx (or index), sub_idx, text
g_key_cols = g_cols[:3]  # First 3 columns are typically the key
j_key_cols = j_cols[:3]
g_key_sql = ", ".join(g_key_cols)
j_key_sql = ", ".join(j_key_cols)

g_keys = set()
for r in gconn.execute(f"SELECT {g_key_sql} FROM text_data"):
    g_keys.add(tuple(r))
j_keys = set()
for r in jconn.execute(f"SELECT {j_key_sql} FROM text_data"):
    j_keys.add(tuple(r))

# Align by using first two columns as canonical key (category, index)
# Truncate to 2 columns for comparison
g_keys_2 = set(k[:2] for k in g_keys)
j_keys_2 = set(k[:2] for k in j_keys)
common_keys = g_keys_2 & j_keys_2

print(f"\nJP unique (cat, idx) pairs: {len(j_keys_2)}")
print(f"Global unique (cat, idx) pairs: {len(g_keys_2)}")
print(f"Common pairs: {len(common_keys)}")
print(f"JP-only pairs: {len(j_keys_2 - g_keys_2)}")
print(f"Global-only pairs: {len(g_keys_2 - j_keys_2)}")

# Sample 10 common pairs
print(f"\nSample 10 common pairs (JP vs Global):")
count = 0
g_key_names = g_key_cols[:2]
for cat, idx in sorted(common_keys)[:10]:
    jp_rows = list(jconn.execute(f"SELECT text FROM text_data WHERE {j_cols[0]}=? AND {j_cols[1]}=? LIMIT 3", (cat, idx)))
    g_rows = list(gconn.execute(f"SELECT text FROM text_data WHERE {g_cols[0]}=? AND {g_cols[1]}=? LIMIT 3", (cat, idx)))
    jp_texts = [r[0][:60] for r in jp_rows]
    g_texts = [r[0][:60] for r in g_rows]
    print(f"  [{cat},{idx}]")
    print(f"    JP:  {jp_texts}")
    print(f"    EN:  {g_texts}")

# Check localize tables
print("\n" + "=" * 70)
print("LOCALIZE TABLES")
print("=" * 70)
g_tables = set(r[0] for r in gconn.execute("SELECT name FROM sqlite_master WHERE type='table'"))
for t in sorted(g_tables):
    if 'local' in t.lower():
        count = gconn.execute(f"SELECT COUNT(*) FROM [{t}]").fetchone()[0]
        print(f"  Global '{t}': {count} rows")
        # Sample
        for r in gconn.execute(f"SELECT * FROM [{t}] LIMIT 2"):
            print(f"    Sample: {r}")

j_tables = set(r[0] for r in jconn.execute("SELECT name FROM sqlite_master WHERE type='table'"))
for t in sorted(j_tables):
    if 'local' in t.lower():
        count = jconn.execute(f"SELECT COUNT(*) FROM [{t}]").fetchone()[0]
        print(f"  JP '{t}': {count} rows")

gconn.close()
jconn.close()
