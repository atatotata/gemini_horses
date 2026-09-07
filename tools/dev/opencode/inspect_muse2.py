import sqlite3

conn = sqlite3.connect(r'C:\Users\Ota\.omniroute\storage.sqlite')
cur = conn.cursor()

cur.execute("""
SELECT timestamp, status, model, requested_model, provider, error_summary
FROM call_logs
WHERE model LIKE '%muse-spark-1.3%' OR requested_model LIKE '%muse-spark-1.3%'
ORDER BY timestamp DESC LIMIT 50
""")
for r in cur.fetchall():
    err = (r[5][:300] + '...') if r[5] and len(r[5]) > 300 else (r[5] or 'OK')
    err = err.replace('\u2014', '-').replace('\u2013', '-')
    print(repr(f"[{r[0]}] {r[1]} | {r[2]} | {r[3]} | {r[4]} | {err}"))

cur.execute("""
SELECT timestamp, status, model, requested_model, provider, error_summary
FROM call_logs
WHERE status IN (402,429)
ORDER BY timestamp DESC LIMIT 30
""")
print("\n--- 402/429 ---")
for r in cur.fetchall():
    err = (r[5][:600] + '...') if r[5] and len(r[5]) > 600 else (r[5] or '')
    err = err.replace('\u2014', '-').replace('\u2013', '-')
    print(repr(f"[{r[0]}] {r[1]} | {r[2]} ({r[3]}) | {r[4]} | {err[:400]}"))

conn.close()
