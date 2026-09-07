import apsw
from collections import Counter

KEY = "9c2bab97bcf8c0c4f1a9ea7881a213f6c9ebf9d8d4c6a8e43ce5a259bde7e9fd"
path = r'C:\TMP\meta_fresh.bin'
uri = f'file:{path}?hexkey={KEY}'
conn = apsw.Connection(uri, flags=apsw.SQLITE_OPEN_READONLY | apsw.SQLITE_OPEN_URI)
cur = conn.cursor()

print("count a:", cur.execute("SELECT COUNT(*) FROM a").fetchone()[0])
print("columns of a:", [r[1] for r in cur.execute("PRAGMA table_info(a)")])

# Count distinct families / second-level for n LIKE patterns
for label, like in [
    ("story/data/storytimeline", "story/data/%/storytimeline_%"),
    ("home/data", "home/data/%"),
    ("story race?", "story/%race%"),
    ("race", "%race%"),
    ("lyric", "%lyric%"),
    ("home (all)", "home/%"),
]:
    rows = cur.execute("SELECT n FROM a WHERE n LIKE ?", (like,)).fetchall()
    print(f"\n[{label}] LIKE {like}: {len(rows)} rows")
    if rows:
        from collections import Counter
        # print up to 3 samples
        for (n,) in rows[:3]:
            print("   sample:", n)
