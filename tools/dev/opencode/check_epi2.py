import sqlite3, json, glob, pathlib, os
mdb=r"G:/Games/steamapps/common/UmamusumePrettyDerby_Jpn/UmamusumePrettyDerby_Jpn_Data/Persistent/master/master.mdb"
conn=sqlite3.connect(mdb)
conn.text_factory=bytes
conn.row_factory=sqlite3.Row
def safe(b):
    if b is None: return ""
    if isinstance(b, bytes):
        try: return b.decode('utf-8')
        except: return b.decode('utf-8','replace')
    return str(b)
def q(sql,p=()):
    return list(conn.execute(sql,p))

print("=== text_data for 1141 with proper decode ===")
for r in q('SELECT category, "index", text FROM text_data WHERE "index"=1141 ORDER BY category'):
    cat=r['category']; idx=r['index']; txt=safe(r['text'])
    print(f" cat {cat:>3}: {txt[:120]!r}")

print("\n=== is cat 88 present for 1141? ===")
rows=q('SELECT "index", text FROM text_data WHERE category=88 AND "index"=1141')
print(" count", len(rows))
for r in rows: print(repr(safe(r['text'])[:300]))

print("\n=== cat 163 for 1141 ===")
rows=q('SELECT text FROM text_data WHERE category=163 AND "index"=1141')
for r in rows: print(repr(safe(r['text'])[:300]))

print("\n=== gemini localized_data raw ===")
for path in [r"G:/Games/steamapps/common/UmamusumePrettyDerby_Jpn/gemini_horses/localized_data/text_data_dict.json", r"G:/Games/steamapps/common/UmamusumePrettyDerby_Jpn/hachimi/localized_data_1/text_data_dict.json"]:
    j=json.load(open(path,encoding='utf-8'))
    print(path)
    for cat in ["6","88","144","163"]:
        d=j.get(cat,{})
        v=d.get("1141") or d.get(1141)
        print(f"  cat {cat}: {'FOUND' if v else 'MISSING'} {repr(v)[:140] if v else ''}")

print("\n=== chara stories ===")
ids=[r[0] for r in q('SELECT story_id FROM chara_story_data WHERE chara_id=1141 ORDER BY episode_index')]
print(ids)
for sid in ids:
    # map to asset path: UmaTL uses assets/story/data/AA/BBBB/storytimeline_<id>.json where AA = str(sid)[:2], BBBB = str(sid)[2:6]? Need verify
    s=str(sid)
    # Try common patterns
    candidates=glob.glob(f"G:/Games/steamapps/common/UmamusumePrettyDerby_Jpn/gemini_horses/localized_data/assets/story/data/**/storytimeline_{s}.json", recursive=True)
    print(f" {s}: localized exists={bool(candidates)}")
# Check dat via meta if needed
# Also check how many chara stories overall missing
all_ids=[r[0] for r in q('SELECT story_id FROM chara_story_data')]
present=set()
for p in glob.glob("G:/Games/steamapps/common/UmamusumePrettyDerby_Jpn/gemini_horses/localized_data/assets/story/data/**/storytimeline_*.json", recursive=True):
    import re
    m=re.search(r'storytimeline_(\d+)\.json', p)
    if m: present.add(int(m.group(1)))
missing=[i for i in all_ids if i not in present]
print(f"\nTotal chara_story_data: {len(all_ids)}, present in gemini: {len(all_ids)-len(missing)}, missing: {len(missing)}")
print(" missing sample", missing[:20])
# Also check Epiphaneia vs missing
print(" Epiphaneia ids missing?", [i for i in ids if i in missing])
