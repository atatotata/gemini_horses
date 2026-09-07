import sqlite3, json, pathlib, glob
mdb=r"G:/Games/steamapps/common/UmamusumePrettyDerby_Jpn/UmamusumePrettyDerby_Jpn_Data/Persistent/master/master.mdb"
conn=sqlite3.connect(mdb)
conn.row_factory=sqlite3.Row
def q(sql,p=()):
    return list(conn.execute(sql,p))

print("=== text_data for id 1141 ===")
for r in q('SELECT category, "index", substr(text,1,120) as t FROM text_data WHERE "index"=1141 ORDER BY category'):
    print(f" cat {r['category']:>3}: {r['t']!r}")

print("\n=== chara_data 1141 ===")
try:
    rows=q('SELECT * FROM chara_data WHERE id=1141')
    for r in rows: print(dict(r))
except Exception as e: print(e)

print("\n=== character_system_text for 1141 ===")
rows=q('SELECT voice_id, substr(text,1,80) as t FROM character_system_text WHERE character_id=1141 ORDER BY voice_id LIMIT 20')
print(f" rows: {len(q('SELECT 1 FROM character_system_text WHERE character_id=1141'))}")
for r in rows: print(r['voice_id'], repr(r['t']))

print("\n=== chara_story_data 1141 ===")
for r in q('SELECT * FROM chara_story_data WHERE chara_id=1141 ORDER BY episode_index'):
    print(dict(r))

print("\n=== live patch checks ===")
import os
td_path=r"G:/Games/steamapps/common/UmamusumePrettyDerby_Jpn/gemini_horses/localized_data/text_data_dict.json"
cst_path=r"G:/Games/steamapps/common/UmamusumePrettyDerby_Jpn/gemini_horses/localized_data/character_system_text_dict.json"
h_td_path=r"G:/Games/steamapps/common/UmamusumePrettyDerby_Jpn/hachimi/localized_data_1/text_data_dict.json"
# quick check selected categories
for p,label in [(td_path,"gemini text_data"),(h_td_path,"hachimi text_data")]:
    try:
        j=json.load(open(p,encoding='utf-8'))
        for cat in ["6","88","144","163"]:
            v=j.get(cat,{}).get("1141") or j.get(cat,{}).get(1141)
            print(f" {label} cat {cat} 1141: {repr(v)[:120] if v else 'MISSING'}")
    except Exception as e: print(label,e)

for p,label in [(cst_path,"gemini CST"),(r"G:/Games/steamapps/common/UmamusumePrettyDerby_Jpn/hachimi/localized_data_1/character_system_text_dict.json","hachimi CST")]:
    try:
        j=json.load(open(p,encoding='utf-8'))
        k="1141" if "1141" in j else 1141
        v=j.get(str(k)) or j.get(k)
        if isinstance(v, dict):
            print(f" {label} 1141: {len(v)} voices, sample {list(v.items())[:2]}")
        else:
            print(f" {label} 1141: {repr(v)[:200] if v else 'MISSING'}")
    except Exception as e: print(label,e)

# story timelines for 1141
print("\n=== storytimeline files for chara 1141 ===")
# from chara_story_data ids: check both repos
ids=[r['story_id'] for r in q('SELECT story_id FROM chara_story_data WHERE chara_id=1141')]
print(" story_ids:", ids)
for sid in ids:
    s=str(sid)
    pattern_a=f"G:/Games/steamapps/common/UmamusumePrettyDerby_Jpn/gemini_horses/localized_data/assets/story/data/*/*/storytimeline_{s}.json"
    pattern_b=f"G:/Games/steamapps/common/UmamusumePrettyDerby_Jpn/hachimi/localized_data_1/assets/story/data/*/*/storytimeline_{s}.json"
    a=glob.glob(pattern_a); b=glob.glob(pattern_b)
    print(f"  {s}: gemini={bool(a)} hachimi={bool(b)}")
    for p in (a+b)[:1]:
        try:
            j=json.load(open(p,encoding='utf-8'))
            blks=j.get("text_block_list",[])[:2]
            for i,blk in enumerate(blks[:2]):
                print(f"    block {i}: name={blk.get('name')!r} text={blk.get('text','')[:80]!r}")
        except Exception as e: print(e)
