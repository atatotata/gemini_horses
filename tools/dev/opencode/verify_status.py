import sqlite3, json

conn = sqlite3.connect(r'C:\Users\Ota\.omniroute\storage.sqlite')
cur = conn.cursor()

print("=== databaseSettings ===")
cur.execute("SELECT key, value FROM key_value WHERE namespace='databaseSettings' ORDER BY key")
for k,v in cur.fetchall():
    print(f"  {k}: {v}")

print("\n=== compression (core) ===")
core_keys = ['enabled','defaultMode','autoTriggerMode','autoTriggerTokens','preserveSystemPrompt','preserveToolDefinitions','disableMessageAging','engines','outputStyles','ultra','ultraEngine','ultraSlmPrewarm']
for k in core_keys:
    cur.execute("SELECT value FROM key_value WHERE namespace='compression' AND key=?", (k,))
    row = cur.fetchone()
    val = row[0] if row else "MISSING"
    if len(val) > 400:
        val = val[:400] + "..."
    print(f"  {k}: {val}")

print("\n=== rtkConfig ===")
cur.execute("SELECT value FROM key_value WHERE namespace='compression' AND key='rtkConfig'")
row = cur.fetchone()
if row:
    print(json.dumps(json.loads(row[0]), indent=2))

print("\n=== cavemanConfig ===")
cur.execute("SELECT value FROM key_value WHERE namespace='compression' AND key='cavemanConfig'")
row = cur.fetchone()
if row:
    print(json.dumps(json.loads(row[0]), indent=2))

print("\n=== sessionDedup ===")
cur.execute("SELECT value FROM key_value WHERE namespace='compression' AND key='sessionDedup'")
row = cur.fetchone()
if row:
    print(json.dumps(json.loads(row[0]), indent=2))

print("\n=== provider_connections ===")
cur.execute("SELECT provider, name, is_active, CASE WHEN api_key IS NULL OR api_key='' THEN 0 ELSE 1 END as has_key, test_status FROM provider_connections ORDER BY provider")
for r in cur.fetchall():
    print(f"  {r[0]:20} | {r[1]:25} | active={r[2]} | has_key={r[3]} | test={r[4]}")

print("\n=== omniroute.json exists ===")
import os
print(os.path.exists(r"C:\Users\Ota\.omniroute\omniroute.json"))

conn.close()
