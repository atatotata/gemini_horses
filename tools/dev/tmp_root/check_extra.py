import sqlite3, pathlib, collections, json, os, re
mdb = r"G:\Games\steamapps\common\UmamusumePrettyDerby_Jpn\UmamusumePrettyDerby_Jpn_Data\Persistent\master\master.mdb"
con = sqlite3.connect(mdb)
cur = con.cursor()
tables = [r[0] for r in cur.execute("SELECT name FROM sqlite_master WHERE type='table'").fetchall()]
cand = [t for t in tables if 'story' in t.lower() or 'event' in t.lower()]
print("CAND TABLES:", cand)
for t in cand:
    cols = [c[1] for c in cur.execute(f'PRAGMA table_info("{t}")').fetchall()]
    try:
        cnt = cur.execute(f'SELECT COUNT(*) FROM "{t}"').fetchone()[0]
    except: cnt="?"
    print(f"{t}: {cnt} cols={cols}")
    try:
        rows = cur.execute(f'SELECT * FROM "{t}" LIMIT 2').fetchall()
        for r in rows: print(" ", r)
    except Exception as e: print("  err",e)

# check which story IDs belong to Extra Stories
# story_event_data usually maps event -> story ids
for t in cand:
    if 'story_event' in t.lower():
        try:
            # list distinct story ids
            cur2 = cur.execute(f'SELECT * FROM "{t}"')
            # try to find column containing story id
            cols = [c[1] for c in cur.execute(f'PRAGMA table_info("{t}")').fetchall()]
            print(f"cols for {t}:", cols)
        except: pass

# check text_data category for titles?
# already know 181 etc
# count localized by prefix
base = pathlib.Path(r"G:/Games/steamapps/common/UmamusumePrettyDerby_Jpn/gemini_horses/localized_data/assets/story/data")
from collections import Counter
c=Counter()
for p in base.rglob("storytimeline_*.json"):
    rel=p.relative_to(base); c[rel.parts[0]]+=1
print("localized by prefix:", dict(sorted(c.items())), "total", sum(c.values()))

# also check raw story_event story ids vs meta/localized
# try to brute list all story ids from story_event_data if has story_id column
try:
    t="story_event_data"
    if t in cand:
        cols=[c[1] for c in cur.execute(f'PRAGMA table_info("{t}")').fetchall()]
        print("story_event_data cols detail")
        for col in cols:
            distinct = cur.execute(f'SELECT COUNT(DISTINCT "{col}") FROM "{t}"').fetchone()[0]
            print(f" col {col}: distinct {distinct} sample", cur.execute(f'SELECT "{col}" FROM "{t}" LIMIT 3').fetchall())
except Exception as e: print(e)

# also check single_mode vs story_event vs anniversary table
# anniversary_data?
for t in [x for x in tables if 'anniv' in x.lower() or 'movie' in x.lower()]:
    cols=[c[1] for c in cur.execute(f'PRAGMA table_info("{t}")').fetchall()]
    cnt=cur.execute(f'SELECT COUNT(*) FROM "{t}"').fetchone()[0]
    print(f"anniv/movie {t}: {cnt} {cols}")

# Try to infer Extra Stories 73 items mapping
# Check meta storytimeline counts per prefix via quick scan of localized vs expected 55+11+4+3=73
# Actually 73 is number of EVENTS, not timelines - each event has multiple timelines
print("Done")
