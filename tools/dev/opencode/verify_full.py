import sqlite3, json, os

conn = sqlite3.connect(r'C:\Users\Ota\.omniroute\storage.sqlite')
cur = conn.cursor()

print("===== databaseSettings =====")
cur.execute("SELECT key, value FROM key_value WHERE namespace='databaseSettings' ORDER BY key")
for k,v in cur.fetchall():
    try:
        pv = json.loads(v)
        print(f"  {k}: {pv} (raw: {v})")
    except:
        print(f"  {k}: {v}")

print("\n===== compression core =====")
core = ['enabled','defaultMode','autoTriggerMode','autoTriggerTokens','preserveSystemPrompt','preserveToolDefinitions','disableMessageAging','engines','outputStyles','ultra']
for k in core:
    cur.execute("SELECT value FROM key_value WHERE namespace='compression' AND key=?", (k,))
    r = cur.fetchone()
    if r:
        try:
            j = json.loads(r[0])
            print(f"  {k}: {json.dumps(j, indent=4)}")
        except:
            print(f"  {k}: {r[0]}")
    else:
        print(f"  {k}: MISSING")

print("\n===== rtkConfig =====")
cur.execute("SELECT value FROM key_value WHERE namespace='compression' AND key='rtkConfig'")
r = cur.fetchone()
if r: print(json.dumps(json.loads(r[0]), indent=2))

print("\n===== cavemanConfig =====")
cur.execute("SELECT value FROM key_value WHERE namespace='compression' AND key='cavemanConfig'")
r = cur.fetchone()
if r: print(json.dumps(json.loads(r[0]), indent=2))

print("\n===== sessionDedup =====")
cur.execute("SELECT value FROM key_value WHERE namespace='compression' AND key='sessionDedup'")
r = cur.fetchone()
if r: print(json.dumps(json.loads(r[0]), indent=2))

print("\n===== cavemanOutputMode / ultraSlmPrewarm =====")
for k in ['cavemanOutputMode','ultraSlmPrewarm','ultraEngine','sessionDedup','ccr','lite','headroom','codexResponsesConfig']:
    cur.execute("SELECT value FROM key_value WHERE namespace='compression' AND key=?", (k,))
    r = cur.fetchone()
    if r:
        try: print(f"  {k}: {json.dumps(json.loads(r[0]))}")
        except: print(f"  {k}: {r[0]}")

print("\n===== provider_connections =====")
cur.execute("SELECT provider, name, is_active, CASE WHEN api_key IS NULL OR api_key='' THEN 0 ELSE 1 END as has_key, test_status, last_error FROM provider_connections ORDER BY provider")
for row in cur.fetchall():
    print(f"  {row[0]:20} | {row[1]:25} | active={row[2]} | has_key={row[3]} | test={row[4]} | err={row[5]}")

print("\n===== daemon health =====")
import urllib.request, urllib.error
try:
    req = urllib.request.urlopen("http://localhost:20128/v1/models", timeout=5)
    print(f"  HTTP {req.status} - daemon alive")
except urllib.error.HTTPError as e:
    print(f"  HTTP {e.code} - daemon alive (auth required = healthy)")
except Exception as e:
    print(f"  FAILED: {e}")

print(f"\n===== omniroute.json exists: {os.path.exists(r'C:\Users\Ota\.omniroute\omniroute.json')} =====")
if os.path.exists(r"C:\Users\Ota\.omniroute\omniroute.json"):
    import pathlib
    print(open(r"C:\Users\Ota\.omniroute\omniroute.json").read()[:1200])

conn.close()
