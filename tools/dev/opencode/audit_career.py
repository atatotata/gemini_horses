import os, sys, json, sqlite3
from pathlib import Path
from collections import Counter

GAME_DIR = Path(r"G:/Games/steamapps/common/UmamusumePrettyDerby_Jpn")
DAT_DIR = GAME_DIR / "UmamusumePrettyDerby_Jpn_Data/Persistent/dat"
META_PATH = GAME_DIR / "UmamusumePrettyDerby_Jpn_Data/Persistent/meta"
MASTER_PATH = GAME_DIR / "UmamusumePrettyDerby_Jpn_Data/Persistent/master/master.mdb"
GEMINI_DIR = GAME_DIR / "gemini_horses/localized_data/assets/story/data"
UPSTREAM_CACHE = GAME_DIR / "gemini_horses/.upstream_cache.json"

sys.path.insert(0, str(GAME_DIR / "gemini_horses/tools/umamusu-utils/scripts"))
from utils import _derive_decryption_key, DB_KEY, DB_BASE_KEY, dict_factory
import apsw

print("=== 1. MASTER.MDB SINGLE_MODE_STORY_DATA ===")
mconn = sqlite3.connect(str(MASTER_PATH))
mc = mconn.cursor()

mc.execute("SELECT gallery_flag, count(*), count(distinct story_id) FROM single_mode_story_data WHERE story_id != 0 GROUP BY gallery_flag")
flag_stats = mc.fetchall()
print("Flag Breakdown (gallery_flag, total_rows, distinct_sids):")
for f, cnt, dist in flag_stats:
    label = "Unknown"
    if f == 0: label = "General/Uncategorized"
    elif f == 1: label = "Horsegirls Career Events"
    elif f == 2: label = "Support Cards (already done)"
    elif f == 3: label = "Main Scenario"
    elif f == 4: label = "Special/Other"
    print(f"  Flag {f} ({label}): {cnt} rows, {dist} unique story IDs")

mc.execute("SELECT DISTINCT story_id FROM single_mode_story_data WHERE gallery_flag = 1 AND story_id != 0")
flag1_sids = set(r[0] for r in mc.fetchall())

mc.execute("SELECT DISTINCT story_id FROM single_mode_story_data WHERE gallery_flag = 3 AND story_id != 0")
flag3_sids = set(r[0] for r in mc.fetchall())

mc.execute("SELECT DISTINCT story_id FROM single_mode_story_data WHERE story_id != 0")
all_sids = set(r[0] for r in mc.fetchall())
mconn.close()

print(f"\nTotal unique single_mode_story_data IDs: {len(all_sids)}")
print(f"Horsegirls (Flag 1) unique IDs: {len(flag1_sids)}")
print(f"Main Scenario (Flag 3) unique IDs: {len(flag3_sids)}")

print("\n=== 2. LOCAL GEMINI_HORSES & UMATL STATUS ===")
local_files = {}
for root, dirs, files in os.walk(GEMINI_DIR):
    for f in files:
        if f.startswith('storytimeline_') and f.endswith('.json'):
            sid_str = f.replace('storytimeline_', '').replace('.json', '')
            if sid_str.isdigit():
                local_files[int(sid_str)] = os.path.relpath(os.path.join(root, f), GEMINI_DIR).replace('\\', '/')

print(f"Total existing story files in gemini_horses: {len(local_files)}")

# Upstream UmaTL index check
upstream_sids = set()
if UPSTREAM_CACHE.exists():
    with open(UPSTREAM_CACHE, 'r', encoding='utf-8') as cf:
        uc = json.load(cf)
    for p in uc:
        if 'storytimeline_' in p:
            fname = os.path.basename(p)
            sid_str = fname.replace('storytimeline_', '').replace('.json', '')
            if sid_str.isdigit():
                upstream_sids.add(int(sid_str))
print(f"Total story files in upstream UmaTL: {len(upstream_sids)}")

# Overlaps
umatl_overlap = all_sids.intersection(upstream_sids)
gemini_overlap = all_sids.intersection(local_files.keys())
print(f"Upstream UmaTL translates {len(umatl_overlap)} single_mode stories.")
print(f"gemini_horses currently translates {len(gemini_overlap)} single_mode stories.")

# Horsegirls Flag 1
f1_in_local = flag1_sids.intersection(local_files.keys())
f1_in_umatl = flag1_sids.intersection(upstream_sids)
f1_missing = flag1_sids - local_files.keys()
print(f"\nHorsegirls (Flag 1, total {len(flag1_sids)}):")
print(f"  Already in gemini_horses: {len(f1_in_local)}")
print(f"  Already in upstream UmaTL: {len(f1_in_umatl)}")
print(f"  Net missing (to translate): {len(f1_missing)}")

# Main Scenario Flag 3
f3_in_local = flag3_sids.intersection(local_files.keys())
f3_in_umatl = flag3_sids.intersection(upstream_sids)
f3_missing = flag3_sids - local_files.keys()
print(f"\nMain Scenario (Flag 3, total {len(flag3_sids)}):")
print(f"  Already in gemini_horses: {len(f3_in_local)}")
print(f"  Already in upstream UmaTL: {len(f3_in_umatl)}")
print(f"  Net missing (to translate): {len(f3_missing)}")

print("\n=== 3. META DB RESOLUTION & DAT AVAILABILITY ===")
conn = apsw.Connection(str(META_PATH))
conn.row_trace = dict_factory
final_key = _derive_decryption_key(DB_KEY, DB_BASE_KEY)
conn.pragma('cipher', 'chacha20')
conn.pragma('hexkey', final_key.hex())
c = conn.cursor()

c.execute("""
SELECT n, h, e FROM a
WHERE n >= 'story/data/' AND n < 'story/data0'
  AND n NOT LIKE '%resourcelist%'
""")
all_meta_stories = c.fetchall()
conn.close()

meta_by_sid = {}
for r in all_meta_stories:
    fname = r['n'].split('/')[-1]
    sid_str = fname.replace('storytimeline_', '')
    if sid_str.isdigit():
        meta_by_sid[int(sid_str)] = r

print(f"Total story timeline entries in meta: {len(meta_by_sid)}")

f1_meta_found = f1_missing.intersection(meta_by_sid.keys())
f1_meta_missing = f1_missing - meta_by_sid.keys()
print(f"Missing Horsegirls stories found in meta: {len(f1_meta_found)} / {len(f1_missing)}")
if f1_meta_missing:
    print(f"  Warning: {len(f1_meta_missing)} not in meta! Samples: {list(f1_meta_missing)[:5]}")

f3_meta_found = f3_missing.intersection(meta_by_sid.keys())
print(f"Missing Main Scenario stories found in meta: {len(f3_meta_found)} / {len(f3_missing)}")

# Check how many are in local dat/
dat_present = 0
dat_missing = 0
for sid in f1_meta_found:
    h = meta_by_sid[sid]['h']
    bundle = DAT_DIR / h[:2] / h
    if bundle.exists():
        dat_present += 1
    else:
        dat_missing += 1

print(f"Local Persistent/dat/ availability for missing Horsegirls stories:")
print(f"  Present in dat/: {dat_present} ({dat_present/len(f1_meta_found)*100:.1f}%)")
print(f"  Need CDN download: {dat_missing} ({dat_missing/len(f1_meta_found)*100:.1f}%)")

f3_dat_present = sum(1 for sid in f3_meta_found if (DAT_DIR / meta_by_sid[sid]['h'][:2] / meta_by_sid[sid]['h']).exists())
print(f"Local Persistent/dat/ availability for missing Main Scenario stories: {f3_dat_present} / {len(f3_meta_found)}")
