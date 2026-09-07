import sqlite3
import json
from pathlib import Path

MDB = Path(r"G:/Games/steamapps/common/UmamusumePrettyDerby_Jpn/UmamusumePrettyDerby_Jpn_Data/Persistent/master/master.mdb")
MSG_DICT = Path(r"G:/Games/steamapps/common/UmamusumePrettyDerby_Jpn/gemini_horses/localized_data/race_jikkyo_message_dict.json")
CMT_DICT = Path(r"G:/Games/steamapps/common/UmamusumePrettyDerby_Jpn/gemini_horses/localized_data/race_jikkyo_comment_dict.json")

conn = sqlite3.connect(f"file:{MDB}?mode=ro", uri=True)
c = conn.cursor()

# ---- race_jikkyo_message ----
c.execute('PRAGMA table_info("race_jikkyo_message")')
print("race_jikkyo_message cols:", [(col[1], col[2]) for col in c.fetchall()])
c.execute('SELECT COUNT(*) FROM "race_jikkyo_message"')
print("  total rows:", c.fetchone()[0])
c.execute('SELECT * FROM "race_jikkyo_message" LIMIT 5')
for r in c.fetchall():
    print("  sample:", r)

c.execute('SELECT DISTINCT "id" FROM "race_jikkyo_message"')
master_msg_ids = set()
for (id_val,) in c.fetchall():
    master_msg_ids.add(str(id_val))
print(f"\n  master message distinct ids: {len(master_msg_ids)}")

# ---- race_jikkyo_comment ----
c.execute('PRAGMA table_info("race_jikkyo_comment")')
print("\nrace_jikkyo_comment cols:", [(col[1], col[2]) for col in c.fetchall()])
c.execute('SELECT COUNT(*) FROM "race_jikkyo_comment"')
print("  total rows:", c.fetchone()[0])
c.execute('SELECT * FROM "race_jikkyo_comment" LIMIT 5')
for r in c.fetchall():
    print("  sample:", r)

c.execute('SELECT DISTINCT "id" FROM "race_jikkyo_comment"')
master_cmt_ids = set()
for (id_val,) in c.fetchall():
    master_cmt_ids.add(str(id_val))
print(f"\n  master comment distinct ids: {len(master_cmt_ids)}")

conn.close()

# Load local dicts
with open(MSG_DICT, encoding='utf-8') as f:
    msg_dict = json.load(f)
with open(CMT_DICT, encoding='utf-8') as f:
    cmt_dict = json.load(f)

local_msg_keys = set(msg_dict.keys())
local_cmt_keys = set(cmt_dict.keys())

missing_msg = master_msg_ids - local_msg_keys
missing_cmt = master_cmt_ids - local_cmt_keys

print(f"\n=== GAP ANALYSIS ===")
print(f"message: master={len(master_msg_ids)}, local={len(local_msg_keys)}, missing={len(missing_msg)}")
print(f"comment: master={len(master_cmt_ids)}, local={len(local_cmt_keys)}, missing={len(missing_cmt)}")

# Get the full rows for missing ids - we need the text columns
conn2 = sqlite3.connect(f"file:{MDB}?mode=ro", uri=True)
c2 = conn2.cursor()

print(f"\n=== MISSING MESSAGE SAMPLES ===")
missing_msg_list = sorted([int(x) for x in missing_msg])
for mid in missing_msg_list[:5]:
    c2.execute(f'SELECT * FROM "race_jikkyo_message" WHERE "id" = ?', (mid,))
    row = c2.fetchone()
    print(f"  id={mid}: {row}")

print(f"\n=== MISSING COMMENT SAMPLES ===")
missing_cmt_list = sorted([int(x) for x in missing_cmt])
for mid in missing_cmt_list[:5]:
    c2.execute(f'SELECT * FROM "race_jikkyo_comment" WHERE "id" = ?', (mid,))
    row = c2.fetchone()
    print(f"  id={mid}: {row}")

conn2.close()

# Save missing ids and their JP text for translation
conn3 = sqlite3.connect(f"file:{MDB}?mode=ro", uri=True)
c3 = conn3.cursor()

# Fetch all missing message rows
missing_msg_data = {}
for mid in missing_msg_list:
    c3.execute('SELECT * FROM "race_jikkyo_message" WHERE "id" = ?', (mid,))
    row = c3.fetchone()
    if row:
        # We need to know column names
        c3.execute('PRAGMA table_info("race_jikkyo_message")')
        cols = [col[1] for col in c3.fetchall()]
        row_dict = dict(zip(cols, row))
        missing_msg_data[str(mid)] = row_dict

# Fetch all missing comment rows
missing_cmt_data = {}
for mid in missing_cmt_list:
    c3.execute('SELECT * FROM "race_jikkyo_comment" WHERE "id" = ?', (mid,))
    row = c3.fetchone()
    if row:
        c3.execute('PRAGMA table_info("race_jikkyo_comment")')
        cols = [col[1] for col in c3.fetchall()]
        row_dict = dict(zip(cols, row))
        missing_cmt_data[str(mid)] = row_dict

conn3.close()

# Save to temp file for translation
output = {
    "message": missing_msg_data,
    "comment": missing_cmt_data,
    "missing_msg_count": len(missing_msg_data),
    "missing_cmt_count": len(missing_cmt_data)
}
out_path = Path(r"C:/TMP/race_jikkyo/missing_data.json")
with open(out_path, 'w', encoding='utf-8', newline='\n') as f:
    json.dump(output, f, ensure_ascii=False, indent=2)
print(f"\nSaved missing data to {out_path}")
print(f"message rows to translate: {len(missing_msg_data)}")
print(f"comment rows to translate: {len(missing_cmt_data)}")
print(f"Total: {len(missing_msg_data) + len(missing_cmt_data)}")
