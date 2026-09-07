#!/usr/bin/env python3
"""
Step 2b: 
1. Identify the full 23 missing extra story IDs
2. Verify story_event_story_data 09 gap
3. Check bundle availability on disk
"""
import apsw
import sqlite3
import os
import json
from pathlib import Path

HACHIMI_DB_KEY = "9c2bab97bcf8c0c4f1a9ea7881a213f6c9ebf9d8d4c6a8e43ce5a259bde7e9fd"
tmp_meta = r'C:\TMP\meta_copy.bin'
master_path = r'G:\Games\steamapps\common\UmamusumePrettyDerby_Jpn\UmamusumePrettyDerby_Jpn_Data\Persistent\master\master.mdb'
dat_root = Path(r'G:\Games\steamapps\common\UmamusumePrettyDerby_Jpn\UmamusumePrettyDerby_Jpn_Data\Persistent\dat')
localized_base = Path(r'G:\Games\steamapps\common\UmamusumePrettyDerby_Jpn\gemini_horses\localized_data\assets\story\data')

# ==============================
# Open meta
# ==============================
uri = f'file:{tmp_meta}?hexkey={HACHIMI_DB_KEY}'
meta = apsw.Connection(uri, flags=apsw.SQLITE_OPEN_READONLY | apsw.SQLITE_OPEN_URI)
mcur = meta.cursor()

# Collect all meta story IDs with full info
meta_story = {}
for row in mcur.execute("SELECT n, h, e FROM a WHERE n LIKE 'story/data/%'"):
    n, h, e = row
    parts = n.split('/')
    if len(parts) >= 4 and 'storytimeline_' in parts[-1]:
        sid_str = parts[-1].replace('storytimeline_', '')
        try:
            sid = int(sid_str)
            meta_story[sid] = {'n': n, 'h': h, 'e': e, 'prefix': parts[2]}
        except ValueError:
            pass

# ==============================
# Open master.mdb
# ==============================
master = sqlite3.connect(f'file:{master_path}?mode=ro', uri=True)
mcur2 = master.cursor()

# --- story_extra_story_data: all 49 unique IDs ---
print("=" * 60)
print("PART 2a: story_extra_story_data - All unique IDs")
print("=" * 60)

all_extra_ids = set()
for num in range(1, 6):
    type_col = f'story_type_{num}'
    sid_col = f'story_id_{num}'
    rows = mcur2.execute(
        f"SELECT story_id_{num} FROM story_extra_story_data WHERE story_type_{num} != 0"
    ).fetchall()
    for r in rows:
        sid = r[0]
        if sid and sid > 1e7 and sid < 999999999 and sid < 1.6e9:
            all_extra_ids.add(int(sid))

print(f"Total unique extra story IDs: {len(all_extra_ids)}")

# Localized
localized_ids = set()
if localized_base.exists():
    for f in localized_base.rglob('storytimeline_*.json'):
        stem = f.stem
        sid_str = stem.replace('storytimeline_', '')
        try:
            localized_ids.add(int(sid_str))
        except ValueError:
            pass

# Compute missing
missing_all = sorted(all_extra_ids - localized_ids)
print(f"Localized extra IDs: {len(all_extra_ids & localized_ids)}")
print(f"Missing from localized: {len(missing_all)}")

# Group missing by prefix
missing_by_prefix = {}
for sid in missing_all:
    prefix = str(sid).zfill(9)[:2]
    missing_by_prefix.setdefault(prefix, []).append(sid)

print("\nMissing by prefix:")
for p in sorted(missing_by_prefix.keys()):
    sids = missing_by_prefix[p]
    print(f"  prefix {p}: {len(sids)} IDs")
    for sid in sids:
        info = meta_story.get(sid, {})
        print(f"    {sid}: {info.get('n', 'NOT IN META')}")

# --- story_event_story_data: 09 prefix analysis ---
print("\n" + "=" * 60)
print("PART 2b: story_event_story_data - 09 prefix gap analysis")
print("=" * 60)

cols = mcur2.execute("PRAGMA table_info(story_event_story_data)").fetchall()
col_names = [c[1] for c in cols]
print(f"Columns ({len(col_names)}): {col_names}")

# Count rows
row_count = mcur2.execute("SELECT COUNT(*) FROM story_event_story_data").fetchone()[0]
print(f"Row count: {row_count}")

# Extract unique story IDs (only story_id_* columns, filter by story_type_*=1)
event_ids_type1 = set()
event_ids_all = set()
for num in range(1, 20):  # Try up to 20 story slots
    type_col = f'story_type_{num}'
    sid_col = f'story_id_{num}'
    if type_col not in col_names or sid_col not in col_names:
        continue
    
    # Type 1 stories only
    rows = mcur2.execute(
        f"SELECT story_id_{num} FROM story_event_story_data WHERE story_type_{num} = 1"
    ).fetchall()
    for r in rows:
        sid = r[0]
        if sid and sid > 1e7 and sid < 999999999 and sid < 1.6e9:
            event_ids_type1.add(int(sid))
    
    # All stories (any type)
    rows = mcur2.execute(
        f"SELECT story_id_{num} FROM story_event_story_data WHERE story_type_{num} != 0"
    ).fetchall()
    for r in rows:
        sid = r[0]
        if sid and sid > 1e7 and sid < 999999999 and sid < 1.6e9:
            event_ids_all.add(int(sid))

print(f"story_event_story_data unique IDs (type=1 only): {len(event_ids_type1)}")
print(f"story_event_story_data unique IDs (all types): {len(event_ids_all)}")

# Breakdown by prefix
for label, ids in [("type=1", event_ids_type1), ("all types", event_ids_all)]:
    by_p = {}
    for sid in ids:
        p = str(sid).zfill(9)[:2]
        by_p.setdefault(p, []).append(sid)
    print(f"\n  {label}:")
    for p in sorted(by_p.keys()):
        print(f"    prefix {p}: {len(by_p[p])} IDs")

# 09 prefix gap: type=1 IDs vs localized 09 IDs
event_09_type1 = {sid for sid in event_ids_type1 if str(sid).zfill(9)[:2] == '09'}
local_09 = {sid for sid in localized_ids if str(sid).zfill(9)[:2] == '09'}
missing_09_type1 = sorted(event_09_type1 - local_09)
print(f"\n09 prefix analysis (type=1 only):")
print(f"  Event type=1 IDs: {len(event_09_type1)}")
print(f"  Localized 09 IDs: {len(local_09)}")
print(f"  Missing from localized: {len(missing_09_type1)}")
if missing_09_type1:
    print(f"  First 10 missing: {missing_09_type1[:10]}")
else:
    print(f"  No gap - all event 09 type=1 IDs are in localized!")

# Also check: meta 09 count vs localized 09
meta_09 = {sid for sid, info in meta_story.items() if info['prefix'] == '09'}
print(f"\nMeta 09 count: {len(meta_09)}")
print(f"Localized 09 count: {len(local_09)}")
print(f"Meta - localized 09 gap: {len(meta_09 - local_09)}")

# All events in meta_09
event_09_all = {sid for sid in event_ids_all if str(sid).zfill(9)[:2] == '09'}
print(f"Event story data all-type 09 IDs: {len(event_09_all)}")
meta_not_in_event = sorted(meta_09 - event_09_all)
if meta_not_in_event:
    print(f"  Meta 09 IDs not in story_event_story_data ({len(meta_not_in_event)}): {meta_not_in_event[:10]}")

# ==============================
# PART 3: Bundle availability check for missing IDs
# ==============================
print("\n" + "=" * 60)
print("PART 3: BUNDLE AVAILABILITY for missing extra stories")
print("=" * 60)

for sid in missing_all:
    info = meta_story.get(sid)
    if not info:
        print(f"  {sid}: NOT IN META!")
        continue
    h = info['h']
    bundle_path = dat_root / h[:2] / h
    exists = bundle_path.exists()
    size = bundle_path.stat().st_size if exists else 0
    print(f"  {sid}: h={h[:20]}..., path={bundle_path}, exists={exists}, size={size}")

# ==============================
# SAVE: Missing IDs + meta info for extraction
# ==============================
extraction_data = []
for sid in missing_all:
    info = meta_story.get(sid)
    if not info:
        print(f"  {sid}: NOT IN META!")
        continue
    h = info['h']
    bundle_path = dat_root / h[:2] / h
    extraction_data.append({
        'sid': sid,
        'prefix': str(sid).zfill(9)[:2],
        'sub': str(sid).zfill(9)[2:6],
        'n': info['n'],
        'h': h,
        'e': info['e'],
        'bundle_path': str(bundle_path),
        'bundle_exists': bundle_path.exists(),
    })

with open(r'C:\TMP\extraction_plan.json', 'w') as f:
    json.dump(extraction_data, f, indent=2)
print(f"\nSaved extraction plan: {len(extraction_data)} bundles to C:\\TMP\\extraction_plan.json")

meta.close()
master.close()
