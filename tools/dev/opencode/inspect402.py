import sqlite3, json, os, re
conn = sqlite3.connect(r'C:\Users\Ota\.omniroute\storage.sqlite')
cur = conn.cursor()

print("=== 402 errors (402 payment/balance) ===")
cur.execute("SELECT timestamp, status, model, requested_model, provider, error_summary FROM call_logs WHERE status=402 ORDER BY timestamp DESC LIMIT 30")
for r in cur.fetchall():
    err = (r[5][:600] if r[5] else "")
    print(repr(f"[{r[0]}] {r[1]} | {r[2]} | {r[3]} | {r[4]} | {err}"))

print("\n=== 1.2 xhigh errors (is it still happening recently?) ===")
cur.execute("SELECT timestamp, status, error_summary FROM call_logs WHERE requested_model LIKE '%xhigh%' ORDER BY timestamp DESC LIMIT 10")
for r in cur.fetchall():
    print(repr(f"[{r[0]}] {r[1]} | {(r[2][:400] if r[2] else '')}"))

print("\n=== Opencode plugin routing for muse ===")
# Find where muse-spark mapping comes from
base = r"C:\Users\Ota\.config\opencode"
for root,dirs,files in os.walk(base):
    for f in files:
        if f.endswith(('.json','.ts','.js')):
            p = os.path.join(root,f)
            try:
                t = open(p,encoding='utf-8',errors='ignore').read()
                if 'muse-spark' in t:
                    print(f"Found muse-spark in {p}")
                    # print matching lines
                    for line in t.splitlines():
                        if 'muse-spark' in line:
                            print("  ", line[:500])
            except: pass

conn.close()
