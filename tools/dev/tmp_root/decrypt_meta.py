#!/usr/bin/env python3
"""Re-decrypt Persistent/meta and query story data coverage."""
import apsw
import json
import sys
import os
from pathlib import Path

tmp = r'C:\TMP\meta_copy.bin'
db_key = '9c2bab97bcf8c0c4f1a9ea7881a213f6c9ebf9d8d4c6a8e43ce5a259bde7e9fd'

print(f"=== Step 1: Open meta with hexkey {db_key[:16]}... ===")
uri = f'file:{tmp}?hexkey={db_key}'
db = apsw.Connection(uri, flags=apsw.SQLITE_OPEN_READONLY | apsw.SQLITE_OPEN_URI)
cur = db.cursor()

count = cur.execute('SELECT COUNT(*) FROM a').fetchone()
print(f"Total meta rows: {count[0]}")

# Count story/timeline entries by prefix
prefix_counts = {}
for row in cur.execute("SELECT n FROM a WHERE n LIKE 'story/data/%/storytimeline_%'"):
    n = row[0]
    parts = n.split('/')
    # story/data/{prefix}/.../storytimeline_{id}
    # path format: story/data/XX/XXXX/storytimeline_XXXXXXXXX
    # prefix is parts[2]  (the first subdir after data/)
    if len(parts) >= 4:
        prefix = parts[2]
        prefix_counts[prefix] = prefix_counts.get(prefix, 0) + 1

print("\n=== Story timeline entries by prefix (meta) ===")
for p in sorted(prefix_counts.keys()):
    print(f"  prefix {p}: {prefix_counts[p]}")

# All story/data paths with n, h, e columns
print("\n=== Sample rows (n, h, e) for story/data ===")
for i, row in enumerate(cur.execute("SELECT n, h, e FROM a WHERE n LIKE 'story/data/%' LIMIT 5")):
    print(f"  n={row[0]}, h={row[1]}, e={row[2]}")

# Also check what story/data paths exist by full structure
print("\n=== story/data structure sample ===")
for row in cur.execute("SELECT n FROM a WHERE n LIKE 'story/data/%' LIMIT 20"):
    print(f"  {row[0]}")

db.close()
print("\n=== Meta opened successfully! ===")
