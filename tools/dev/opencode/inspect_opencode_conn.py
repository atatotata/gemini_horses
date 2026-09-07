import sqlite3, json

conn = sqlite3.connect(r'C:\Users\Ota\.omniroute\storage.sqlite')
cur = conn.cursor()

cur.execute("""
SELECT id, provider, auth_type, name, is_active, api_key, access_token, refresh_token, 
       provider_specific_data, last_error, default_model
FROM provider_connections
WHERE provider LIKE '%opencode%' OR provider LIKE '%go%'
""")

cols = [c[0] for c in cur.description]
for r in cur.fetchall():
    d = dict(zip(cols, r))
    # mask sensitive strings
    if d['api_key']:
        d['api_key'] = d['api_key'][:6] + '...' + d['api_key'][-4:]
    if d['access_token']:
        d['access_token'] = d['access_token'][:6] + '...' + d['access_token'][-4:]
    print(json.dumps(d, indent=2))

conn.close()
