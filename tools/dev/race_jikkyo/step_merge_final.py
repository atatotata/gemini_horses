import json
import sqlite3
import hashlib
import os
from pathlib import Path

MDB = Path(r"G:/Games/steamapps/common/UmamusumePrettyDerby_Jpn/UmamusumePrettyDerby_Jpn_Data/Persistent/master/master.mdb")
MSG_DICT_GEMINI = Path(r"G:/Games/steamapps/common/UmamusumePrettyDerby_Jpn/gemini_horses/localized_data/race_jikkyo_message_dict.json")
CMT_DICT_GEMINI = Path(r"G:/Games/steamapps/common/UmamusumePrettyDerby_Jpn/gemini_horses/localized_data/race_jikkyo_comment_dict.json")
MSG_DICT_HACHIMI = Path(r"G:/Games/steamapps/common/UmamusumePrettyDerby_Jpn/hachimi/localized_data_1/race_jikkyo_message_dict.json")
CMT_DICT_HACHIMI = Path(r"G:/Games/steamapps/common/UmamusumePrettyDerby_Jpn/hachimi/localized_data_1/race_jikkyo_comment_dict.json")
CHECKPOINT = Path(r"C:/TMP/race_jikkyo/race_checkpoint.json")

# Load all
with open(MSG_DICT_GEMINI, encoding="utf-8") as f:
    msg_dict = json.load(f)
with open(CMT_DICT_GEMINI, encoding="utf-8") as f:
    cmt_dict = json.load(f)
with open(CHECKPOINT, encoding="utf-8") as f:
    checkpoint = json.load(f)

print(f"Current msg_dict: {len(msg_dict)} keys")
print(f"Current cmt_dict: {len(cmt_dict)} keys")
print(f"Checkpoint: {len(checkpoint)} entries")

conn = sqlite3.connect(f"file:{MDB}?mode=ro", uri=True)
c = conn.cursor()

# Find remaining missing msg IDs
c.execute('SELECT DISTINCT "id" FROM "race_jikkyo_message"')
master_msg_ids = {str(r[0]) for r in c.fetchall()}
missing_msg_ids = sorted(master_msg_ids - set(msg_dict.keys()), key=int)
print(f"Missing msg IDs: {len(missing_msg_ids)}")

# For each missing ID, get JP text and look up EN in checkpoint
for mid in missing_msg_ids:
    c.execute('SELECT "message" FROM "race_jikkyo_message" WHERE "id" = ?', (int(mid),))
    row = c.fetchone()
    if row:
        jp = row[0].replace("\\n", "\n")
        en = checkpoint.get(jp)
        if en:
            en_clean = en.replace("\r\n", "\n").replace("\r", "\n").strip()
            msg_dict[mid] = en_clean
            print(f"  Added msg[{mid}]: {en_clean[:80]}")
        else:
            print(f"  WARNING: msg[{mid}] JP not in checkpoint: {jp[:80]}")

# Verify no more missing
c.execute('SELECT DISTINCT "id" FROM "race_jikkyo_message"')
master_msg_ids2 = {str(r[0]) for r in c.fetchall()}
still_missing = master_msg_ids2 - set(msg_dict.keys())
print(f"\nAfter fix - missing msg IDs: {len(still_missing)}")

# Verify cmt complete
c.execute('SELECT DISTINCT "id" FROM "race_jikkyo_comment"')
master_cmt_ids = {str(r[0]) for r in c.fetchall()}
missing_cmt = master_cmt_ids - set(cmt_dict.keys())
print(f"Missing cmt IDs: {len(missing_cmt)}")

conn.close()

# Write to both repos
def write_dict(path, data):
    tmp = str(path) + ".tmp"
    with open(tmp, "w", encoding="utf-8", newline="\n") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)
    os.replace(tmp, str(path))

write_dict(MSG_DICT_GEMINI, msg_dict)
write_dict(MSG_DICT_HACHIMI, msg_dict)
write_dict(CMT_DICT_GEMINI, cmt_dict)
write_dict(CMT_DICT_HACHIMI, cmt_dict)

print(f"\nFinal msg_dict: {len(msg_dict)} keys")
print(f"Final cmt_dict: {len(cmt_dict)} keys")

# Verify identical
def file_hash(p):
    with open(p, "rb") as f:
        return hashlib.md5(f.read()).hexdigest()

for name, gp, hp in [
    ("race_jikkyo_message_dict.json", MSG_DICT_GEMINI, MSG_DICT_HACHIMI),
    ("race_jikkyo_comment_dict.json", CMT_DICT_GEMINI, CMT_DICT_HACHIMI)
]:
    gh = file_hash(gp)
    hh = file_hash(hp)
    print(f"{name}: gemini={gh}, hachimi={hh}, identical={gh==hh}")

# Sample EN lines 25-36
print("\n=== SAMPLE EN LINES (msg 25-36, Feb Stakes fanfare) ===")
for sid in ["25", "26", "27", "28", "29", "30", "31", "32", "33", "34", "35", "36"]:
    if sid in msg_dict:
        print(f"  msg[{sid}]: {msg_dict[sid]}")
    else:
        print(f"  msg[{sid}]: MISSING")

# Show last 10 cmt entries
print("\n=== SAMPLE CMT EN LINES (last 10) ===")
cmt_keys = sorted([int(k) for k in cmt_dict.keys()])
for k in cmt_keys[-10:]:
    print(f"  cmt[{k}]: {cmt_dict[str(k)][:100]}")
