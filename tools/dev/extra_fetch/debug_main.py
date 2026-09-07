#!/usr/bin/env python3
"""Debug: trace exactly what main script does."""
import apsw
import json
import time
import urllib.request
import urllib.error
from pathlib import Path

META_PATH = Path(r"G:\Games\steamapps\common\UmamusumePrettyDerby_Jpn\UmamusumePrettyDerby_Jpn_Data\Persistent\meta")
MASTER_PATH = Path(r"G:\Games\steamapps\common\UmamusumePrettyDerby_Jpn\UmamusumePrettyDerby_Jpn_Data\Persistent\master\master.mdb")
LOCALIZED_BASE = Path(r"G:\Games\steamapps\common\UmamusumePrettyDerby_Jpn\gemini_horses\localized_data\assets\story\data")
OUT_BASE = Path(r"C:\TMP\extra_fetch\story_json")
DB_KEY = "9c2bab97bcf8c0c4f1a9ea7881a213f6c9ebf9d8d4c6a8e43ce5a259bde7e9fd"
CDN_URL = "https://prd-storage-game-umamusume.akamaized.net/dl/resources/{}/assetbundles/{}/{}"

uri = f"file:{META_PATH}?hexkey={DB_KEY}"
meta_db = apsw.Connection(uri, flags=apsw.SQLITE_OPEN_READONLY | apsw.SQLITE_OPEN_URI)
cur = meta_db.cursor()

# Get platform
first_row = cur.execute("SELECT n FROM a LIMIT 1").fetchone()
print(f"First row n: {first_row[0]}")
platform = first_row[0][2:6] if first_row[0].startswith("dat/") else "Windows"
print(f"Platform detected: '{platform}'")

# Get a test SID's hash
row = cur.execute("SELECT n, h, e FROM a WHERE n = 'story/data/09/0009/storytimeline_090009001'").fetchone()
n, h, e = row
prefix = h[:2]
url = CDN_URL.format(platform, prefix, h)
print(f"Test URL: {url}")

try:
    req = urllib.request.Request(url)
    resp = urllib.request.urlopen(req, timeout=15)
    data = resp.read()
    print(f"  Downloaded: {len(data)} bytes")
except urllib.error.HTTPError as exc:
    print(f"  HTTP {exc.code}: {exc.reason}")
except Exception as exc:
    print(f"  Error: {exc}")

meta_db.close()
