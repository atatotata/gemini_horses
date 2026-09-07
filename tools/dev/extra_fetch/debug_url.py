#!/usr/bin/env python3
"""Debug: check meta platform and try various CDN URL patterns."""
import apsw
import urllib.request
import json

META_PATH = r"G:\Games\steamapps\common\UmamusumePrettyDerby_Jpn\UmamusumePrettyDerby_Jpn_Data\Persistent\meta"
DB_KEY = "9c2bab97bcf8c0c4f1a9ea7881a213f6c9ebf9d8d4c6a8e43ce5a259bde7e9fd"

uri = f"file:{META_PATH}?hexkey={DB_KEY}"
db = apsw.Connection(uri, flags=apsw.SQLITE_OPEN_READONLY | apsw.SQLITE_OPEN_URI)
cur = db.cursor()

# Check platform
platforms = cur.execute("SELECT DISTINCT substr(n, 1, 4) FROM a LIMIT 10").fetchall()
print("Platform prefixes:", [p[0] for p in platforms])

# Get a known 09 entry
row = cur.execute("SELECT n, h, e FROM a WHERE n LIKE 'story/data/09/%/storytimeline_%' LIMIT 1").fetchone()
if row:
    n, h, e = row
    print(f"\nSample: n={n}, h={h}, e={e}")
    
    # Try multiple URL patterns
    prefix = h[:2]
    urls = [
        f"https://prd-storage-game-umamusume.akamaized.net/dl/resources/Windows/assetbundles/{prefix}/{h}",
        f"https://prd-storage-game-umamusume.akamaized.net/dl/resources/windows/assetbundles/{prefix}/{h}",
        f"https://prd-storage-game-umamusume.akamaized.net/dl/resource/Windows/assetbundles/{prefix}/{h}",
        f"https://prd-storage-game-umamusume.akamaized.net/dl/resources/Windows/{prefix}/{h}",
    ]
    for url in urls:
        try:
            req = urllib.request.Request(url)
            resp = urllib.request.urlopen(req, timeout=15)
            data = resp.read()
            print(f"  OK ({len(data)} bytes): {url}")
            break
        except urllib.error.HTTPError as e:
            print(f"  HTTP {e.code}: {url}")
        except Exception as e:
            print(f"  Error: {e} -> {url}")
else:
    print("No 09 entry found!")

# Also check what 'Windows' looks like as n value
win_rows = cur.execute("SELECT n FROM a WHERE n LIKE 'Windows%' LIMIT 5").fetchall()
print("\n'Windows' prefixed entries:", [r[0] for r in win_rows])

db.close()
