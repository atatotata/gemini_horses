#!/usr/bin/env python3
"""Probe Global meta DB and check for story/home/lyrics assets."""
import apsw

db_path = r"G:\Games\steamapps\common\UmamusumePrettyDerby\UmamusumePrettyDerby_Data\Persistent\meta"
DB_KEY_GLOBAL = "A713A5C79DBC9497C0A88669"

try:
    uri = f"file:{db_path}?hexkey={DB_KEY_GLOBAL}"
    conn = apsw.Connection(uri, flags=apsw.SQLITE_OPEN_READONLY)
    conn.pragma("cipher", "chacha20")
    conn.pragma("hexkey", DB_KEY_GLOBAL)
    tables = [r[0] for r in conn.execute("SELECT name FROM sqlite_master WHERE type='table'")]
    print(f"Meta tables ({len(tables)}): {tables}")
    for t in tables[:3]:
        count = conn.execute(f"SELECT COUNT(*) FROM [{t}]").fetchone()[0]
        desc = conn.execute(f"PRAGMA table_info([{t}])").fetchall()
        cols = [d[1] for d in desc]
        print(f"  {t}: {count} rows, cols={cols}")
        # Sample
        for r in conn.execute(f"SELECT * FROM [{t}] LIMIT 2"):
            print(f"    {r}")
    conn.close()
except Exception as e:
    print(f"Error: {e}")
    # Try unencrypted
    try:
        conn = apsw.Connection(db_path)
        tables = [r[0] for r in conn.execute("SELECT name FROM sqlite_master WHERE type='table'")]
        print(f"Unencrypted meta tables: {tables}")
    except Exception as e2:
        print(f"Unencrypted also failed: {e2}")
