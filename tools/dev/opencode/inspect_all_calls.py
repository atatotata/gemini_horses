import sqlite3

conn = sqlite3.connect(r'C:\Users\Ota\.omniroute\storage.sqlite')
cur = conn.cursor()

print("=== CALL LOGS ===")
cur.execute("PRAGMA table_info(call_logs)")
cols = [c[1] for c in cur.fetchall()]
cur.execute(f"SELECT {', '.join(cols)} FROM call_logs ORDER BY timestamp DESC LIMIT 20")
for r in cur.fetchall():
    print(dict(zip(cols, r)))

print("\n=== REQUEST DETAIL LOGS ===")
cur.execute("PRAGMA table_info(request_detail_logs)")
rd_cols = [c[1] for c in cur.fetchall()]
cur.execute(f"SELECT {', '.join(rd_cols)} FROM request_detail_logs ORDER BY id DESC LIMIT 20")
for r in cur.fetchall():
    d = dict(zip(rd_cols, r))
    filtered = {k: v for k, v in d.items() if v is not None and k not in ('request_body', 'response_body', 'artifact_relpath')}
    print(filtered)

conn.close()
