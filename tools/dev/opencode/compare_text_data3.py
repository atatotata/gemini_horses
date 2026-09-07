#!/usr/bin/env python3
"""Compare JP and Global text_data - final version with quoted identifiers."""
import apsw

global_db = r"G:\Games\steamapps\common\UmamusumePrettyDerby\UmamusumePrettyDerby_Data\Persistent\master\master.mdb"
jp_db = r"G:\Games\steamapps\common\UmamusumePrettyDerby_Jpn\UmamusumePrettyDerby_Jpn_Data\Persistent\master\master.mdb"

gconn = apsw.Connection(global_db)
jconn = apsw.Connection(jp_db)

# Key overlap using quoted column names
print("=" * 70)
print("text_data KEY OVERLAP")
print("=" * 70)

g_keys = set()
for r in gconn.execute('SELECT "category", "index" FROM text_data'):
    g_keys.add(r)
j_keys = set()
for r in jconn.execute('SELECT "category", "index" FROM text_data'):
    j_keys.add(r)

common_keys = g_keys & j_keys
print(f"JP unique (category, index) pairs: {len(j_keys)}")
print(f"Global unique (category, index) pairs: {len(g_keys)}")
print(f"Common pairs: {len(common_keys)}")
print(f"JP-only pairs: {len(j_keys - g_keys)}")
print(f"Global-only pairs: {len(g_keys - j_keys)}")

# Sample 15 common pairs
print(f"\nSample 15 common pairs (JP vs Global text):")
for cat, idx in sorted(common_keys)[:15]:
    jp_rows = jconn.execute('SELECT text FROM text_data WHERE category=? AND "index"=? LIMIT 2', (cat, idx)).fetchall()
    g_rows = gconn.execute('SELECT text FROM text_data WHERE category=? AND "index"=? LIMIT 2', (cat, idx)).fetchall()
    jp_texts = [r[0][:70] for r in jp_rows]
    g_texts = [r[0][:70] for r in g_rows]
    print(f"  [{cat},{idx}]")
    print(f"    JP:  {jp_texts}")
    print(f"    EN:  {g_texts}")

# character_system_text key overlap
print("\n" + "=" * 70)
print("character_system_text KEY OVERLAP")
print("=" * 70)

g_cst_keys = set()
for r in gconn.execute('SELECT "character_id", "voice_id" FROM character_system_text'):
    g_cst_keys.add(r)
j_cst_keys = set()
for r in jconn.execute('SELECT "character_id", "voice_id" FROM character_system_text'):
    j_cst_keys.add(r)

common_cst = g_cst_keys & j_cst_keys
print(f"JP unique (character_id, voice_id) pairs: {len(j_cst_keys)}")
print(f"Global unique (character_id, voice_id) pairs: {len(g_cst_keys)}")
print(f"Common pairs: {len(common_cst)}")
print(f"JP-only pairs: {len(j_cst_keys - g_cst_keys)}")
print(f"Global-only pairs: {len(g_cst_keys - j_cst_keys)}")

# Sample 5 common CST pairs
print(f"\nSample 5 common CST pairs (JP vs Global text):")
for char_id, voice_id in sorted(common_cst)[:5]:
    jp_row = jconn.execute('SELECT text FROM character_system_text WHERE character_id=? AND voice_id=?', (char_id, voice_id)).fetchone()
    g_row = gconn.execute('SELECT text FROM character_system_text WHERE character_id=? AND voice_id=?', (char_id, voice_id)).fetchone()
    print(f"  [{char_id},{voice_id}]")
    print(f"    JP:  {jp_row[0][:70] if jp_row else 'N/A'}")
    print(f"    EN:  {g_row[0][:70] if g_row else 'N/A'}")

# Check if Global text is already English (not JP)
print("\n" + "=" * 70)
print("LANGUAGE CHECK: Is Global text_data already English?")
print("=" * 70)
import re
jp_regex = re.compile(r'[\u3040-\u309F\u30A0-\u30FF\u4E00-\u9FAF]')  # Hiragana, Katakana, CJK
# Sample 100 random rows from Global
sample_rows = gconn.execute('SELECT text FROM text_data LIMIT 100').fetchall()
jp_count = sum(1 for r in sample_rows if jp_regex.search(r[0]))
en_count = sum(1 for r in sample_rows if not jp_regex.search(r[0]))
print(f"Of 100 sampled Global text_data rows:")
print(f"  Contains JP characters: {jp_count}")
print(f"  No JP characters (likely EN): {en_count}")
# Show a few EN examples
en_examples = [r[0][:80] for r in sample_rows if not jp_regex.search(r[0])][:5]
print(f"  EN examples: {en_examples}")

# Now check CST
print("\nCST language check:")
sample_cst = gconn.execute('SELECT text FROM character_system_text LIMIT 100').fetchall()
jp_cst = sum(1 for r in sample_cst if jp_regex.search(r[0]))
en_cst = sum(1 for r in sample_cst if not jp_regex.search(r[0]))
print(f"Of 100 sampled Global CST rows:")
print(f"  Contains JP characters: {jp_cst}")
print(f"  No JP characters (likely EN): {en_cst}")
en_cst_examples = [r[0][:80] for r in sample_cst if not jp_regex.search(r[0])][:5]
print(f"  EN examples: {en_cst_examples}")

# Check if Global text_data has JP at all
print("\n" + "=" * 70)
print("FULL LANGUAGE SCAN (first 5000 rows)")
print("=" * 50)
sample_5k = gconn.execute('SELECT text FROM text_data LIMIT 5000').fetchall()
jp_5k = sum(1 for r in sample_5k if jp_regex.search(r[0]))
print(f"Global text_data (5000 rows): {jp_5k} contain JP, {5000-jp_5k} are EN/other")

cst_5k = gconn.execute('SELECT text FROM character_system_text LIMIT 5000').fetchall()
jp_cst_5k = sum(1 for r in cst_5k if jp_regex.search(r[0]))
print(f"Global CST (5000 rows): {jp_cst_5k} contain JP, {len(cst_5k)-jp_cst_5k} are EN/other")

gconn.close()
jconn.close()
