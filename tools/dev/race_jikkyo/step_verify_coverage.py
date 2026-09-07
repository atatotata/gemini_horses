import json
import sqlite3
from pathlib import Path

MDB = Path(r"G:/Games/steamapps/common/UmamusumePrettyDerby_Jpn/UmamusumePrettyDerby_Jpn_Data/Persistent/master/master.mdb")
MSG_DICT = Path(r"G:/Games/steamapps/common/UmamusumePrettyDerby_Jpn/gemini_horses/localized_data/race_jikkyo_message_dict.json")
CMT_DICT = Path(r"G:/Games/steamapps/common/UmamusumePrettyDerby_Jpn/gemini_horses/localized_data/race_jikkyo_comment_dict.json")
CHECKPOINT = Path(r"C:/TMP/race_jikkyo/race_checkpoint.json")

with open(MSG_DICT, encoding="utf-8") as f:
    msg_dict = json.load(f)
with open(CMT_DICT, encoding="utf-8") as f:
    cmt_dict = json.load(f)
with open(CHECKPOINT, encoding="utf-8") as f:
    checkpoint = json.load(f)

conn = sqlite3.connect(f"file:{MDB}?mode=ro", uri=True)
c = conn.cursor()

# Get ALL missing IDs
c.execute('SELECT DISTINCT "id" FROM "race_jikkyo_message"')
master_msg_ids = {str(r[0]) for r in c.fetchall()}
missing_msg_ids = sorted(master_msg_ids - set(msg_dict.keys()), key=int)

c.execute('SELECT DISTINCT "id" FROM "race_jikkyo_comment"')
master_cmt_ids = {str(r[0]) for r in c.fetchall()}
missing_cmt_ids = sorted(master_cmt_ids - set(cmt_dict.keys()), key=int)

# Collect JP texts for missing IDs
msg_jp_texts = set()
for mid in missing_msg_ids:
    c.execute('SELECT "message" FROM "race_jikkyo_message" WHERE "id" = ?', (int(mid),))
    row = c.fetchone()
    if row:
        msg_jp_texts.add(row[0].replace("\\n", "\n"))

cmt_jp_texts = set()
for mid in missing_cmt_ids:
    c.execute('SELECT "message" FROM "race_jikkyo_comment" WHERE "id" = ?', (int(mid),))
    row = c.fetchone()
    if row:
        cmt_jp_texts.add(row[0].replace("\\n", "\n"))

conn.close()

print(f"Missing msg IDs: {len(missing_msg_ids)}, unique JP texts: {len(msg_jp_texts)}")
print(f"Missing cmt IDs: {len(missing_cmt_ids)}, unique JP texts: {len(cmt_jp_texts)}")
print(f"Total missing IDs: {len(missing_msg_ids) + len(missing_cmt_ids)}")
print(f"Total unique JP texts: {len(msg_jp_texts) + len(cmt_jp_texts)}")

# Check coverage
covered_msg = msg_jp_texts & set(checkpoint.keys())
covered_cmt = cmt_jp_texts & set(checkpoint.keys())
uncovered_msg = msg_jp_texts - set(checkpoint.keys())
uncovered_cmt = cmt_jp_texts - set(checkpoint.keys())

print(f"\nMsg JP covered by checkpoint: {len(covered_msg)}/{len(msg_jp_texts)}")
print(f"Cmt JP covered by checkpoint: {len(covered_cmt)}/{len(cmt_jp_texts)}")
print(f"Msg still uncovered: {len(uncovered_msg)}")
print(f"Cmt still uncovered: {len(uncovered_cmt)}")

if uncovered_msg:
    print("\nSample uncovered msg JP:")
    for jp in list(uncovered_msg)[:5]:
        print(f"  {jp[:80]}")

# Show some checkpoint entries to verify
print(f"\nCheckpoint sample entries:")
for i, (k, v) in enumerate(checkpoint.items()):
    if i >= 5:
        break
    print(f"  '{k[:60]}' -> '{v[:60]}'")
