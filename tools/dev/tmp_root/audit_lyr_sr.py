import apsw, re, sys
from pathlib import Path
KEY = "9c2bab97bcf8c0c4f1a9ea7881a213f6c9ebf9d8d4c6a8e43ce5a259bde7e9fd"
META = r'C:\TMP\meta_fresh.bin'
LOC = Path(r'G:\Games\steamapps\common\UmamusumePrettyDerby_Jpn\gemini_horses\localized_data')
log = open(r'C:\TMP\audit_hls_out.txt','w',encoding='utf-8')
def P(*a): print(*a, file=log); log.flush()

conn = apsw.Connection(f'file:{META}?hexkey={KEY}', flags=apsw.SQLITE_OPEN_READONLY | apsw.SQLITE_OPEN_URI)
cur = conn.cursor()

# LYRICS
rows = cur.execute("SELECT n FROM a WHERE n LIKE 'live/musicscores/%'").fetchall()
meta_music = set()
for (n,) in rows:
    if n.endswith('_lyrics'):
        meta_music.add(n.rsplit('/',1)[1].replace('_lyrics',''))
P("meta music lyric entries:", len(meta_music), "samples", sorted(meta_music)[:5])
loc_lyr = {f.name.replace('_lyrics.json','') for f in (LOC/'assets'/'lyrics').glob('*_lyrics.json')}
P("local lyrics music ids:", len(loc_lyr))
P("lyric gap meta-not-local:", len(meta_music - loc_lyr))
P("local-only lyric:", sorted(loc_lyr - meta_music))

# STORYRACE
rows = cur.execute("SELECT n FROM a WHERE n LIKE 'race/storyrace/text/%'").fetchall()
meta_sr = set()
for (n,) in rows:
    meta_sr.add(n.split('/')[-1].replace('storyrace_',''))
P("meta storyrace text ids:", len(meta_sr))
loc_sr = {f.name.replace('storyrace_','').replace('.json','') for f in (LOC/'assets'/'race'/'storyrace').rglob('storyrace_*.json')}
P("local storyrace files:", len(loc_sr))
miss_sr = meta_sr - loc_sr
only_sr = loc_sr - meta_sr
P("storyrace gap meta-not-local:", len(miss_sr), sorted(miss_sr)[:40])
P("local-only storyrace:", len(only_sr), sorted(only_sr)[:40])
conn.close()
log.close()
print("done")
