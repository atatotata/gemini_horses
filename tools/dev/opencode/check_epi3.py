import sqlite3, json, glob
mdb=r"G:/Games/steamapps/common/UmamusumePrettyDerby_Jpn/UmamusumePrettyDerby_Jpn_Data/Persistent/master/master.mdb"
conn=sqlite3.connect(mdb)
conn.text_factory=bytes
def s(b): return b.decode('utf-8') if isinstance(b,bytes) else str(b)
rows=list(conn.execute('SELECT category,"index",text FROM text_data WHERE "index"=1141 ORDER BY category'))
print(f"text_data rows for 1141: {len(rows)}")
for cat,idx,txt in rows:
    t=s(txt)
    print(f" cat {cat:3}: {t[:140]!r}")

# live dicts
import pathlib
g=r"G:/Games/steamapps/common/UmamusumePrettyDerby_Jpn/gemini_horses/localized_data/text_data_dict.json"
h=r"G:/Games/steamapps/common/UmamusumePrettyDerby_Jpn/hachimi/localized_data_1/text_data_dict.json"
for p in [g,h]:
    j=json.load(open(p,encoding='utf-8'))
    print(f"\n{p.split('/')[-2]}: cat88 1141={'FOUND' if j.get('88',{}).get('1141') else 'MISSING'}, cat163 1141={'FOUND' if j.get('163',{}).get('1141') else 'MISSING'} -> {repr(j.get('163',{}).get('1141','')[:90])}")

# story presence
ids=[r[0] for r in conn.execute('SELECT story_id FROM chara_story_data WHERE chara_id=1141 ORDER BY episode_index')]
print(f"\nchara_story_data for 1141: {ids}")
all_ids=[r[0] for r in conn.execute('SELECT story_id FROM chara_story_data')]
present=set()
for pat in [r"G:/Games/steamapps/common/UmamusumePrettyDerby_Jpn/gemini_horses/localized_data/assets/story/data/**/storytimeline_*.json", r"G:/Games/steamapps/common/UmamusumePrettyDerby_Jpn/hachimi/localized_data_1/assets/story/data/**/storytimeline_*.json"]:
    import re
    for f in glob.glob(pat, recursive=True):
        m=re.search(r"storytimeline_(\d+)",f)
        if m: present.add(int(m.group(1)))
missing=[x for x in all_ids if x not in present]
print(f"chara_story_data total {len(all_ids)}, present {len(all_ids)-len(missing)}, missing {len(missing)}")
print(f"Epiphaneia missing: {[x for x in ids if x not in present]}")
print(f"missing sample: {missing[:10]}")
# CST
c=len(list(conn.execute('SELECT 1 FROM character_system_text WHERE character_id=1141')))
print(f"\ncharacter_system_text 1141: {c} rows in master.mdb")
j=json.load(open(r"G:/Games/steamapps/common/UmamusumePrettyDerby_Jpn/gemini_horses/localized_data/character_system_text_dict.json",encoding='utf-8'))
print(f" gemini CST 1141: {len(j.get('1141',{}))} voices")
j2=json.load(open(r"G:/Games/steamapps/common/UmamusumePrettyDerby_Jpn/hachimi/localized_data_1/character_system_text_dict.json",encoding='utf-8'))
print(f" hachimi CST 1141: {len(j2.get('1141',{}))} voices")
