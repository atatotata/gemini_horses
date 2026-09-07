import sqlite3, pathlib
mdb = r"G:\Games\steamapps\common\UmamusumePrettyDerby_Jpn\UmamusumePrettyDerby_Jpn_Data\Persistent\master\master.mdb"
con = sqlite3.connect(mdb)
cur = con.cursor()

def get_story_ids(table):
    # generic: get all story_id_* where story_type_* !=0
    cols = [c[1] for c in cur.execute(f'PRAGMA table_info("{table}")').fetchall()]
    # find story_type_* and story_id_* pairs
    types = [c for c in cols if c.startswith("story_type")]
    ids = []
    for t in types:
        num = t.split("_")[-1]
        id_col = f"story_id_{num}"
        if id_col in cols:
            rows = cur.execute(f'SELECT "{id_col}" FROM "{table}" WHERE "{t}"!=0 AND "{id_col}"!=0').fetchall()
            ids.extend([r[0] for r in rows])
    return sorted(set(ids))

# Extra Stories mapping
# Story Event: 55 events shown in screenshot (Story Event 55/55)
# table story_event_story_data should give story timeline ids for those
# But we need to confirm count 55
cnt_event = cur.execute('SELECT COUNT(*) FROM story_event_data').fetchone()[0]
print(f"story_event_data: {cnt_event} events")
ids_event = get_story_ids("story_event_story_data")
print(f" story_event_story_data: {len(ids_event)} unique story ids, sample {ids_event[:10]}")
# also check distinct event count in that table
try:
    print(" distinct story_event_id in story_event_story_data:", cur.execute('SELECT COUNT(DISTINCT story_event_id) FROM story_event_story_data').fetchone()[0])
except: pass

# Anniversary: 11/11 - likely story_extra_data where? Let's inspect
cols = [c[1] for c in cur.execute('PRAGMA table_info("story_extra_data")').fetchall()]
print("\nstory_extra_data cols", cols)
rows = cur.execute('SELECT * FROM story_extra_data').fetchall()
print(f" story_extra_data {len(rows)} rows:")
for r in rows: print(" ", r)
# story_extra_story_data
ids_extra = get_story_ids("story_extra_story_data")
print(f"\nstory_extra_story_data: {len(ids_extra)} unique ids sample {ids_extra[:10]} total rows {cur.execute('SELECT COUNT(*) FROM story_extra_story_data').fetchone()[0]}")
# group by story_extra_id
try:
    for row in cur.execute('SELECT story_extra_id, COUNT(*) FROM story_extra_story_data GROUP BY story_extra_id').fetchall():
        print(f"  extra_id {row[0]}: {row[1]} timelines")
except: pass

# Movie: 4/4
cnt_movie = cur.execute('SELECT COUNT(*) FROM story_extra_movie_data').fetchone()[0]
print(f"\nstory_extra_movie_data: {cnt_movie} movies")
for r in cur.execute('SELECT * FROM story_extra_movie_data').fetchall(): print(" ", r)
cnt_evt_movie = cur.execute('SELECT COUNT(*) FROM story_extra_event_movie').fetchone()[0]
print(f"story_extra_event_movie: {cnt_evt_movie} rows")
for r in cur.execute('SELECT * FROM story_extra_event_movie LIMIT 5').fetchall(): print(" ", r)

# Localized ids
base = pathlib.Path(r"G:/Games/steamapps/common/UmamusumePrettyDerby_Jpn/gemini_horses/localized_data/assets/story/data")
local_ids = set()
import pathlib as pl
for p in base.rglob("storytimeline_*.json"):
    try: local_ids.add(int(p.stem.split("_")[1]))
    except: pass
print(f"\nlocalized total {len(local_ids)}")

def cov(name, idlist):
    s=set(idlist)
    if not s:
        print(f"{name}: 0 ids")
        return
    have=s & local_ids
    miss=s - local_ids
    print(f"{name}: {len(s)} total, {len(have)} have ({len(have)/len(s)*100:.1f}%), {len(miss)} missing")
    if miss: print("  missing sample", sorted(miss)[:10])
    # also prefix distribution
    from collections import Counter
    c=Counter()
    for sid in s:
        c[str(sid).zfill(9)[:2]]+=1
    print("  by prefix", dict(c))
    return miss

print("\n--- Coverage vs localized ---")
m_event = cov("Story Event (story_event_story_data)", ids_event)
m_extra = cov("Seasonal/Extra (story_extra_story_data)", ids_extra)
# also check movie ids? movie ids are not storytimeline, skip

# Also check: what story types are these? story_type
for tbl in ["story_event_story_data","story_extra_story_data"]:
    print(f"\n{tbl} type distribution:")
    cols_t = [c[1] for c in cur.execute(f'PRAGMA table_info("{tbl}")').fetchall()]
    for col in cols_t:
        if col.startswith("story_type"):
            vals = cur.execute(f'SELECT "{col}", COUNT(*) FROM "{tbl}" GROUP BY "{col}"').fetchall()
            print(f" {col}: {vals}")

# Check localized prefix counts for event-related prefixes
from collections import Counter
c=Counter()
for sid in local_ids:
    pref=str(sid).zfill(9)[:2]
    c[pref]+=1
print("\nlocalized prefix full:", dict(sorted(c.items())))
# Event ids are 9xxxxxxx -> prefix 09, extra ids are 1xxxxxxx -> prefix 10/01 etc

# Also total storytimeline in meta for comparison if possible - try to open meta quickly via apsw
try:
    import shutil, pathlib
    meta_src = pathlib.Path(r"G:\Games\steamapps\common\UmamusumePrettyDerby_Jpn\UmamusumePrettyDerby_Jpn_Data\Persistent\meta")
    tmp = pathlib.Path(r"C:\TMP\meta_tmp_copy2")
    if not tmp.exists():
        shutil.copy(str(meta_src), str(tmp))
        print("\ncopied meta")
    import apsw
    # key from hachimi-tools const.py
    # baseKey f170cea4dfcea3e1a5d8c70bd1 (13 bytes) plainKey hex?
    base_hex="f170cea4dfcea3e1a5d8c70bd1"
    plain_hex="6d5b65336336632554712d73505363386d34377b356370233734532973433633"
    import binascii
    base=bytes.fromhex(base_hex)
    plain=bytes.fromhex(plain_hex)
    # final = plain XOR base[i%len(base)]
    final=bytes([ plain[i] ^ base[i % len(base)] for i in range(len(plain)) ])
    hexkey=final.hex()
    print("hexkey", hexkey[:16]+"...")
    db=apsw.Connection(str(tmp))
    cur2=db.cursor()
    # try pragma
    cur2.execute(f"PRAGMA key=\"x'{hexkey}'\"")
    # try select
    tables2 = [r[0] for r in cur2.execute("SELECT name FROM sqlite_master WHERE type='table'").fetchall()]
    print("meta tables", tables2[:10])
    cnt_a = cur2.execute("SELECT COUNT(*) FROM a").fetchone()[0]
    print(f"meta a total {cnt_a}")
    # count story by prefix in meta
    rows = cur2.execute("SELECT n FROM a WHERE n LIKE 'story/data/%/storytimeline_%'").fetchall()
    print(f"meta storytimeline rows {len(rows)}")
    from collections import Counter as C2
    cc=C2()
    for (n,) in rows:
        # n = story/data/09/0035/storytimeline_090035007
        parts=n.split("/")
        if len(parts)>=3:
            pref=parts[2]
            cc[pref]+=1
    print("meta by prefix", dict(sorted(cc.items())))
    # check how many of our event ids are in meta
    # build map sid -> n : story/data/XX/YYYY/storytimeline_{sid:09d}
    def sid_to_path(sid):
        s=str(sid).zfill(9)
        return f"story/data/{s[:2]}/{s[2:6]}/storytimeline_{s}"
    missing_in_meta=[]
    have_in_meta=[]
    for sid in list(ids_event)[:5]:
        path=sid_to_path(sid)
        cnt=cur2.execute("SELECT COUNT(*) FROM a WHERE n=?", (path,)).fetchone()[0]
        print(f" check {sid} -> {path} -> {cnt}")
    # bulk check
    for sid in ids_event:
        path=sid_to_path(sid)
        if cur2.execute("SELECT COUNT(*) FROM a WHERE n=?", (path,)).fetchone()[0]>0:
            have_in_meta.append(sid)
        else:
            missing_in_meta.append(sid)
    print(f"event ids in meta: {len(have_in_meta)}/{len(ids_event)} have, missing {len(missing_in_meta)} sample {missing_in_meta[:5]}")
    # same for extra
    have2=[]
    miss2=[]
    for sid in ids_extra:
        path=sid_to_path(sid)
        if cur2.execute("SELECT COUNT(*) FROM a WHERE n=?", (path,)).fetchone()[0]>0:
            have2.append(sid)
        else:
            miss2.append(sid)
    print(f"extra ids in meta: {len(have2)}/{len(ids_extra)} have, missing {len(miss2)} sample {miss2[:5]}")
except Exception as e:
    import traceback; traceback.print_exc()
    print("meta err", e)
