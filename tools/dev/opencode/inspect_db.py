import sqlite3, json

conn = sqlite3.connect(r'C:\Users\Ota\.omniroute\storage.sqlite')
cur = conn.cursor()

# Get all tables
cur.execute("SELECT name FROM sqlite_master WHERE type='table'")
tables = [t[0] for t in cur.fetchall()]
print("Tables in storage.sqlite:", tables)

# Check each table schema and row count
for table in tables:
    cur.execute(f"SELECT COUNT(*) FROM {table}")
    count = cur.fetchone()[0]
    print(f"\nTable {table}: {count} rows")
    if table != 'key_value':
        cur.execute(f"PRAGMA table_info({table})")
        cols = [c[1] for c in cur.fetchall()]
        print(f"  Columns: {cols}")
        cur.execute(f"SELECT * FROM {table} LIMIT 5")
        for row in cur.fetchall():
            print("  Row:", row[:3], "... (truncated)" if len(row) > 3 else "")

conn.close()
