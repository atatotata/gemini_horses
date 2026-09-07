#!/usr/bin/env python3
"""Probe meta database for story/data gap files."""
import apsw
import os

DB_PATH = r"C:\TMP\meta_fresh.bin"
DB_KEY = "9c2bab97bcf8c0c4f1a9ea7881a213f6c9eb7e9fd"
PREFIXES = ["50", "40", "11", "80", "83"]

db = apsw.Connection(DB_PATH, flags=apsw.SQLITE_OPEN_READONLY)
db.execute(f"PRAGMA key = 'x\"{DB_KEY}\"'")

# Count total rows
cur = db.execute("SELECT count(*) FROM a")
print(f"Total rows: {cur.fetchone()[0]}")

# Sample a row to see structure
cur = db.execute("SELECT * FROM a LIMIT 1")
row = cur.fetchone()
if row:
    cur2 = db.execute("PRAGMA table_info(a)")
    cols = [r[1] for r in cur2]
    print(f"Columns: {cols}")
    print(f"Sample: {dict(zip(cols, row))}")

# Count meta entries per prefix
for pfx in PREFIXES:
    like_pat = f"story/data/{pfx}/%"
    cur = db.execute("SELECT count(*) FROM a WHERE n LIKE ?", (like_pat,))
    cnt = cur.fetchone()[0]
    like_pat2 = f"story/data/{pfx}/%/storytimeline_%"
    cur2 = db.execute("SELECT count(*) FROM a WHERE n LIKE ?", (like_pat2,))
    cnt2 = cur2.fetchone()[0]
    print(f"Prefix {pfx}: total={cnt}, storytimeline={cnt2}")

db.close()
