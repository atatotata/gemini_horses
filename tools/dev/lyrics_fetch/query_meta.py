#!/usr/bin/env python3
"""Query live_data and find lyrics/storyrace entries in master.mdb."""
import apsw
import os

MASTER_MDB = r"G:\Games\steamapps\common\UmamusumePrettyDerby_Jpn\UmamusumePrettyDerby_Jpn_Data\Persistent\master\master.mdb"
DAT_DIR = r"G:\Games\steamapps\common\UmamusumePrettyDerby_Jpn\UmamusumePrettyDerby_Jpn_Data\Persistent\dat"
LOCAL_LYRICS_DIR = r"G:\Games\steamapps\common\UmamusumePrettyDerby_Jpn\gemini_horses\localized_data\assets\lyrics"
LOCAL_STORYRACE_DIR = r"G:\Games\steamapps\common\UmamusumePrettyDerby_Jpn\gemini_horses\localized_data\assets\race\storyrace\text"

conn = apsw.Connection(MASTER_MDB)
cursor = conn.cursor()

# Check live_data table
print("=== live_data ===")
cols = [r[1] for r in cursor.execute("PRAGMA table_info(live_data)")]
print("Columns:", cols)
rows = list(cursor.execute("SELECT * FROM live_data LIMIT 3"))
for r in rows:
    print(r)

# Check for lyrics-related entries - the name in the DB is likely an asset bundle path
# Look for anything containing 'lyrics' in any text column
print("\n=== Searching for lyrics entries ===")
# Search across all columns that might contain 'lyrics'
for col_name in cols:
    try:
        rows = list(cursor.execute(f"SELECT * FROM live_data WHERE CAST({col_name} AS TEXT) LIKE '%lyrics%' LIMIT 5"))
        if rows:
            print(f"Found in column {col_name}:")
            for r in rows:
                print(r)
    except:
        pass

print("\n=== live_permission_data ===")
cols2 = [r[1] for r in cursor.execute("PRAGMA table_info(live_permission_data)")]
print("Columns:", cols2)

# Count lyrics
count = list(cursor.execute("SELECT COUNT(*) FROM live_data"))
print(f"live_data count: {count}")
count2 = list(cursor.execute("SELECT COUNT(*) FROM live_permission_data"))
print(f"live_permission_data count: {count2}")

conn.close()
