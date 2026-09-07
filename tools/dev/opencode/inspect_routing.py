import sqlite3, json

conn = sqlite3.connect(r'C:\Users\Ota\.omniroute\storage.sqlite')
cur = conn.cursor()

print("=== REGISTERED KEYS ===")
cur.execute("SELECT * FROM registered_keys")
for r in cur.fetchall():
    print(r)

print("\n=== MODEL COMBO MAPPINGS ===")
cur.execute("SELECT * FROM model_combo_mappings")
for r in cur.fetchall():
    print(r)

print("\n=== MODEL CAPABILITY OVERRIDES ===")
cur.execute("SELECT * FROM model_capability_overrides")
for r in cur.fetchall():
    print(r)

print("\n=== RECENT ROUTING DECISIONS ===")
cur.execute("SELECT * FROM routing_decisions ORDER BY id DESC LIMIT 10")
for r in cur.fetchall():
    print(r)

conn.close()
