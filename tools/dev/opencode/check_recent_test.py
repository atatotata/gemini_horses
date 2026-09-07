import sqlite3, json

conn = sqlite3.connect(r'C:\Users\Ota\.omniroute\storage.sqlite')
cur = conn.cursor()

cur.execute("""
SELECT timestamp, status, model, requested_model, provider, error_summary, artifact_relpath
FROM call_logs
ORDER BY timestamp DESC LIMIT 5
""")

for r in cur.fetchall():
    print(f"[{r[0]}] status={r[1]} | model={r[2]} | req={r[3]} | prov={r[4]}")
    print(f"  error: {r[5]}")
    print(f"  artifact: {r[6]}")

conn.close()
