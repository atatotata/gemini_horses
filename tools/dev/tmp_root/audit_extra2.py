import sqlite3, pathlib, collections, json
mdb = r"G:\Games\steamapps\common\UmamusumePrettyDerby_Jpn\UmamusumePrettyDerby_Jpn_Data\Persistent\master\master.mdb"
con = sqlite3.connect(mdb)
cur = con.cursor()
def q(sql):
    return [r[0] for r in cur.execute(sql).fetchall()] if "SELECT" in sql else None

# Inspect Extra Stories tables
tables = ["story_extra_data","story_extra_story_data","story_extra_movie_data","story_extra_event_movie","story_event_data","story_event_story_data"]
for t in tables:
    cols = [c[1] for c in cur.execute(f'PRAGMA table_info("{t}")').fetchall()]
    cnt = cur.execute(f'SELECT COUNT(*) FROM "{t}"').fetchone()[0]
    print(f"\n{t}: {cnt} rows")
    print(" cols:", cols)
    rows = cur.execute(f'SELECT * FROM "{t}" LIMIT 5').fetchall()
    for r in rows: print(" ", r)

# Gather story IDs per category
extra_story_ids = []
try:
    rows = cur.execute('SELECT story_id_1, story_id_2, story_id_3, story_id_4, story_id_5 FROM story_extra_story_data').fetchall()
    for r in rows:
        for sid in r:
            if sid and sid != 0:
                extra_story_ids.append(sid)
except Exception as e:
    print("story_extra_story_data err",e)
# story_event_story_data
event_story_ids = []
try:
    # list cols
    cols = [c[1] for c in cur.execute('PRAGMA table_info("story_event_story_data")').fetchall()]
    print("\nstory_event_story_data cols", cols)
    # dump rows
    rows = cur.execute('SELECT * FROM "story_event_story_data" LIMIT 3').fetchall()
    for r in rows: print(r)
    # guess story id col
    for col in cols:
        if "story" in col.lower():
            print(f" distinct {col}:", cur.execute(f'SELECT COUNT(*) FROM "story_event_story_data" WHERE "{col}"!=0').fetchone()[0])
    # assume story_id
    for col in cols:
        if "story_id" in col.lower():
            ids = [r[0] for r in cur.execute(f'SELECT "{col}" FROM "story_event_story_data" WHERE "{col}"!=0').fetchall()]
            event_story_ids.extend(ids)
            print(f"col {col} total {len(ids)} sample {ids[:5]}")
except Exception as e: print(e)

print(f"\nExtra seasonal/story_extra ids: {len(extra_story_ids)} total {len(set(extra_story_ids))} unique sample {sorted(set(extra_story_ids))[:10]}")
print(f"Event story ids: {len(event_story_ids)} unique {len(set(event_story_ids))} sample {sorted(set(event_story_ids))[:10]}")

# Anniversary? maybe story_event_data with type?
# Check story_extra_data
try:
    rows = cur.execute('SELECT * FROM story_extra_data LIMIT 10').fetchall()
    print("\nstory_extra_data samples")
    for r in rows: print(r)
except: pass

# Movie ids
try:
    rows = cur.execute('SELECT * FROM story_extra_movie_data').fetchall()
    print("\nstory_extra_movie_data", len(rows), rows)
    rows2 = cur.execute('SELECT * FROM story_extra_event_movie').fetchall()
    print("story_extra_event_movie", len(rows2), rows2[:5])
except: pass

# Localized_data presence
base = pathlib.Path(r"G:/Games/steamapps/common/UmamusumePrettyDerby_Jpn/gemini_horses/localized_data/assets/story/data")
from collections import Counter
c=Counter()
all_local_ids=set()
for p in base.rglob("storytimeline_*.json"):
    try:
        sid = int(p.stem.replace("storytimeline_",""))
        all_local_ids.add(sid)
    except: pass
    rel=p.relative_to(base); c[rel.parts[0]]+=1
print("\nlocalized by prefix:", dict(sorted(c.items())), "total", len(all_local_ids))

# Check coverage for extra categories
def check(ids, label):
    ids_set=set(ids)
    have = ids_set & all_local_ids
    miss = ids_set - all_local_ids
    print(f"{label}: {len(ids_set)} total, {len(have)} have ({len(have)/len(ids_set)*100:.1f}%), {len(miss)} missing")
    if miss: print("  missing sample", sorted(miss)[:10])
    return miss

print("\n--- Coverage ---")
m1 = check(extra_story_ids, "story_extra_story_data (Seasonal/Extra)")
m2 = check(event_story_ids, "story_event_story_data (Story Event 55)")
# Also check story_event_data story ids if any
try:
    # story_event_data may not have story ids directly, but story_event_story_data is mapping
    pass
except: pass
# Anniversary guess: story_extra_data id linking?
# Try story_extra_data -> extra_story_data via story_extra_story_data's story_extra_data_id?
cols = [c[1] for c in cur.execute('PRAGMA table_info("story_extra_story_data")').fetchall()]
print("\nstory_extra_story_data cols:", cols)
# Try to list story_extra_data ids
try:
    sids = [r[0] for r in cur.execute('SELECT "story_id_1" FROM story_extra_story_data').fetchall() if r[0]!=0]
    print("story_id_1 distinct", len(set(sids)))
except: pass

# Check movie - movies are usm not timeline, skip
# Also check home vs story: Extra Stories menu includes story only, not home
# Check if any 09 prefix corresponds to event
# list prefix for event ids
def prefix_map(ids):
    cnt=Counter()
    for sid in ids:
        s=str(sid)
        # Hachimi path is assets/story/data/XX/YYYY/ where XX = first 2 digits of story_id? Actually 09/0035 => 090035007 => prefix 09
        pref=s[:2] if len(s)>=9 else s[:2]
        cnt[pref]+=1
    return cnt
print("event ids by prefix", prefix_map(event_story_ids))
print("extra ids by prefix", prefix_map(extra_story_ids))

# Also check total meta storytimeline counts per prefix via localized? Already have
# Try to load meta to compare if needed - skip for now
