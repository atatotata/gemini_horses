import json
import sqlite3
from pathlib import Path

MDB = Path(r"G:/Games/steamapps/common/UmamusumePrettyDerby_Jpn/UmamusumePrettyDerby_Jpn_Data/Persistent/master/master.mdb")
MSG_DICT = Path(r"G:/Games/steamapps/common/UmamusumePrettyDerby_Jpn/gemini_horses/localized_data/race_jikkyo_message_dict.json")
CHECKPOINT = Path(r"C:/TMP/race_jikkyo/race_checkpoint.json")

with open(MSG_DICT, encoding="utf-8") as f:
    msg_dict = json.load(f)
with open(CHECKPOINT, encoding="utf-8") as f:
    checkpoint = json.load(f)

conn = sqlite3.connect(f"file:{MDB}?mode=ro", uri=True)
c = conn.cursor()

c.execute('SELECT DISTINCT "id" FROM "race_jikkyo_message"')
master_msg_ids = {str(r[0]) for r in c.fetchall()}
missing_msg_ids = sorted(master_msg_ids - set(msg_dict.keys()), key=int)

out_lines = []
for mid in missing_msg_ids:
    c.execute('SELECT "message" FROM "race_jikkyo_message" WHERE "id" = ?', (int(mid),))
    row = c.fetchone()
    if row:
        jp_raw = row[0]
        jp_normalized = jp_raw.replace("\\n", "\n")
        out_lines.append(f"ID {mid}:")
        out_lines.append(f"  raw repr: {repr(jp_raw)}")
        out_lines.append(f"  normalized repr: {repr(jp_normalized)}")
        out_lines.append(f"  in checkpoint: {jp_normalized in checkpoint}")
        # Also check if raw version is in checkpoint
        out_lines.append(f"  raw in checkpoint: {jp_raw in checkpoint}")
        
        # Show matching checkpoint entries
        for ck, cv in checkpoint.items():
            if jp_normalized[:30] in ck or ck[:30] in jp_normalized:
                out_lines.append(f"  FOUND MATCH: '{ck[:60]}' -> '{cv[:60]}'")
                break
        else:
            # Try fuzzy: check if any checkpoint key starts with same chars
            jp_first20 = jp_normalized[:20]
            for ck in checkpoint:
                if ck[:20] == jp_first20:
                    out_lines.append(f"  FUZZY MATCH: '{ck[:60]}'")
                    break
            else:
                out_lines.append(f"  NO MATCH FOUND for first 20 chars: {repr(jp_first20)}")
    out_lines.append("")

conn.close()

with open(r"C:/TMP/race_jikkyo/debug_missing.txt", "w", encoding="utf-8") as f:
    f.write("\n".join(out_lines))

print("Debug written to debug_missing.txt")
print(f"Missing IDs: {missing_msg_ids}")
