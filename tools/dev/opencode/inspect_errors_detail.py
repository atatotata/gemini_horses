import sqlite3, json

conn = sqlite3.connect(r'C:\Users\Ota\.omniroute\storage.sqlite')
cur = conn.cursor()

cur.execute("PRAGMA table_info(call_logs)")
cols = [c[1] for c in cur.fetchall()]

cur.execute(f"""
SELECT {', '.join(cols)}
FROM call_logs
WHERE status >= 400 OR error_summary IS NOT NULL
ORDER BY timestamp DESC
LIMIT 20
""")

for r in cur.fetchall():
    d = dict(zip(cols, r))
    summary = {
        'timestamp': d.get('timestamp'),
        'status': d.get('status'),
        'model': d.get('model'),
        'requested_model': d.get('requested_model'),
        'provider': d.get('provider'),
        'error_summary': d.get('error_summary'),
        'error_type': d.get('error_type'),
        'account': d.get('account')
    }
    print(json.dumps(summary, default=str))

conn.close()
