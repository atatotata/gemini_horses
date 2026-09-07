import apsw, re, json
from pathlib import Path

KEY = "9c2bab97bcf8c0c4f1a9ea7881a213f6c9ebf9d8d4c6a8e43ce5a259bde7e9fd"
META = r'C:\TMP\meta_fresh.bin'
LOC = Path(r'G:\Games\steamapps\common\UmamusumePrettyDerby_Jpn\gemini_horses\localized_data')

res = {}

conn = apsw.Connection(f'file:{META}?hexkey={KEY}', flags=apsw.SQLITE_OPEN_READONLY | apsw.SQLITE_OPEN_URI)
cur = conn.cursor()

# --- HOME ---
meta_home = {}
rows = cur.execute("SELECT n FROM a WHERE n LIKE 'home/data/%'").fetchall()
for (n,) in rows:
    p = n.split('/')
    if len(p) == 5 and p[4].startswith('hometimeline_'):
        meta_home[p[4]] = n  # basename -> path
meta_home2 = {b.split('hometimeline_',1)[1] for b in meta_home}
print("meta home plain basenames:", len(meta_home))
print("meta home id-suffix distinct:", len(meta_home2))

loc_home = set()
home_files = list((LOC/'assets'/'home'/'data').rglob('*.json'))
plain_home = 0
for f in home_files:
    if f.name.startswith('hometimeline_'):
        plain_home += 1
        loc_home.add(f.name.split('hometimeline_',1)[1].rsplit('.json',1)[0])
print("local home total json:", len(home_files), " plain hometimeline:", plain_home, " distinct suffix:", len(loc_home))
# compare id-suffix sets
mh = {b.split('hometimeline_',1)[1] for b in meta_home if '_' in b}
miss = mh - loc_home
print("home gap (meta suffix not local):", len(miss))

# --- LYRICS ---
rows = cur.execute("SELECT n FROM a WHERE n LIKE 'live/musicscores/%'").fetchall()
meta_music = set()
for (n,) in rows:
    if n.endswith('_lyrics'):
        meta_music.add(n.rsplit('/',1)[1].replace('_lyrics',''))
print("\nmeta music lyric entries:", len(meta_music))
loc_lyr = {f.name.replace('_lyrics.json','') for f in (LOC/'assets'/'lyrics').glob('*_lyrics.json')}
print("local lyrics music ids:", len(loc_lyr))
print("lyric gap meta-not-local:", len(meta_music - loc_lyr), sorted(meta_music - loc_lyr)[:25])
print("local-only lyric:", loc_lyr - meta_music)

# --- STORYRACE ---
rows = cur.execute("SELECT n FROM a WHERE n LIKE 'race/storyrace/text/%'").fetchall()
meta_sr = {n.split('/')[-1].replace('storyrace_','') for (n,) in rows}
print("\nmeta storyrace text ids:", len(meta_sr))
loc_sr = {f.name.replace('storyrace_','').replace('.json','') for f in (LOC/'assets'/'race'/'storyrace').rglob('storyrace_*.json')}
print("local storyrace files:", len(loc_sr))
print("storyrace gap meta-not-local:", len(meta_sr - loc_sr), sorted(meta_sr - loc_sr))
print("local-only storyrace:", len(loc_sr - meta_sr), sorted(loc_sr - meta_sr))
conn.close()
