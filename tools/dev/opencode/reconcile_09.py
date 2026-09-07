"""Reconcile: meta 09 = 457, story_event_story_data type=1 = 449, localized 09 = 255. Find the full picture."""
import sqlite3, os, sys, json
from pathlib import Path

sys.path.insert(0, r'G:\Games\steamapps\common\UmamusumePrettyDerby_Jpn\gemini_horses\tools\umamusu-utils\scripts')
from utils import _derive_decryption_key, DB_KEY, DB_BASE_KEY, dict_factory
import apsw

GAME_DIR = Path(r"G:/Games/steamapps/common/UmamusumePrettyDerby_Jpn")
META_PATH = GAME_DIR / "UmamusumePrettyDerby_Jpn_Data/Persistent/meta"
MASTER_PATH = GAME_DIR / "UmamusumePrettyDerby_Jpn_Data/Persistent/master/master.mdb"
GEMINI_DIR = GAME_DIR / "gemini_horses/localized_data/assets/story/data"
DAT_DIR = GAME_DIR / "UmamusumePrettyDerby_Jpn_Data/Persistent/dat"

# 1. Meta 09 sids
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

# 2. story_event_story_data sids (stored as 9000xxxx, map to 09000xxxx)
mconn = sqlite3.connect(str(MASTER_PATH))
mc = mconn.cursor()
mc.execute("SELECT DISTINCT story_id_1 FROM story_event_story_data WHERE story_type_1 = 1")
master_09 = set()
for row in mc.fetchall():
    sid = row[0]
    if 90001000 <= sid <= 90099999:
        # Map to meta format: prepend 0 -> 090001001
        full_sid = int(f"0{sid}")
        master_09.add(full_sid)
mconn.close()

# 3. Localized 09 sids
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

# 4. Analysis
meta_set = set(meta_09.keys())
print(f"Meta 09 sids: {len(meta_set)}")
print(f"Master story_event type=1 sids (09xxx): {len(master_09)}")
print(f"Localized 09 sids: {len(localized_09)}")

# Check which meta sids are in master and which are not
in_both = meta_set & master_09
meta_only = meta_set - master_09
master_only = master_09 - meta_set

print(f"\nIn both meta & master: {len(in_both)}")
print(f"In meta only (not in story_event): {len(meta_only)}")
if meta_only:
    print(f"  Meta-only sids: {sorted(meta_only)[:30]}")
print(f"In master only (not in meta): {len(master_only)}")
if master_only:
    print(f"  Master-only sids: {sorted(master_only)[:30]}")

# Missing from localized
missing_from_localized_meta = sorted(meta_set - localized_09)
missing_from_localized_master = sorted(master_09 - localized_09)
print(f"\nMissing from localized (meta - localized): {len(missing_from_localized_meta)}")
print(f"Missing from localized (master - localized): {len(missing_from_localized_master)}")

# Check dat files for master sids
master_no_dat = []
master_with_dat = []
for sid in sorted(master_09):
    if sid in meta_09:
        h = meta_09[sid]['h']
        dat_path = DAT_DIR / h[:2] / h
        if dat_path.exists():
            master_with_dat.append(sid)
        else:
            master_no_dat.append(sid)

print(f"\nMaster 09 sids with dat file: {len(master_with_dat)}")
print(f"Master 09 sids WITHOUT dat file: {len(master_no_dat)}")

# Overall: which sids have dat files out of ALL meta 09
meta_with_dat = [sid for sid in meta_set if (DAT_DIR / meta_09[sid]['h'][:2] / meta_09[sid]['h']).exists()]
print(f"\nALL meta 09 with dat: {len(meta_with_dat)}/{len(meta_set)}")
print(f"Meta 09 dat sids: {sorted(meta_with_dat)}")

# Which of the 202 missing from localized have dat files?
missing_202 = sorted(meta_set - localized_09)
missing_202_with_dat = [sid for sid in missing_202 if (DAT_DIR / meta_09[sid]['h'][:2] / meta_09[sid]['h']).exists()]
missing_202_no_dat = [sid for sid in missing_202 if not (DAT_DIR / meta_09[sid]['h'][:2] / meta_09[sid]['h']).exists()]
print(f"\n202 missing from localized: with dat={len(missing_202_with_dat)}, no dat={len(missing_202_no_dat)}")
print(f"With dat: {missing_202_with_dat}")

# Save full analysis
analysis = {
    'meta_09_count': len(meta_set),
    'master_type1_09_count': len(master_09),
    'localized_09_count': len(localized_09),
    'in_both_meta_master': len(in_both),
    'meta_only': sorted(meta_only),
    'master_only': sorted(master_only),
    'missing_202': missing_202,
    'missing_202_with_dat': missing_202_with_dat,
    'missing_202_no_dat': missing_202_no_dat,
    'meta_with_dat': sorted(meta_with_dat),
}

with open(r"C:\TMP\extra_fetch\story_json\analysis_09.json", "w", encoding="utf-8") as f:
    json.dump(analysis, f, indent=2)
print("\nSaved analysis to C:\\TMP\\extra_fetch\\story_json\\analysis_09.json")
