#!/usr/bin/env python3
"""Probe Global master.mdb to understand table structure."""
import apsw
import sqlite3

db_path = r"G:\Games\steamapps\common\UmamusumePrettyDerby\UmamusumePrettyDerby_Data\Persistent\master\master.mdb"

print("=== Attempting Global master.mdb ===")

# Try without encryption first
try:
    conn = apsw.Connection(db_path)
    tables = [row[0] for row in conn.execute("SELECT name FROM sqlite_master WHERE type='table'")]
    print(f"Found {len(tables)} tables (unencrypted):")
    for t in sorted(tables):
        print(f"  {t}")
    
    # Check if text_data exists
    if "text_data" in tables:
        count = conn.execute("SELECT COUNT(*) FROM text_data").fetchone()[0]
        print(f"\ntext_data row count: {count}")
        # Sample rows
        print("Sample text_data rows (first 5):")
        for row in conn.execute("SELECT * FROM text_data LIMIT 5"):
            print(f"  {row}")
        # Check categories
        cats = [r[0] for r in conn.execute("SELECT DISTINCT category FROM text_data ORDER BY category")]
        print(f"Categories in text_data: {cats}")
    
    if "character_system_text" in tables:
        count = conn.execute("SELECT COUNT(*) FROM character_system_text").fetchone()[0]
        print(f"\ncharacter_system_text row count: {count}")
        print("Sample character_system_text rows (first 3):")
        for row in conn.execute("SELECT * FROM character_system_text LIMIT 3"):
            print(f"  {row}")
    
    conn.close()
except Exception as e:
    print(f"Unencrypted failed: {e}")
    
    # Try with global hexkey
    try:
        DB_KEY_GLOBAL = "A713A5C79DBC9497C0A88669"
        uri = f"file:{db_path}?hexkey={DB_KEY_GLOBAL}"
        conn = apsw.Connection(uri, flags=apsw.SQLITE_OPEN_READONLY)
        conn.pragma("cipher", "chacha20")
        conn.pragma("hexkey", DB_KEY_GLOBAL)
        tables = [row[0] for row in conn.execute("SELECT name FROM sqlite_master WHERE type='table'")]
        print(f"Found {len(tables)} tables (with global key):")
        for t in sorted(tables):
            print(f"  {t}")
        conn.close()
    except Exception as e2:
        print(f"Global key also failed: {e2}")

# Also probe JP master.mdb for comparison
print("\n=== JP master.mdb (reference) ===")
jp_path = r"G:\Games\steamapps\common\UmamusumePrettyDerby_Jpn\UmamusumePrettyDerby_Jpn_Data\Persistent\master\master.mdb"
try:
    conn = apsw.Connection(jp_path)
    tables = [row[0] for row in conn.execute("SELECT name FROM sqlite_master WHERE type='table'")]
    print(f"Found {len(tables)} tables (unencrypted):")
    for t in sorted(tables)[:20]:
        print(f"  {t}")
    if "text_data" in tables:
        count = conn.execute("SELECT COUNT(*) FROM text_data").fetchone()[0]
        print(f"\ntext_data row count: {count}")
        cats = [r[0] for r in conn.execute("SELECT DISTINCT category FROM text_data ORDER BY category")]
        print(f"Categories in text_data: {cats}")
    conn.close()
except Exception as e:
    print(f"JP also failed: {e}")
