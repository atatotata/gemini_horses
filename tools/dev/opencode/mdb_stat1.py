import sqlite3
c = sqlite3.connect(r'file:G:/Games/steamapps/common/UmamusumePrettyDerby_Jpn/UmamusumePrettyDerby_Jpn_Data/Persistent/master/master.mdb?mode=ro', uri=True)
cur = c.cursor()
print('stat1 rows:', cur.execute('SELECT COUNT(*) FROM sqlite_stat1').fetchone()[0])
print('stat1 sample:', [r for r in cur.execute('SELECT * FROM sqlite_stat1 LIMIT 3')])
print('total tables incl internal:', cur.execute("SELECT COUNT(*) FROM sqlite_master WHERE type='table'").fetchone()[0])
