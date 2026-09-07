import sqlite3, json

conn = sqlite3.connect(r'C:\Users\Ota\.omniroute\storage.sqlite')
cur = conn.cursor()

print("=== PROVIDER CONNECTIONS ===")
cur.execute("""
SELECT id, provider, auth_type, name, is_active, test_status, error_code, last_error, last_error_at, 
       length(api_key), length(access_token), length(refresh_token), default_model
FROM provider_connections
""")
for r in cur.fetchall():
    print(f"Provider: {r[1]} | Name: {r[3]} | Auth: {r[2]} | Active: {r[4]} | Test: {r[5]} | ErrCode: {r[6]} | Err: {r[7]} | ErrAt: {r[8]} | HasKey: {bool(r[9])} | HasToken: {bool(r[10])} | HasRefresh: {bool(r[11])} | DefModel: {r[12]}")

print("\n=== RECENT FAILED CALL LOGS / PROXY LOGS ===")
cur.execute("""
SELECT timestamp, path, model, requested_model, provider, status, error_summary, error_type
FROM proxy_logs
ORDER BY timestamp DESC
LIMIT 15
""")
for r in cur.fetchall():
    print(f"[{r[0]}] Model: {r[2]} ({r[3]}) | Prov: {r[4]} | Status: {r[5]} | Err: {r[6]} | Type: {r[7]}")

print("\n=== RECENT CALL LOGS ===")
cur.execute("""
SELECT timestamp, provider, model, status, success, error_code, latency_ms, endpoint
FROM call_logs
ORDER BY timestamp DESC
LIMIT 15
""")
for r in cur.fetchall():
    print(f"[{r[0]}] Prov: {r[1]} | Model: {r[2]} | Status: {r[3]} | Success: {r[4]} | ErrCode: {r[5]} | Latency: {r[6]}ms | Endpoint: {r[7]}")

conn.close()
