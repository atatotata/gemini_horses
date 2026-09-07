#!/usr/bin/env python3
"""Re-decrypt Persistent/meta correctly and query story data coverage."""
import apsw
import json
import os
import sqlite3
from pathlib import Path

# === KEYS ===
# From meta_db_lib.py for Japanese version:
HACHIMI_DB_KEY = "9c2bab97bcf8c0c4f1a9ea7881a213f6c9ebf9d8d4c6a8e43ce5a259bde7e9fd"

# Derived from task spec (baseKey XOR plainKey):
base_hex = "f170cea4dfcea3e1a5d8c70bd1"
plain_hex = "6d5b65336336632554712d73505363386d34377b356370233734532973433633"
base = bytes.fromhex(base_hex)
plain = bytes.fromhex(plain_hex)
final_key = bytes([plain[i] ^ base[i % len(base)] for i in range(len(plain))])
derived_hexkey = final_key.hex()

print(f"Hachimi DB_KEY prefix: {HACHIMI_DB_KEY[:20]}...")
print(f"Derived hexkey prefix: {derived_hexkey[:20]}...")

tmp = r'C:\TMP\meta_copy.bin'

# === STEP 1: Try opening meta with various keys ===
def try_open_meta(path, hexkey, label):
    try:
        uri = f'file:{path}?hexkey={hexkey}'
        db = apsw.Connection(uri, flags=apsw.SQLITE_OPEN_READONLY | apsw.SQLITE_OPEN_URI)
        cur = db.cursor()
        count = cur.execute('SELECT COUNT(*) FROM a').fetchone()
        print(f"\nSUCCESS with {label}: {count[0]} rows")
        return db
    except Exception as e:
        print(f"Failed with {label}: {e}")
        return None

# Try each key
for key, label in [
    (HACHIMI_DB_KEY, "hachimi DB_KEY"),
    (derived_hexkey, "derived XOR key"),
]:
    db = try_open_meta(tmp, key, label)
    if db:
        break

if not db:
    print("\nERROR: Could not open meta with any key!")
    exit(1)

cur = db.cursor()

# === Query meta ===
print("\n=== Meta total row count ===")
total = cur.execute('SELECT COUNT(*) FROM a').fetchone()[0]
print(f"Total rows: {total}")

# Get schema
print("\n=== Table 'a' schema ===")
for row in cur.execute("PRAGMA table_info(a)"):
    print(f"  col {row[1]} ({row[2]})")

# Count story/timeline entries by prefix
prefix_counts = {}
story_rows = []
for row in cur.execute("SELECT n, h, e FROM a WHERE n LIKE 'story/data/%'"):
    n, h, e = row
    parts = n.split('/')
    # Expected: story/data/XX/XXXX/storytimeline_XXXXXXXXX
    if len(parts) >= 4 and 'storytimeline_' in parts[-1]:
        prefix = parts[2]
        prefix_counts[prefix] = prefix_counts.get(prefix, 0) + 1
        story_rows.append((n, h, e, prefix))

print("\n=== Story timeline entries by prefix (meta) ===")
for p in sorted(prefix_counts.keys()):
    print(f"  prefix {p}: {prefix_counts[p]}")

# Show some sample rows
print("\n=== Sample rows (n, h, e) for first 5 ===")
for n, h, e, _ in story_rows[:5]:
    print(f"  n={n}, h={h}, e={e}")

db.close()
print("\n=== Done step 1 ===")
