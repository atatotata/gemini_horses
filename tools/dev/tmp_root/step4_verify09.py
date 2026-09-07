#!/usr/bin/env python3
import apsw
import sqlite3
from pathlib import Path

HACHIMI_DB_KEY = "9c2bab97bcf8c0c4f1a9ea7881a213f6c9ebf9d8d4c6a8e43ce5a259bde7e9fd"
tmp_meta = r'C:\TMP\meta_copy.bin'
master_path = r'G:\Games\steamapps\common\UmamusumePrettyDerby_Jpn\UmamusumePrettyDerby_Jpn_Data\Persistent\master\master.mdb'
localized_base = Path(r'G:\Games\steamapps\common\UmamusumePrettyDerby_Jpn\gemini_horses\localized_data\assets\story\data')

uri = f'file:{tmp_meta}?hexkey={HACHIMI_DB_KEY}'
meta = apsw.Connection(uri, flags=apsw.SQLITE_OPEN_READONLY | apsw.SQLITE_OPEN_URI)
mcur = meta.cursor()

meta_09 = set()
for row in mcur.execute("SELECT n FROM a WHERE n LIKE 'story/data/09/%'"):
    n = row[0]
    parts = n.split('/')
    if len(parts) >= 4 and 'storytimeline_' in parts[-1]:
        sid_str = parts[-1].replace('storytimeline_', '')
        try:
            meta_09.add(int(sid_str))
        except ValueError:
            pass

master = sqlite3.connect(f'file:{master_path}?mode=ro', uri=True)
mcur2 = master.cursor()

cols = [c[1] for c in mcur2.execute("PRAGMA table_info(story_event_story_data)").fetchall()]
event_09_all = set()
event_09_type1 = set()
for num in range(1, 20):
    type_col = f'story_type_{num}'
    sid_col = f'story_id_{num}'
    if type_col not in cols or sid_col not in cols:
        continue
    for r in mcur2.execute(f"SELECT story_id_{num} FROM story_event_story_data WHERE story_type_{num} != 0").fetchall():
        sid = r[0]
        if sid and 1e7 < sid < 1.6e9 and str(sid).zfill(9)[:2] == '09':
            event_09_all.add(int(sid))
    for r in mcur2.execute(f"SELECT story_id_{num} FROM story_event_story_data WHERE story_type_{num} = 1").fetchall():
        sid = r[0]
        if sid and 1e7 < sid < 1.6e9 and str(sid).zfill(9)[:2] == '09':
            event_09_type1.add(int(sid))

localized_09 = set()
for f in localized_base.rglob('storytimeline_*.json'):
    sid_str = f.stem.replace('storytimeline_', '')
    try:
        sid = int(sid_str)
        if str(sid).zfill(9)[:2] == '09':
            localized_09.add(sid)
    except ValueError:
        pass

print(f"Meta 09: {len(meta_09)}")
print(f"Event 09 (all types): {len(event_09_all)}")
print(f"Event 09 (type=1): {len(event_09_type1)}")
print(f"Localized 09: {len(localized_09)}")

type_diff = event_09_all - event_09_type1
print(f"\nEvent 09 non-type1: {len(type_diff)}")
if type_diff:
    for sid in sorted(type_diff)[:10]:
        print(f"  {sid}")

meta_not_event = meta_09 - event_09_all
print(f"\nMeta 09 NOT in event story data: {len(meta_not_event)}")
if meta_not_event:
    for sid in sorted(meta_not_event)[:10]:
        print(f"  {sid}")

event_type1_not_localized = event_09_type1 - localized_09
localized_not_event_type1 = localized_09 - event_09_type1
print(f"\nEvent type1 NOT in localized: {len(event_type1_not_localized)}")
if event_type1_not_localized:
    for sid in sorted(event_type1_not_localized)[:10]:
        print(f"  {sid}")
print(f"Localized NOT in event type1: {len(localized_not_event_type1)}")
if localized_not_event_type1:
    for sid in sorted(localized_not_event_type1):
        print(f"  {sid}")

meta_and_type1_match = meta_09 == event_09_type1
print(f"\nMeta 09 == Event type1 09: {meta_and_type1_match}")
if not meta_and_type1_match:
    print(f"  meta has but event_type1 doesn't: {sorted(meta_09 - event_09_type1)[:5]}")
    print(f"  event_type1 has but meta doesn't: {sorted(event_09_type1 - meta_09)[:5]}")

print(f"\n=== CONCLUSION ===")
print(f"  meta_09={len(meta_09)}, event_type1={len(event_09_type1)}, localized={len(localized_09)}")
if len(meta_09) == len(localized_09):
    print(f"  GAP=0: meta 09 == localized 09 ({len(meta_09)} files)")
else:
    gap = len(meta_09) - len(localized_09)
    print(f"  GAP={gap}: meta has {len(meta_09)} but localized only has {len(localized_09)}")
    print(f"  Missing {gap} files from localized_data")

meta.close()
master.close()
