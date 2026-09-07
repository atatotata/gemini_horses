import sqlite3
from pathlib import Path

MDB = Path(r"G:/Games/steamapps/common/UmamusumePrettyDerby_Jpn/UmamusumePrettyDerby_Jpn_Data/Persistent/master/master.mdb")
MSG_DICT = Path(r"G:/Games/steamapps/common/UmamusumePrettyDerby_Jpn/gemini_horses/localized_data/race_jikkyo_message_dict.json")

import json
with open(MSG_DICT, encoding="utf-8") as f:
    msg_dict = json.load(f)

conn = sqlite3.connect(f"file:{MDB}?mode=ro", uri=True)
c = conn.cursor()

# Check ID 109
c.execute('SELECT * FROM "race_jikkyo_message" WHERE "id" = 109')
row = c.fetchone()
print(f"ID 109 in master: {row}")

# Check all master IDs vs dict
c.execute('SELECT DISTINCT "id" FROM "race_jikkyo_message"')
master_ids = {str(r[0]) for r in c.fetchall()}
missing = master_ids - set(msg_dict.keys())
print(f"Master distinct IDs: {len(master_ids)}")
print(f"Dict keys: {len(msg_dict)}")
print(f"Missing: {len(missing)}")
if missing:
    print(f"Missing IDs: {sorted([int(x) for x in missing])}")

# Also check for near-gaps: IDs in master that don't have corresponding dict key
for check_id in [108, 109, 110]:
    c.execute('SELECT "id", "message" FROM "race_jikkyo_message" WHERE "id" = ?', (check_id,))
    row = c.fetchone()
    print(f"  master id={check_id}: {row}")

conn.close()
