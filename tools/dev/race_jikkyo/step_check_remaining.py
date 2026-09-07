import json

# Load checkpoint
checkpoint = json.load(open(r"C:/TMP/race_jikkyo/race_checkpoint.json", "r", encoding="utf-8"))
print(f"Checkpoint has {len(checkpoint)} entries")

# Load missing data
import sqlite3
from pathlib import Path

MDB = Path(r"G:/Games/steamapps/common/UmamusumePrettyDerby_Jpn/UmamusumePrettyDerby_Jpn_Data/Persistent/master/master.mdb")
MSG_DICT = Path(r"G:/Games/steamapps/common/UmamusumePrettyDerby_Jpn/gemini_horses/localized_data/race_jikkyo_message_dict.json")

with open(MSG_DICT, encoding="utf-8") as f:
    msg_dict = json.load(f)

conn = sqlite3.connect(f"file:{MDB}?mode=ro", uri=True)
c = conn.cursor()

c.execute('SELECT DISTINCT "id" FROM "race_jikkyo_message"')
master_msg_ids = {str(r[0]) for r in c.fetchall()}
missing_msg_ids = master_msg_ids - set(msg_dict.keys())

c.execute('SELECT DISTINCT "id" FROM "race_jikkyo_comment"')
cmt_dict = json.load(open(r"G:/Games/steamapps/common/UmamusumePrettyDerby_Jpn/gemini_horses/localized_data/race_jikkyo_comment_dict.json", encoding="utf-8"))
master_cmt_ids = {str(r[0]) for r in c.fetchall()}
missing_cmt_ids = master_cmt_ids - set(cmt_dict.keys())

still_missing_msg = []
for mid in sorted(missing_msg_ids, key=int):
    c.execute('SELECT "message" FROM "race_jikkyo_message" WHERE "id" = ?', (int(mid),))
    row = c.fetchone()
    if row:
        jp = row[0].replace("\\n", "\n")
        if jp not in checkpoint:
            still_missing_msg.append((int(mid), jp))

still_missing_cmt = []
for mid in sorted(missing_cmt_ids, key=int):
    c.execute('SELECT "message" FROM "race_jikkyo_comment" WHERE "id" = ?', (int(mid),))
    row = c.fetchone()
    if row:
        jp = row[0].replace("\\n", "\n")
        if jp not in checkpoint:
            still_missing_cmt.append((int(mid), jp))

conn.close()

print(f"Still missing msg: {len(still_missing_msg)}")
print(f"Still missing cmt: {len(still_missing_cmt)}")
print(f"Total still needed: {len(still_missing_msg) + len(still_missing_cmt)}")

if still_missing_msg:
    print("\nSample missing msg JP:")
    for idx, jp in still_missing_msg[:5]:
        print(f"  id={idx}: {jp[:80]}")
if still_missing_cmt:
    print("\nSample missing cmt JP:")
    for idx, jp in still_missing_cmt[:5]:
        print(f"  id={idx}: {jp[:80]}")
