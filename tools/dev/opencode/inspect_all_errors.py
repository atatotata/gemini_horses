import sqlite3, json

conn = sqlite3.connect(r'C:\Users\Ota\.omniroute\storage.sqlite')
cur = conn.cursor()

cur.execute("""
SELECT timestamp, status, model, requested_model, provider, error_summary
FROM call_logs
WHERE status >= 400
ORDER BY timestamp DESC
LIMIT 50
""")

rows = cur.fetchall()
print(f"Total error logs found: {len(rows)}")
for r in rows:
    print(f"[{r[0]}] Status: {r[1]} | Prov: {r[4]} | ReqModel: {r[3]} | Error: {r[5]}")

conn.close()
