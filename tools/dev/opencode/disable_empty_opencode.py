import sqlite3

conn = sqlite3.connect(r'C:\Users\Ota\.omniroute\storage.sqlite')
cur = conn.cursor()

# Check current state of 'opencode' provider
cur.execute("SELECT id, provider, name, is_active, api_key FROM provider_connections WHERE provider = 'opencode'")
rows = cur.fetchall()
print("BEFORE:")
for r in rows:
    print(r)

# Deactivate unkeyed 'opencode' provider
cur.execute("UPDATE provider_connections SET is_active = 0 WHERE provider = 'opencode' AND (api_key IS NULL OR api_key = '')")
conn.commit()

# Verify
cur.execute("SELECT id, provider, name, is_active, api_key FROM provider_connections WHERE provider = 'opencode'")
rows = cur.fetchall()
print("\nAFTER:")
for r in rows:
    print(r)

conn.close()
print("\nSuccessfully disabled unkeyed 'opencode' provider.")
