import sqlite3, json, os

DB = r'G:\Games\steamapps\common\UmamusumePrettyDerby_Jpn\UmamusumePrettyDerby_Jpn_Data\Persistent\master\master.mdb'
DICT = r'G:\Games\steamapps\common\UmamusumePrettyDerby_Jpn\gemini_horses\localized_data\text_data_dict.json'

con = sqlite3.connect(DB)
cur = con.cursor()

# user table count
n = cur.execute("SELECT COUNT(*) FROM sqlite_master WHERE type='table' AND name NOT LIKE 'sqlite_%'").fetchone()[0]
print('USER TABLE COUNT:', n)

tables = ['text_data','character_system_text','race_jikkyo_message','race_jikkyo_comment',
          'single_mode_story_data','chara_story_data','main_story_data',
          'story_event_story_data','story_extra_story_data']
for t in tables:
    row = cur.execute('SELECT sql FROM sqlite_master WHERE type="table" AND name=?', (t,)).fetchone()
    if row:
        print('---', t, '---')
        print(row[0])
    else:
        print('---', t, '--- NOT PRESENT')

con.close()

print('=== DICT ===')
print('size:', os.path.getsize(DICT))
with open(DICT, 'r', encoding='utf-8') as f:
    head = f.read(1500)
print(head[:1500])
