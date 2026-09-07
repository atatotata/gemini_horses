#!/usr/bin/env python3
"""Full meta analysis + localized data gap identification."""
import apsw
import os
import sqlite3
from pathlib import Path

HACHIMI_DB_KEY = "9c2bab97bcf8c0c4f1a9ea7881a213f6c9ebf9d8d4c6a8e43ce5a259bde7e9fd"
tmp = r'C:\TMP\meta_copy.bin'

# === Open meta ===
uri = f'file:{tmp}?hexkey={HACHIMI_DB_KEY}'
db = apsw.Connection(uri, flags=apsw.SQLITE_OPEN_READONLY | apsw.SQLITE_OPEN_URI)
cur = db.cursor()

total = cur.execute('SELECT COUNT(*) FROM a').fetchone()[0]
print(f"Meta total rows: {total}")

# === Prefix counts for story/data/XX/.../storytimeline_XXX ===
prefix_counts = {}
for row in cur.execute("SELECT n FROM a WHERE n LIKE 'story/data/%'"):
    n = row[0]
    parts = n.split('/')
    if len(parts) >= 4 and 'storytimeline_' in parts[-1]:
        prefix = parts[2]
        prefix_counts[prefix] = prefix_counts.get(prefix, 0) + 1

print("\n=== Meta storytimeline counts by prefix ===")
for p in sorted(prefix_counts.keys()):
    print(f"  prefix {p}: {prefix_counts[p]}")

# === Now get all meta story IDs as ints ===
meta_ids = {}
for row in cur.execute("SELECT n, h, e FROM a WHERE n LIKE 'story/data/%'"):
    n, h, e = row
    parts = n.split('/')
    if len(parts) >= 4 and 'storytimeline_' in parts[-1]:
        sid_str = parts[-1].replace('storytimeline_', '')
        try:
            sid = int(sid_str)
            prefix = parts[2]
            meta_ids[sid] = {'n': n, 'h': h, 'e': e, 'prefix': prefix}
        except ValueError:
            pass

print(f"\nTotal meta story IDs: {len(meta_ids)}")

# === Localized data coverage ===
localized_base = Path(r'G:\Games\steamapps\common\UmamusumePrettyDerby_Jpn\gemini_horses\localized_data\assets\story\data')
localized_ids = set()
if localized_base.exists():
    for f in localized_base.rglob('storytimeline_*.json'):
        stem = f.stem  # storytimeline_XXXXXXXXX
        sid_str = stem.replace('storytimeline_', '')
        try:
            localized_ids.add(int(sid_str))
        except ValueError:
            pass
    print(f"Localized story timeline IDs: {len(localized_ids)}")
else:
    print("Localized base path not found!")

# === Coverage by prefix ===
print("\n=== Coverage by prefix ===")
all_prefixes = sorted(set(
    list(prefix_counts.keys()) +
    [str(sid).zfill(9)[:2] for sid in localized_ids]
))
for p in all_prefixes:
    meta_p = sum(1 for sid, info in meta_ids.items() if info['prefix'] == p)
    local_p = sum(1 for sid in localized_ids if str(sid).zfill(9)[:2] == p)
    print(f"  prefix {p}: meta={meta_p}, localized={local_p}")

# === Extra Stories seasonal gap: IDs in meta but not in localized ===
# Prefix 10 = Extra Stories seasonal
extra_prefixes = ['10']
for p in extra_prefixes:
    meta_p = {sid: info for sid, info in meta_ids.items() if info['prefix'] == p}
    local_p = {sid for sid in localized_ids if str(sid).zfill(9)[:2] == p}
    missing = sorted(set(meta_p.keys()) - local_p)
    print(f"\n=== Prefix {p} (Extra Stories) ===")
    print(f"  Meta count: {len(meta_p)}")
    print(f"  Localized count: {len(local_p)}")
    print(f"  Missing in localized: {len(missing)}")
    for sid in missing:
        info = meta_p[sid]
        print(f"    {sid}: n={info['n']}, h={info['h'][:16]}...")

# === Prefix 09 gap ===
p09 = '09'
meta_p09 = {sid: info for sid, info in meta_ids.items() if info['prefix'] == p09}
local_p09 = {sid for sid in localized_ids if str(sid).zfill(9)[:2] == p09}
missing_p09 = sorted(set(meta_p09.keys()) - local_p09)
print(f"\n=== Prefix {p09} (Story Event) ===")
print(f"  Meta count: {len(meta_p09)}")
print(f"  Localized count: {len(local_p09)}")
print(f"  Missing in localized: {len(missing_p09)}")
if missing_p09:
    for sid in missing_p09[:10]:
        info = meta_p09[sid]
        print(f"    {sid}: n={info['n']}")
    if len(missing_p09) > 10:
        print(f"    ... and {len(missing_p09) - 10} more")

# Save missing seasonal IDs for next step
import json
with open(r'C:\TMP\missing_seasonal_ids.json', 'w') as f:
    json.dump({
        'missing_10': sorted(meta_p.keys() - local_p) if '10' in extra_prefixes else [],
        'missing_09': missing_p09,
    }, f, indent=2)
print(f"\nSaved missing IDs to C:\\TMP\\missing_seasonal_ids.json")

db.close()
