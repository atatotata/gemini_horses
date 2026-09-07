"""
Resolve the 202 missing Story Event 09 sids.
- Meta DB has 457 prefix-09 storytimeline entries
- Localized has 255 prefix-09 files
- Missing = 202
- Verify each has dat file
"""
import json, os, sys, sqlite3
from pathlib import Path
from collections import Counter

sys.path.insert(0, r'G:\Games\steamapps\common\UmamusumePrettyDerby_Jpn\gemini_horses\tools\umamusu-utils\scripts')
from utils import _derive_decryption_key, DB_KEY, DB_BASE_KEY, dict_factory
import apsw

GAME_DIR = Path(r"G:/Games/steamapps/common/UmamusumePrettyDerby_Jpn")
DAT_DIR = GAME_DIR / "UmamusumePrettyDerby_Jpn_Data/Persistent/dat"
META_PATH = GAME_DIR / "UmamusumePrettyDerby_Jpn_Data/Persistent/meta"
GEMINI_DIR = GAME_DIR / "gemini_horses/localized_data/assets/story/data"
OUT_BASE = Path(r"C:/TMP/extra_fetch/story_json")

# 1. Meta 09 entries
conn = apsw.Connection(str(META_PATH))
conn.row_trace = dict_factory
final_key = _derive_decryption_key(DB_KEY, DB_BASE_KEY)
conn.pragma('cipher', 'chacha20')
conn.pragma('hexkey', final_key.hex())
c = conn.cursor()

meta_09 = {}
for row in c.execute("SELECT n, h, e FROM a WHERE n LIKE 'story/data/09/%storytimeline_%' AND n NOT LIKE '%resourcelist%'"):
    n = row['n']
    sid_str = n.split('_')[-1]
    try:
        meta_09[int(sid_str)] = row
    except ValueError:
        pass
conn.close()

# 2. Localized 09 sids
localized_09 = set()
for root, dirs, files in os.walk(GEMINI_DIR):
    for f in files:
        if f.startswith("storytimeline_") and f.endswith(".json"):
            rel = os.path.relpath(os.path.join(root, f), GEMINI_DIR)
            parts = rel.replace("\\", "/").split("/")
            if parts[0] == "09":
                sid = f.replace("storytimeline_", "").replace(".json", "")
                try:
                    localized_09.add(int(sid))
                except ValueError:
                    pass

# 3. Missing
missing_sids = sorted(set(meta_09.keys()) - localized_09)

# 4. Verify dat files
missing_with_dat = []
missing_no_dat = []
for sid in missing_sids:
    row = meta_09[sid]
    h = row['h']
    dat_path = DAT_DIR / h[:2] / h
    if dat_path.exists():
        missing_with_dat.append(sid)
    else:
        missing_no_dat.append(sid)

# 5. Build task list
tasks = []
for sid in missing_sids:
    row = meta_09[sid]
    n = row['n']
    h = row['h']
    e = row['e']
    parts = n.split('/')
    prefix = parts[2]  # "09"
    sub = parts[3]     # "0001", etc.
    out_json = OUT_BASE / prefix / sub / f"storytimeline_{sid}.json"
    tasks.append({
        'sid': sid,
        'n': n,
        'h': h,
        'e': e,
        'sub': sub,
        'out_json': str(out_json)
    })

# Output
result = {
    'meta_09_count': len(meta_09),
    'localized_09_count': len(localized_09),
    'missing_count': len(missing_sids),
    'missing_with_dat': len(missing_with_dat),
    'missing_no_dat': len(missing_no_dat),
    'missing_no_dat_list': missing_no_dat,
    'tasks': tasks,
}

with open(OUT_BASE / "resolve_09.json", "w", encoding="utf-8") as f:
    json.dump(result, f, indent=2)

print(f"Meta 09: {len(meta_09)}")
print(f"Localized 09: {len(localized_09)}")
print(f"Missing: {len(missing_sids)}")
print(f"With dat: {len(missing_with_dat)}")
print(f"No dat: {len(missing_no_dat)}")
if missing_no_dat:
    print(f"No dat sids: {missing_no_dat}")
sub_counter = Counter(t['sub'] for t in tasks)
print(f"Subfolder distribution:")
for sub, cnt in sorted(sub_counter.items()):
    print(f"  {sub}: {cnt}")
