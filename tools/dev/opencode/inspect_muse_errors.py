import sqlite3, json

conn = sqlite3.connect(r'C:\Users\Ota\.omniroute\storage.sqlite')
cur = conn.cursor()

print("=== PROVIDER CONNECTIONS ===")
cur.execute("SELECT provider, name, is_active, test_status, last_error FROM provider_connections ORDER BY provider")
for r in cur.fetchall():
    print(f"{r[0]:22} | {r[1]:25} | active={r[2]} | test={r[3]} | err={str(r[4])[:180] if r[4] else ''}")

print("\n=== RECENT CALL LOGS FOR muse-spark 1.2/1.3 ===")
cur.execute("""
SELECT timestamp, status, model, requested_model, provider, account, error_summary, duration
FROM call_logs
WHERE model LIKE '%muse-spark%' OR requested_model LIKE '%muse-spark%'
ORDER BY timestamp DESC LIMIT 40
""")
for r in cur.fetchall():
    print(f"[{r[0]}] status={r[1]} | model={r[2]} | req={r[3]} | prov={r[4]} | acct={r[5]} | err={str(r[6])[:300] if r[6] else 'OK'} | dur={r[7]}")

print("\n=== MOST RECENT 402 and 429 ERRORS ===")
cur.execute("""
SELECT timestamp, status, model, requested_model, provider, error_summary
FROM call_logs
WHERE status IN (402,429)
ORDER BY timestamp DESC LIMIT 20
""")
for r in cur.fetchall():
    print(f"[{r[0]}] {r[1]} | {r[2]} ({r[3]}) | {r[4]} | {str(r[5])[:500]}")

conn.close()
