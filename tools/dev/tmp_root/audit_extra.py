import sqlite3, pathlib, json, os, re
from collections import Counter
mdb = pathlib.Path(r"G:\Games\steamapps\common\UmamusumePrettyDerby_Jpn\UmamusumePrettyDerby_Jpn_Data\Persistent\master\master.mdb")
con = sqlite3.connect(str(mdb))
cur = con.cursor()
tables = [r[0] for r in cur.execute("SELECT name FROM sqlite_master WHERE type='table'").fetchall()]
# find event/story tables
candidates = [t for t in tables if 'story' in t.lower() or 'event' in t.lower() or 'anniv' in t.lower() or 'movie' in t.lower()]
print("candidate tables:", candidates)
for t in candidates:
    try:
        cnt = cur.execute(f'SELECT COUNT(*) FROM "{t}"').fetchone()[0]
        cols = [r[1] for r in cur.execute(f'PRAGMA table_info("{t}")').fetchall()]
        print(f"{t}: {cnt} rows cols={cols}")
        # sample 2 rows
        for row in cur.execute(f'SELECT * FROM "{t}" LIMIT 2').fetchall():
            print(" ", row[:10])
    except Exception as e:
        print(t, "err", e)

# also check localized_data distribution
base = pathlib.Path(r"G:/Games/steamapps/common/UmamusumePrettyDerby_Jpn/gemini_horses/localized_data/assets/story/data")
c = Counter()
for p in base.rglob("storytimeline_*.json"):
    rel = p.relative_to(base)
    c[rel.parts[0]] += 1
print("localized_data by prefix:", dict(sorted(c.items())))
print("total localized:", sum(c.values()))

# check meta if available - try to count story prefixes
try:
    import shutil
    meta_src = pathlib.Path(r"G:\Games\steamapps\common\UmamusumePrettyDerby_Jpn\UmamusumePrettyDerby_Jpn_Data\Persistent\meta")
    tmp = pathlib.Path(r"C:\TMP\meta_tmp_copy")
    if not tmp.exists():
        shutil.copy(str(meta_src), str(tmp))
        print("copied meta to tmp")
    # try apsw
    import apsw
    # need key - use hachimi-tools const
    # brute try chacha20 hexkey from earlier audit
    # we know meta table a exists
    # use apsw with hexkey via pragma
    # try to open with apsw
    # key derived: 9c2bab97bcf8c0c4f1a9ea7881a213f6c9ebf9d8d4c6a8e43ce5a259bde7e9fd
    import pathlib as pl
    # use apsw connection with encryption?
    # attempt using apsw with key
    print("trying apsw open...")
    # We'll try using sqlcipher via apsw
    # Simpler: try to use sqlite3 and see error
    import subprocess, textwrap
    # use existing hachimi-tools decrypt to test?
except Exception as e:
    print("meta check skipped:", e)
