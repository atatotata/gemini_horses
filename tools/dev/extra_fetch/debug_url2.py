#!/usr/bin/env python3
"""Debug: check what platform string meta uses and test URL download."""
import apsw
import urllib.request

META_PATH = r"G:\Games\steamapps\common\UmamusumePrettyDerby_Jpn\UmamusumePrettyDerby_Jpn_Data\Persistent\meta"
DB_KEY = "9c2bab97bcf8c0c4f1a9ea7881a213f6c9ebf9d8d4c6a8e43ce5a259bde7e9fd"

uri = f"file:{META_PATH}?hexkey={DB_KEY}"
db = apsw.Connection(uri, flags=apsw.SQLITE_OPEN_READONLY | apsw.SQLITE_OPEN_URI)
cur = db.cursor()

# Get a valid hash
row = cur.execute("SELECT n, h, e FROM a WHERE n = 'story/data/09/0009/storytimeline_090009001'").fetchone()
n, h, e = row
print(f"Test SID: n={n}, h={h}, e={e}")

prefix = h[:2]
# Test various platforms
platforms_to_try = ["Windows", "windows", "WIN", "win"]
for plat in platforms_to_try:
    url = f"https://prd-storage-game-umamusume.akamaized.net/dl/resources/{plat}/assetbundles/{prefix}/{h}"
    try:
        req = urllib.request.Request(url)
        resp = urllib.request.urlopen(req, timeout=15)
        data = resp.read()
        print(f"  OK ({len(data)} bytes): {url}")
        break
    except urllib.error.HTTPError as e:
        print(f"  HTTP {e.code}: {url}")
    except Exception as e:
        print(f"  Error: {e}")

db.close()
