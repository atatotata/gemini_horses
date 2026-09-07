#!/usr/bin/env python3
"""Debug: check exact meta paths for 09 prefix SIDs."""
import apsw

META_PATH = r"G:\Games\steamapps\common\UmamusumePrettyDerby_Jpn\UmamusumePrettyDerby_Jpn_Data\Persistent\meta"
DB_KEY = "9c2bab97bcf8c0c4f1a9ea7881a213f6c9ebf9d8d4c6a8e43ce5a259bde7e9fd"

uri = f"file:{META_PATH}?hexkey={DB_KEY}"
db = apsw.Connection(uri, flags=apsw.SQLITE_OPEN_READONLY | apsw.SQLITE_OPEN_URI)
cur = db.cursor()

# Check specific SID paths
test_sids = [90009001, 90014001, 90016002, 90025001]
for sid in test_sids:
    sid_str = str(sid).zfill(9)
    expected_path = f"story/data/{sid_str[:2]}/{sid_str[2:6]}/storytimeline_{sid_str}"
    row = cur.execute("SELECT n, h, e FROM a WHERE n = ?", (expected_path,)).fetchone()
    if row:
        print(f"  SID {sid}: FOUND -> n={row[0]}, h={row[1]}")
    else:
        print(f"  SID {sid}: NOT FOUND at {expected_path}")
        # Search for any path containing the SID
        rows = cur.execute("SELECT n, h, e FROM a WHERE n LIKE ?", (f"%{sid_str}%",)).fetchall()
        if rows:
            for r in rows:
                print(f"    Found: n={r[0]}, h={r[1]}, e={r[2]}")
        else:
            print(f"    No match at all for {sid_str}")

# Now check: what paths do type=1 story_event_story_data IDs map to?
# Let's look at all story/data/09 paths that don't have "resourcelist" in them
rows = cur.execute("SELECT n, h, e FROM a WHERE n LIKE 'story/data/09/%/storytimeline_%' AND n NOT LIKE '%resources%'").fetchall()
print(f"\nTotal story/data/09 storytimeline (non-resources) rows: {len(rows)}")
if rows:
    print("  Sample:")
    for r in rows[:5]:
        print(f"    n={r[0]}, h={r[1]}, e={r[2]}")

# Also check if there are entries that DON'T have resourcelist  
# but have a different structure
rows2 = cur.execute("SELECT n, h, e FROM a WHERE n LIKE 'story/data/09/%/storytimeline_%'").fetchall()
print(f"\nTotal story/data/09 storytimeline (all) rows: {len(rows2)}")
# Group by structure
from collections import Counter
c = Counter()
for r in rows2:
    parts = r[0].split("/")
    if len(parts) >= 5:
        key = "/".join(parts[3:])
    else:
        key = r[0]
    c[key] += 1
for k, v in c.most_common(20):
    print(f"  {k}: {v}")

db.close()
