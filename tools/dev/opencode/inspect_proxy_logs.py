import sqlite3, json

conn = sqlite3.connect(r'C:\Users\Ota\.omniroute\storage.sqlite')
cur = conn.cursor()

cur.execute("PRAGMA table_info(proxy_logs)")
cols = [c[1] for c in cur.fetchall()]
print("proxy_logs columns:", cols)

cur.execute("SELECT * FROM proxy_logs ORDER BY timestamp DESC LIMIT 10")
for r in cur.fetchall():
    row_dict = dict(zip(cols, r))
    print("\nProxy Log:", {k: v for k, v in row_dict.items() if v is not None and k not in ('request_body', 'response_body')})

print("\n=== REQUEST DETAIL LOGS ===")
cur.execute("PRAGMA table_info(request_detail_logs)")
rd_cols = [c[1] for c in cur.fetchall()]
cur.execute("SELECT * FROM request_detail_logs ORDER BY id DESC LIMIT 10")
for r in cur.fetchall():
    print(dict(zip(rd_cols, r)))

conn.close()
