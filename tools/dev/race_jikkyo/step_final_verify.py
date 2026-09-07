import json
import sqlite3
import hashlib
from pathlib import Path

MDB = Path(r"G:/Games/steamapps/common/UmamusumePrettyDerby_Jpn/UmamusumePrettyDerby_Jpn_Data/Persistent/master/master.mdb")
MSG_GEMINI = Path(r"G:/Games/steamapps/common/UmamusumePrettyDerby_Jpn/gemini_horses/localized_data/race_jikkyo_message_dict.json")
CMT_GEMINI = Path(r"G:/Games/steamapps/common/UmamusumePrettyDerby_Jpn/gemini_horses/localized_data/race_jikkyo_comment_dict.json")
MSG_HACHIMI = Path(r"G:/Games/steamapps/common/UmamusumePrettyDerby_Jpn/hachimi/localized_data_1/race_jikkyo_message_dict.json")
CMT_HACHIMI = Path(r"G:/Games/steamapps/common/UmamusumePrettyDerby_Jpn/hachimi/localized_data_1/race_jikkyo_comment_dict.json")
CHECKPOINT = Path(r"C:/TMP/race_jikkyo/race_checkpoint.json")

# Load everything
with open(MSG_GEMINI, encoding="utf-8") as f:
    msg_dict = json.load(f)
with open(CMT_GEMINI, encoding="utf-8") as f:
    cmt_dict = json.load(f)
with open(CHECKPOINT, encoding="utf-8") as f:
    checkpoint = json.load(f)

conn = sqlite3.connect(f"file:{MDB}?mode=ro", uri=True)
c = conn.cursor()

c.execute('SELECT COUNT(DISTINCT "id") FROM "race_jikkyo_message"')
master_msg_count = c.fetchone()[0]
c.execute('SELECT DISTINCT "id" FROM "race_jikkyo_message"')
master_msg_ids = {str(r[0]) for r in c.fetchall()}

c.execute('SELECT COUNT(DISTINCT "id") FROM "race_jikkyo_comment"')
master_cmt_count = c.fetchone()[0]
c.execute('SELECT DISTINCT "id" FROM "race_jikkyo_comment"')
master_cmt_ids = {str(r[0]) for r in c.fetchall()}

conn.close()

lines = []
lines.append("=" * 60)
lines.append("FINAL VERIFICATION REPORT")
lines.append("=" * 60)

missing_msg = master_msg_ids - set(msg_dict.keys())
missing_cmt = master_cmt_ids - set(cmt_dict.keys())

lines.append("")
lines.append("1. COVERAGE")
lines.append(f"   race_jikkyo_message: master={master_msg_count}, dict={len(msg_dict)}, missing={len(missing_msg)}")
lines.append(f"   race_jikkyo_comment: master={master_cmt_count}, dict={len(cmt_dict)}, missing={len(missing_cmt)}")
lines.append(f"   GAP FILLED: msg {1080 - len(missing_msg)}/1080, cmt {120 - len(missing_cmt)}/120")
lines.append(f"   Total merged: {1080 - len(missing_msg) + 120 - len(missing_cmt)}/1200")

lines.append("")
lines.append("2. CHECKPOINT")
lines.append(f"   Entries: {len(checkpoint)}")

def file_hash(p):
    with open(p, "rb") as f:
        return hashlib.md5(f.read()).hexdigest()

lines.append("")
lines.append("3. REPO IDENTITY")
for name, gp, hp in [
    ("race_jikkyo_message_dict.json", MSG_GEMINI, MSG_HACHIMI),
    ("race_jikkyo_comment_dict.json", CMT_GEMINI, CMT_HACHIMI)
]:
    gh = file_hash(gp)
    hh = file_hash(hp)
    lines.append(f"   {name}: gemini={gh}, hachimi={hh}, identical={gh==hh}")

lines.append("")
lines.append("4. SAMPLE EN LINES (msg 25-36, Feb Stakes fanfare)")
for sid in ["25", "26", "27", "28", "29", "30", "31", "32", "33", "34", "35", "36"]:
    val = msg_dict.get(sid, "MISSING")
    lines.append(f"   msg[{sid}]: {val}")

lines.append("")
lines.append("5. SAMPLE NEW CMT EN LINES")
for k in [3050, 3063, 3064, 3068, 3070]:
    sk = str(k)
    val = cmt_dict.get(sk, "MISSING")
    lines.append(f"   cmt[{k}]: {val[:150]}")

lines.append("")
lines.append("6. MORE ADDED MSG SAMPLES (ids 100-110)")
for sid in ["100", "101", "102", "103", "104", "105", "106", "107", "108", "109", "110"]:
    val = msg_dict.get(sid, "MISSING")
    lines.append(f"   msg[{sid}]: {val[:120]}")

output = "\n".join(lines)
with open(r"C:/TMP/race_jikkyo/final_report.txt", "w", encoding="utf-8") as f:
    f.write(output)
print(f"Report written. Lines: {len(lines)}")
