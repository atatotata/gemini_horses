"""Check dat paths for 09 missing entries."""
import json, os, sys
from pathlib import Path

sys.path.insert(0, r'G:\Games\steamapps\common\UmamusumePrettyDerby_Jpn\gemini_horses\tools\umamusu-utils\scripts')
from utils import _derive_decryption_key, DB_KEY, DB_BASE_KEY, dict_factory
import apsw

GAME_DIR = Path(r"G:/Games/steamapps/common/UmamusumePrettyDerby_Jpn")
DAT_DIR = GAME_DIR / "UmamusumePrettyDerby_Jpn_Data/Persistent/dat"
META_PATH = GAME_DIR / "UmamusumePrettyDerby_Jpn_Data/Persistent/meta"

with open(r"C:\TMP\extra_fetch\story_json\resolve_09.json", "r", encoding="utf-8") as f:
    data = json.load(f)

tasks = data['tasks']

# Check first 10 dat paths
for t in tasks[:10]:
    sid = t['sid']
    h = t['h']
    e = t['e']
    dat_path = DAT_DIR / h[:2] / h
    print(f"sid={sid}, h={h}, e={e}, dat_exists={dat_path.exists()}")

# Check missing ones more carefully
no_dat = []
with_dat = []
for t in tasks:
    dat_path = DAT_DIR / t['h'][:2] / t['h']
    if dat_path.exists():
        with_dat.append(t)
    else:
        no_dat.append(t)

print(f"\nWith dat: {len(with_dat)}, No dat: {len(no_dat)}")

if no_dat:
    # Check first no-dat to see if maybe the hash is different
    t = no_dat[0]
    sid = t['sid']
    h = t['h']
    print(f"\nSample no-dat sid={sid}:")
    print(f"  h={h}, h[:2]={h[:2]}")
    prefix_dir = DAT_DIR / h[:2]
    print(f"  dir {prefix_dir} exists: {prefix_dir.exists()}")
    if prefix_dir.exists():
        entries = list(prefix_dir.iterdir())[:5]
        for e in entries:
            print(f"    {e.name}")
    
    # Also check ALL meta entries for this sid
    conn = apsw.Connection(str(META_PATH))
    conn.row_trace = dict_factory
    final_key = _derive_decryption_key(DB_KEY, DB_BASE_KEY)
    conn.pragma('cipher', 'chacha20')
    conn.pragma('hexkey', final_key.hex())
    c = conn.cursor()
    
    print(f"\n  All meta entries for {sid}:")
    for row in c.execute(f"SELECT n, h, e FROM a WHERE n LIKE '%{sid}%'"):
        h2 = row['h']
        dat_path2 = DAT_DIR / h2[:2] / h2
        print(f"    n={row['n']}, h={h2}, dat_exists={dat_path2.exists()}")
    conn.close()
