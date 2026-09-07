"""Investigate: why only 4/202 dat files exist. Check the 4, check if data already in localized JSON."""
import json, os, sys
from pathlib import Path

with open(r"C:\TMP\extra_fetch\story_json\resolve_09.json", "r", encoding="utf-8") as f:
    data = json.load(f)

tasks = data['tasks']
GAME_DIR = Path(r"G:/Games/steamapps/common/UmamusumePrettyDerby_Jpn")
DAT_DIR = GAME_DIR / "UmamusumePrettyDerby_Jpn_Data/Persistent/dat"

# Show the 4 that exist
with_dat = [t for t in tasks if (DAT_DIR / t['h'][:2] / t['h']).exists()]
print(f"=== {len(with_dat)} bundles exist locally ===")
for t in with_dat:
    dat_path = DAT_DIR / t['h'][:2] / t['h']
    sz = dat_path.stat().st_size
    print(f"  sid={t['sid']}, h={t['h']}, size={sz}, out={t['out_json']}")

# Check ALL 09 meta entries to see what % have dat files
print("\n=== Checking ALL 457 meta 09 entries for dat existence ===")
all_09_tasks = []
for t in tasks:
    all_09_tasks.append(t)

# Actually let's check the other way - check localized files that already exist
GEMINI_DIR = GAME_DIR / "gemini_horses/localized_data/assets/story/data"
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

# Check if the localized files have actual content or are empty
sample_localized = sorted(localized_09)[:5]
for sid in sample_localized:
    # Find the file
    sid_str = str(sid)
    prefix = sid_str[:2]  # "09"
    sub = sid_str[2:6]
    fname = f"storytimeline_{sid}.json"
    fpath = GEMINI_DIR / prefix / sub / fname
    if fpath.exists():
        sz = fpath.stat().st_size
        print(f"  Localized {sid}: {fpath}, size={sz}")

# Check if there's another dat directory or download path
print("\n=== Check dat dir contents for 09 hash prefix samples ===")
from collections import Counter
hash_prefixes = Counter()
for t in tasks:
    hash_prefixes[t['h'][:2]] += 1
print(f"Hash prefix distribution: {dict(hash_prefixes)}")

# Count how many 09 entries (ALL) have dat files
sys.path.insert(0, r'G:\Games\steamapps\common\UmamusumePrettyDerby_Jpn\gemini_horses\tools\umamusu-utils\scripts')
from utils import _derive_decryption_key, DB_KEY, DB_BASE_KEY, dict_factory
import apsw

META_PATH = GAME_DIR / "UmamusumePrettyDerby_Jpn_Data/Persistent/meta"
conn = apsw.Connection(str(META_PATH))
conn.row_trace = dict_factory
final_key = _derive_decryption_key(DB_KEY, DB_BASE_KEY)
conn.pragma('cipher', 'chacha20')
conn.pragma('hexkey', final_key.hex())
c = conn.cursor()

total_09 = 0
has_dat = 0
for row in c.execute("SELECT n, h FROM a WHERE n LIKE 'story/data/09/%storytimeline_%' AND n NOT LIKE '%resourcelist%'"):
    total_09 += 1
    if (DAT_DIR / row['h'][:2] / row['h']).exists():
        has_dat += 1
conn.close()

print(f"\n=== ALL 457 meta 09 entries ===")
print(f"Has dat file: {has_dat}/{total_09}")
print(f"Missing dat: {total_09 - has_dat}")
