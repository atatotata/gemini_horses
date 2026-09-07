#!/usr/bin/env python3
"""Compare JP and Global text_data categories and counts."""
import apsw
import json

global_db = r"G:\Games\steamapps\common\UmamusumePrettyDerby\UmamusumePrettyDerby_Data\Persistent\master\master.mdb"
jp_db = r"G:\Games\steamapps\common\UmamusumePrettyDerby_Jpn\UmamusumePrettyDerby_Jpn_Data\Persistent\master\master.mdb"

# Global is unencrypted
gconn = apsw.Connection(global_db)
jconn = apsw.Connection(jp_db)

print("=" * 70)
print("TABLE COMPARISON")
print("=" * 70)
g_tables = set(r[0] for r in gconn.execute("SELECT name FROM sqlite_master WHERE type='table'"))
j_tables = set(r[0] for r in jconn.execute("SELECT name FROM sqlite_master WHERE type='table'"))
print(f"Global tables: {len(g_tables)}")
print(f"JP tables: {len(j_tables)}")
common = g_tables & j_tables
g_only = g_tables - j_tables
j_only = j_tables - g_tables
print(f"Common: {len(common)}")
print(f"Global-only: {len(g_only)}")
print(f"JP-only: {len(j_only)}")
print(f"\nJP-only tables (first 40):")
for t in sorted(j_only)[:40]:
    print(f"  {t}")

print("\n" + "=" * 70)
print("text_data CATEGORY COMPARISON")
print("=" * 70)
g_cats = {}
for row in gconn.execute("SELECT category, COUNT(*) FROM text_data GROUP BY category ORDER BY category"):
    g_cats[row[0]] = row[1]
j_cats = {}
for row in jconn.execute("SELECT category, COUNT(*) FROM text_data GROUP BY category ORDER BY category"):
    j_cats[row[0]] = row[1]

all_cats = sorted(set(list(g_cats.keys()) + list(j_cats.keys())))
print(f"{'Cat':>5} {'JP':>7} {'Global':>7} {'Diff':>7}  Note")
print("-" * 70)
jp_total = 0
g_total = 0
for c in all_cats:
    jv = j_cats.get(c, 0)
    gv = g_cats.get(c, 0)
    diff = gv - jv
    note = ""
    if c not in g_cats:
        note = "JP-ONLY"
    elif c not in j_cats:
        note = "GLOBAL-ONLY"
    elif gv == 0:
        note = "EMPTY IN GLOBAL"
    jp_total += jv
    g_total += gv
    print(f"{c:>5} {jv:>7} {gv:>7} {diff:>+7}  {note}")
print("-" * 70)
print(f"{'TOTAL':>5} {jp_total:>7} {g_total:>7} {g_total-jp_total:>+7}")

print("\n" + "=" * 70)
print("character_system_text COMPARISON")
print("=" * 70)
g_cst = gconn.execute("SELECT COUNT(*) FROM character_system_text").fetchone()[0]
j_cst = jconn.execute("SELECT COUNT(*) FROM character_system_text").fetchone()[0]
print(f"JP character_system_text: {j_cst}")
print(f"Global character_system_text: {g_cst}")

# Check character IDs in CST
g_chars = set(r[0] for r in gconn.execute("SELECT DISTINCT character_id FROM character_system_text"))
j_chars = set(r[0] for r in jconn.execute("SELECT DISTINCT character_id FROM character_system_text"))
print(f"JP character IDs in CST: {len(j_chars)}")
print(f"Global character IDs in CST: {len(g_chars)}")
j_only_chars = j_chars - g_chars
g_only_chars = g_chars - j_chars
print(f"JP-only character IDs: {len(j_only_chars)} -> {sorted(j_only_chars)[:20]}...")
print(f"Global-only character IDs: {len(g_only_chars)} -> {sorted(g_only_chars)[:20]}...")

print("\n" + "=" * 70)
print("text_data KEY OVERLAP (category, index) - SAMPLE")
print("=" * 70)
# Check how many exact (category, index) pairs overlap
g_keys = set(r[0:2] for r in gconn.execute("SELECT category, idx FROM text_data"))
j_keys = set(r[0:2] for r in jconn.execute("SELECT category, idx FROM text_data"))
common_keys = g_keys & j_keys
print(f"JP unique (category, index) pairs: {len(j_keys)}")
print(f"Global unique (category, index) pairs: {len(g_keys)}")
print(f"Common pairs: {len(common_keys)}")
print(f"JP-only pairs: {len(j_keys - g_keys)}")
print(f"Global-only pairs: {len(g_keys - j_keys)}")

# Sample 10 common pairs: compare JP vs Global text
print("\nSample 10 common pairs (JP vs Global text):")
count = 0
for cat, idx in sorted(common_keys):
    if count >= 10:
        break
    jp_rows = list(jconn.execute("SELECT text FROM text_data WHERE category=? AND idx=? LIMIT 3", (cat, idx)))
    g_rows = list(gconn.execute("SELECT text FROM text_data WHERE category=? AND idx=? LIMIT 3", (cat, idx)))
    jp_texts = [r[0][:50] for r in jp_rows]
    g_texts = [r[0][:50] for r in g_rows]
    print(f"  [{cat},{idx}]")
    print(f"    JP:  {jp_texts}")
    print(f"    EN:  {g_texts}")
    count += 1

# Check localize_dict-equivalent table
print("\n" + "=" * 70)
print("LOCALIZE TABLE CHECK")
print("=" * 70)
if "localize" in g_tables:
    g_loc = gconn.execute("SELECT COUNT(*) FROM localize").fetchone()[0]
    print(f"Global 'localize' table: {g_loc} rows")
elif "localize_data" in g_tables:
    g_loc = gconn.execute("SELECT COUNT(*) FROM localize_data").fetchone()[0]
    print(f"Global 'localize_data' table: {g_loc} rows")
else:
    print("No localize/localize_data table found in Global")

if "localize" in j_tables:
    j_loc = jconn.execute("SELECT COUNT(*) FROM localize").fetchone()[0]
    print(f"JP 'localize' table: {j_loc} rows")

gconn.close()
jconn.close()
