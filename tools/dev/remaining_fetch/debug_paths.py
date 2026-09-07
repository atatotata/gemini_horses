#!/usr/bin/env python3
"""Debug: compare meta paths vs localized paths."""
import apsw
import os

DB_URI = r"file:C:\TMP\meta_fresh.bin?hexkey=9c2bab97bcf8c0c4f1a9ea7881a213f6c9ebf9d8d4c6a8e43ce5a259bde7e9fd"
LOCALIZED_BASE = r"G:\Games\steamapps\common\UmamusumePrettyDerby_Jpn\gemini_horses\localized_data\assets\story\data"

db = apsw.Connection(DB_URI, flags=apsw.SQLITE_OPEN_READONLY | apsw.SQLITE_OPEN_URI)

# Sample meta paths for prefix 50
print("=== META PATHS (50) ===")
cur = db.execute("SELECT n FROM a WHERE n LIKE 'story/data/50/%/storytimeline_%' LIMIT 5")
for r in cur:
    print(r[0])

# Sample localized paths for prefix 50
print("\n=== LOCALIZED PATHS (50) ===")
pfx_dir = os.path.join(LOCALIZED_BASE, "50")
subs = sorted(os.listdir(pfx_dir))[:5]
for sub in subs:
    sub_dir = os.path.join(pfx_dir, sub)
    if os.path.isdir(sub_dir):
        fns = sorted(os.listdir(sub_dir))[:3]
        for fn in fns:
            rel = f"story/data/50/{sub}/{fn}"
            print(rel)

# Sample meta paths for prefix 11
print("\n=== META PATHS (11) ===")
cur = db.execute("SELECT n FROM a WHERE n LIKE 'story/data/11/%/storytimeline_%' LIMIT 5")
for r in cur:
    print(r[0])

# Sample localized paths for prefix 11
print("\n=== LOCALIZED PATHS (11) ===")
pfx_dir = os.path.join(LOCALIZED_BASE, "11")
if os.path.isdir(pfx_dir):
    subs = sorted(os.listdir(pfx_dir))[:5]
    for sub in subs:
        sub_dir = os.path.join(pfx_dir, sub)
        if os.path.isdir(sub_dir):
            fns = sorted(os.listdir(sub_dir))[:3]
            for fn in fns:
                rel = f"story/data/11/{sub}/{fn}"
                print(rel)
else:
    print("No dir for 11")

db.close()
