#!/usr/bin/env python3
"""
Complete analysis:
1. Meta prefix counts
2. master.mdb story_extra_story_data for seasonal IDs
3. Localized coverage gap
4. Story Event 09 gap
5. Missing IDs verification
"""
import apsw
import os
import json
import sqlite3
from pathlib import Path

HACHIMI_DB_KEY = "9c2bab97bcf8c0c4f1a9ea7881a213f6c9ebf9d8d4c6a8e43ce5a259bde7e9fd"
tmp_meta = r'C:\TMP\meta_copy.bin'
master_path = r'G:\Games\steamapps\common\UmamusumePrettyDerby_Jpn\UmamusumePrettyDerby_Jpn_Data\Persistent\master\master.mdb'

# ==============================
# PART 1: META QUERIES
# ==============================
print("=" * 60)
print("PART 1: META DATABASE")
print("=" * 60)

uri = f'file:{tmp_meta}?hexkey={HACHIMI_DB_KEY}'
meta = apsw.Connection(uri, flags=apsw.SQLITE_OPEN_READONLY | apsw.SQLITE_OPEN_URI)
mcur = meta.cursor()

total = mcur.execute('SELECT COUNT(*) FROM a').fetchone()[0]
print(f"Meta total rows: {total}")

# Schema
print("\nTable 'a' columns:")
for row in mcur.execute("PRAGMA table_info(a)"):
    print(f"  {row[1]} ({row[2]})")

# Prefix counts for story data
prefix_counts = {}
meta_story = {}  # sid -> {n, h, e, prefix}
for row in mcur.execute("SELECT n, h, e FROM a WHERE n LIKE 'story/data/%'"):
    n, h, e = row
    parts = n.split('/')
    if len(parts) >= 4 and 'storytimeline_' in parts[-1]:
        sid_str = parts[-1].replace('storytimeline_', '')
        try:
            sid = int(sid_str)
            prefix = parts[2]
            prefix_counts[prefix] = prefix_counts.get(prefix, 0) + 1
            meta_story[sid] = {'n': n, 'h': h, 'e': e, 'prefix': prefix}
        except ValueError:
            pass

print(f"\nMeta story entries: {len(meta_story)}")
print("\nBy prefix:")
for p in sorted(prefix_counts.keys()):
    print(f"  prefix {p}: {prefix_counts[p]}")

# ==============================
# PART 2: MASTER.MDB EXTRA STORY DATA
# ==============================
print("\n" + "=" * 60)
print("PART 2: MASTER.MDB (story_extra_story_data)")
print("=" * 60)

master = sqlite3.connect(f'file:{master_path}?mode=ro', uri=True)
mcur2 = master.cursor()

# Check if table exists
tables = [r[0] for r in mcur2.execute("SELECT name FROM sqlite_master WHERE type='table'")]
print(f"Tables in master.mdb: {len(tables)}")

# Find story_extra_story_data related tables
extra_tables = [t for t in tables if 'extra' in t.lower()]
print(f"Extra story tables: {extra_tables}")

# Check for story_extra_story_data
if 'story_extra_story_data' in tables:
    # Get column info
    cols = mcur2.execute("PRAGMA table_info(story_extra_story_data)").fetchall()
    print(f"\nstory_extra_story_data columns ({len(cols)}):")
    for c in cols:
        print(f"  {c[1]} ({c[2]})")
    
    # Count rows
    row_count = mcur2.execute("SELECT COUNT(*) FROM story_extra_story_data").fetchone()[0]
    print(f"\nRow count: {row_count}")
    
    # Sample first row
    first = mcur2.execute("SELECT * FROM story_extra_story_data LIMIT 1").fetchone()
    col_names = [c[1] for c in cols]
    print(f"\nSample row:")
    for cn, val in zip(col_names, first):
        print(f"  {cn} = {val}")
    
    # Extract story IDs: for each story_type_N where != 0, collect story_id_N
    story_ids = set()
    for c in cols:
        col_name = c[1]
        if col_name.startswith('story_type_'):
            num = col_name.replace('story_type_', '')
            sid_col = f'story_id_{num}'
            if sid_col in col_names:
                rows = mcur2.execute(
                    f"SELECT story_id_{num} FROM story_extra_story_data WHERE story_type_{num} != 0"
                ).fetchall()
                for r in rows:
                    sid = r[0]
                    if sid and sid > 1e7 and sid < 999999999 and sid < 1.6e9:
                        story_ids.add(int(sid))
    
    print(f"\nUnique extra story IDs (type!=0, valid range): {len(story_ids)}")
    
    # Categorize by prefix
    extra_by_prefix = {}
    for sid in sorted(story_ids):
        prefix = str(sid).zfill(9)[:2]
        extra_by_prefix.setdefault(prefix, []).append(sid)
    
    print("\nBy prefix:")
    for p in sorted(extra_by_prefix.keys()):
        print(f"  prefix {p}: {len(extra_by_prefix[p])} IDs")
        for sid in extra_by_prefix[p][:5]:
            print(f"    {sid}")
        if len(extra_by_prefix[p]) > 5:
            print(f"    ... and {len(extra_by_prefix[p]) - 5} more")
else:
    print("story_extra_story_data table NOT FOUND")
    # Try alternative table names
    for t in tables:
        if 'story' in t.lower():
            print(f"  Found: {t}")

# Also check story_event_story_data
event_tables = [t for t in tables if 'event' in t.lower() and 'story' in t.lower()]
print(f"\nEvent story tables: {event_tables}")

for tbl in event_tables:
    cols = mcur2.execute(f"PRAGMA table_info({tbl})").fetchall()
    row_count = mcur2.execute(f"SELECT COUNT(*) FROM {tbl}").fetchone()[0]
    col_names = [c[1] for c in cols]
    print(f"\n{tbl}: {row_count} rows")
    
    # Extract story IDs
    event_ids = set()
    for c in cols:
        col_name = c[1]
        if col_name.startswith('story_type_'):
            num = col_name.replace('story_type_', '')
            sid_col = f'story_id_{num}'
            if sid_col in col_names:
                rows = mcur2.execute(
                    f"SELECT story_id_{num} FROM {tbl} WHERE story_type_{num} != 0"
                ).fetchall()
                for r in rows:
                    sid = r[0]
                    if sid and sid > 1e7 and sid < 999999999 and sid < 1.6e9:
                        event_ids.add(int(sid))
    
    event_by_prefix = {}
    for sid in sorted(event_ids):
        prefix = str(sid).zfill(9)[:2]
        event_by_prefix.setdefault(prefix, []).append(sid)
    
    print(f"  Unique event story IDs: {len(event_ids)}")
    for p in sorted(event_by_prefix.keys()):
        print(f"  prefix {p}: {len(event_by_prefix[p])} IDs")

# ==============================
# PART 3: LOCALIZED DATA
# ==============================
print("\n" + "=" * 60)
print("PART 3: LOCALIZED DATA COVERAGE")
print("=" * 60)

localized_base = Path(r'G:\Games\steamapps\common\UmamusumePrettyDerby_Jpn\gemini_horses\localized_data\assets\story\data')
localized_ids = set()
if localized_base.exists():
    for f in localized_base.rglob('storytimeline_*.json'):
        stem = f.stem
        sid_str = stem.replace('storytimeline_', '')
        try:
            localized_ids.add(int(sid_str))
        except ValueError:
            pass
    print(f"Localized story timeline IDs: {len(localized_ids)}")
else:
    print(f"Localized base NOT FOUND: {localized_base}")

localized_by_prefix = {}
for sid in localized_ids:
    prefix = str(sid).zfill(9)[:2]
    localized_by_prefix.setdefault(prefix, []).append(sid)

print("\nBy prefix:")
for p in sorted(localized_by_prefix.keys()):
    print(f"  prefix {p}: {len(localized_by_prefix[p])} IDs")

# ==============================
# PART 4: GAP ANALYSIS
# ==============================
print("\n" + "=" * 60)
print("PART 4: GAP ANALYSIS (meta present, localized missing)")
print("=" * 60)

all_prefixes = sorted(set(list(prefix_counts.keys()) + list(localized_by_prefix.keys())))
for p in all_prefixes:
    meta_n = prefix_counts.get(p, 0)
    local_n = len(localized_by_prefix.get(p, []))
    # IDs in meta but not in localized
    meta_sids = {sid for sid, info in meta_story.items() if info['prefix'] == p}
    local_sids = {sid for sid in localized_ids if str(sid).zfill(9)[:2] == p}
    missing = sorted(meta_sids - local_sids)
    extra = sorted(local_sids - meta_sids)
    print(f"\n  prefix {p}:")
    print(f"    meta: {meta_n}, localized: {local_n}")
    if missing:
        print(f"    MISSING in localized ({len(missing)}): {missing[:10]}{'...' if len(missing)>10 else ''}")
    if extra:
        print(f"    EXTRA in localized ({len(extra)}): {extra[:10]}{'...' if len(extra)>10 else ''}")

# ==============================
# PART 5: SAVE MISSING IDs
# ==============================
print("\n" + "=" * 60)
print("PART 5: MISSING IDS FOR EXTRACTION")
print("=" * 60)

# Focus on prefix 10 (Extra Stories seasonal)
meta_10 = {sid: info for sid, info in meta_story.items() if info['prefix'] == '10'}
local_10 = {sid for sid in localized_ids if str(sid).zfill(9)[:2] == '10'}
missing_10 = sorted(meta_10.keys() - local_10)
print(f"Missing prefix 10 IDs: {len(missing_10)}")
for sid in missing_10:
    info = meta_10[sid]
    print(f"  {sid}: n={info['n']}, h={info['h'][:16]}..., e={info['e']}")

# Verify each missing ID exists in meta
print("\nVerifying missing 10 IDs in meta:")
for sid in missing_10:
    path_check = f"story/data/{str(sid).zfill(9)[:2]}/{str(sid).zfill(9)[2:6]}/storytimeline_{str(sid).zfill(9)}"
    exists = mcur.execute("SELECT COUNT(*) FROM a WHERE n=?", (path_check,)).fetchone()[0]
    print(f"  {sid}: path={path_check}, in_meta={exists > 0}")

# Save for extraction
result = {
    'meta_total': total,
    'meta_story_count': len(meta_story),
    'prefix_counts': prefix_counts,
    'missing_10': [{'sid': sid, 'n': meta_10[sid]['n'], 'h': meta_10[sid]['h'], 'e': meta_10[sid]['e']} for sid in missing_10],
    'missing_09': [],
}
with open(r'C:\TMP\analysis_result.json', 'w') as f:
    json.dump(result, f, indent=2)
print(f"\nSaved to C:\\TMP\\analysis_result.json")

meta.close()
master.close()
