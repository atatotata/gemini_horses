import sqlite3
MASTER_PATH = r"G:\Games\steamapps\common\UmamusumePrettyDerby_Jpn\UmamusumePrettyDerby_Jpn_Data\Persistent\master\master.mdb"
mconn = sqlite3.connect(MASTER_PATH)
mc = mconn.cursor()
mc.execute("SELECT name FROM sqlite_master WHERE type='table'")
tables = [row[0] for row in mc.fetchall()]
print("Tables:", tables)
for t in tables:
    if 'story' in t.lower():
        mc.execute(f"PRAGMA table_info({t})")
        cols = mc.fetchall()
        print(f"\n{t} columns: {[c[1] for c in cols]}")
        mc.execute(f"SELECT * FROM {t} LIMIT 2")
        rows = mc.fetchall()
        for r in rows:
            print(f"  {r}")
mconn.close()
