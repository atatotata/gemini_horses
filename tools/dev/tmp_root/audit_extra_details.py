import apsw, sqlite3
from pathlib import Path
from collections import Counter

KEY = "9c2bab97bcf8c0c4f1a9ea7881a213f6c9ebf9d8d4c6a8e43ce5a259bde7e9fd"
conn = apsw.Connection(f'file:C:\\TMP\\meta_fresh.bin?hexkey={KEY}', flags=apsw.SQLITE_OPEN_READONLY | apsw.SQLITE_OPEN_URI)
cur = conn.cursor()
meta_plain = {}
for (n,) in cur.execute("SELECT n FROM a WHERE n LIKE 'story/data/%'"):
    p = n.split('/')
    if len(p)==5 and p[4].startswith('storytimeline_'):
        meta_plain[p[4][14:]] = p[2]
conn.close()

LOC = Path(r'G:\Games\steamapps\common\UmamusumePrettyDerby_Jpn\gemini_horses\localized_data\assets\story\data')
local = set()
for f in LOC.rglob('storytimeline_*.json'):
    local.add(f.stem[14:])

con = sqlite3.connect(r'G:\Games\steamapps\common\UmamusumePrettyDerby_Jpn\UmamusumePrettyDerby_Jpn_Data\Persistent\master\master.mdb')
mc = con.cursor()
single = {str(r[0]).zfill(9) for r in mc.execute('SELECT DISTINCT story_id FROM single_mode_story_data WHERE story_id!=0')}
con.close()
sm_meta = single & set(meta_plain)
sm_gap = sorted(sm_meta - local)
print("single_mode gap total", len(sm_gap))
print("by prefix:", dict(sorted(Counter(x[:2] for x in sm_gap).items())))

# where do the prefix-40 gaps sit in the per-prefix 40 gap of 356?
p40_gap_all = sorted(x for x in meta_plain if meta_plain[x]=='40' and x not in local)
print("all prefix40 gaps:", len(p40_gap_all), " of which single_mode:", len([x for x in p40_gap_all if x in single]))
p50_gap_all = [x for x in meta_plain if meta_plain[x]=='50' and x not in local]
print("all prefix50 gaps:", len(p50_gap_all), " of which single_mode:", len([x for x in p50_gap_all if x in single]))

# dat size
import os
dat = Path(r'G:\Games\steamapps\common\UmamusumePrettyDerby_Jpn\UmamusumePrettyDerby_Jpn_Data\Persistent\dat')
tot = sum(f.stat().st_size for f in dat.rglob('*') if f.is_file())
print("dat bytes:", tot, "GB:", round(tot/1e9,2))
