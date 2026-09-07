import sqlite3, json

conn = sqlite3.connect(r'C:\Users\Ota\.omniroute\storage.sqlite')
cur = conn.cursor()

cur.execute("""
SELECT id, timestamp, status, model, requested_model, provider, error_summary, duration
FROM call_logs
ORDER BY id DESC LIMIT 10
""")

for r in cur.fetchall():
    print(dict(zip(['id', 'timestamp', 'status', 'model', 'requested_model', 'provider', 'error_summary', 'duration'], r)))

conn.close()
