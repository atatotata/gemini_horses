import sqlite3, json, glob, os

conn = sqlite3.connect(r"G:\Games\steamapps\common\UmamusumePrettyDerby_Jpn\UmamusumePrettyDerby_Jpn_Data\Persistent\master\master.mdb")
c = conn.cursor()

c.execute("SELECT story_id, support_card_id, support_chara_id FROM single_mode_story_data WHERE gallery_flag = 2")
rows = c.fetchall()
print(f"Total support card events in single_mode_story_data (gallery_flag=2): {len(rows)}")

existing_files = set()
for f in glob.glob(r"G:\Games\steamapps\common\UmamusumePrettyDerby_Jpn\gemini_horses\localized_data\assets\story\data\**\storytimeline_*.json", recursive=True):
    bn = os.path.basename(f)
    sid = bn.replace("storytimeline_", "").replace(".json", "")
    existing_files.add(int(sid))

missing_supp = []
present_supp = []
for sid, sc_id, ch_id in rows:
    if sid in existing_files:
        present_supp.append((sid, sc_id, ch_id))
    else:
        missing_supp.append((sid, sc_id, ch_id))

print(f"Already present: {len(present_supp)}")
print(f"Missing: {len(missing_supp)}")
for sid, sc_id, ch_id in missing_supp[:10]:
    print(f"  Missing: story_id={sid}, support_card_id={sc_id}, support_chara_id={ch_id}")
