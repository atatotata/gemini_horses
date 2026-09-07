#!/usr/bin/env python3
"""Probe Global meta using hachimi-tools MetaDb approach."""
import sys
sys.path.insert(0, r"G:\Games\steamapps\common\UmamusumePrettyDerby_Jpn\gemini_horses\tools\hachimi-tools")

from meta_db_lib import MetaDb

# Global meta
global_meta_path = r"G:\Games\steamapps\common\UmamusumePrettyDerby\UmamusumePrettyDerby_Data\Persistent\meta"
print("=== Global Meta ===")
try:
    db = MetaDb(global_meta_path, key="A713A5C79DBC9497C0A88669")
    # List tables
    tables = [r[0] for r in db.db.execute("SELECT name FROM sqlite_master WHERE type='table'")]
    print(f"Tables: {tables}")
    for t in tables:
        count = db.db.execute(f"SELECT COUNT(*) FROM [{t}]").fetchone()[0]
        desc = db.db.execute(f"PRAGMA table_info([{t}])").fetchall()
        cols = [d[1] for d in desc]
        print(f"  {t}: {count} rows, cols={cols}")
    db.close()
except Exception as e:
    print(f"Error: {e}")

# JP meta for reference
jp_meta_path = r"G:\Games\steamapps\common\UmamusumePrettyDerby_Jpn\UmamusumePrettyDerby_Jpn_Data\Persistent\meta"
print("\n=== JP Meta ===")
try:
    db = MetaDb(jp_meta_path)
    tables = [r[0] for r in db.db.execute("SELECT name FROM sqlite_master WHERE type='table'")]
    print(f"Tables: {tables}")
    for t in tables:
        count = db.db.execute(f"SELECT COUNT(*) FROM [{t}]").fetchone()[0]
        desc = db.db.execute(f"PRAGMA table_info([{t}])").fetchall()
        cols = [d[1] for d in desc]
        print(f"  {t}: {count} rows, cols={cols}")
    db.close()
except Exception as e:
    print(f"Error: {e}")
