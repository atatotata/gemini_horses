import sqlite3
con = sqlite3.connect(r'G:\Games\steamapps\common\UmamusumePrettyDerby_Jpn\UmamusumePrettyDerby_Jpn_Data\Persistent\master\master.mdb')
cur = con.cursor()
tables = [r[0] for r in cur.execute("SELECT name FROM sqlite_master WHERE type='table' ORDER BY name")]
for t in tables:
    if any(k in t.lower() for k in ['story','chara','single','main','event','extra','home','race','lyric','race']):
        n = cur.execute(f'SELECT COUNT(*) FROM "{t}"').fetchone()[0]
        print(f'{n:8d}  {t}')
print('---')
print('total tables', len(tables))
