import apsw, sqlite3, json
from pathlib import Path

KEY = "9c2bab97bcf8c0c4f1a9ea7881a213f6c9ebf9d8d4c6a8e43ce5a259bde7e9fd"
conn = apsw.Connection(f'file:C:\\TMP\\meta_fresh.bin?hexkey={KEY}', flags=apsw.SQLITE_OPEN_READONLY | apsw.SQLITE_OPEN_URI)
cur = conn.cursor()
meta_plain = {}
for (n,) in cur.execute("SELECT n FROM a WHERE n LIKE 'story/data/%'"):
    p = n.split('/')
    if len(p)==5 and p[4].startswith('storytimeline_'):
        sid = p[4][14:]
        if sid.isdigit():
            meta_plain[sid.zfill(9)] = p[2]
conn.close()

LOC = Path(r'G:\Games\steamapps\common\UmamusumePrettyDerby_Jpn\gemini_horses\localized_data\assets\story\data')
local = set()
for f in LOC.rglob('storytimeline_*.json'):
    sid = f.stem[14:]
    if sid.isdigit():
        local.add(sid.zfill(9))

con = sqlite3.connect(r'G:\Games\steamapps\common\UmamusumePrettyDerby_Jpn\UmamusumePrettyDerby_Jpn_Data\Persistent\master\master.mdb')
mc = con.cursor()
single = {str(r[0]).zfill(9) for r in mc.execute('SELECT DISTINCT story_id FROM single_mode_story_data WHERE story_id!=0')}
chara  = {str(r[0]).zfill(9) for r in mc.execute('SELECT DISTINCT story_id FROM chara_story_data WHERE story_id!=0')}

def pairs(tbl):
    cols=[c[1] for c in mc.execute(f'PRAGMA table_info("{tbl}")')]
    ns=sorted({c.replace('story_type_','') for c in cols if c.startswith('story_type_')}, key=int)
    s=set()
    for num in ns:
        tc,ic=f'story_type_{num}',f'story_id_{num}'
        if ic in cols:
            s|={str(r[0]).zfill(9) for r in mc.execute(f'SELECT "{ic}" FROM "{tbl}" WHERE "{tc}"!=0 AND "{ic}"!=0')}
    return s
main = pairs('main_story_data'); event = pairs('story_event_story_data'); extra = pairs('story_extra_story_data')
con.close()

for name, s in [('single_mode',single),('chara',chara),('main',main),('event',event),('extra',extra)]:
    im=s & set(meta_plain); il=s & local
    print(f"{name:11s} src={len(s):5d} in_meta={len(im):5d} in_local={len(il):5d} gap={len(im-il):3d} not_in_meta={len(s-im):3d}")
