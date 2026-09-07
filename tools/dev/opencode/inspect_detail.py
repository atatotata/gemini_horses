import sqlite3, json, os, glob

conn = sqlite3.connect(r'C:\Users\Ota\.omniroute\storage.sqlite')
cur = conn.cursor()

# Get recent failed artifact relpaths for muse 1.2 xhigh and 1.3
for model_match in ['%muse-spark-1.3%', '%xhigh%']:
    print(f"\n=== {model_match} ===")
    cur.execute("SELECT timestamp, status, model, requested_model, provider, error_summary, artifact_relpath FROM call_logs WHERE (model LIKE ? OR requested_model LIKE ?) AND status >= 400 ORDER BY timestamp DESC LIMIT 5", (model_match, model_match))
    for r in cur.fetchall():
        print(f"[{r[0]}] {r[1]} | {r[2]} ({r[3]}) | {r[4]}")
        print(f"  err: {r[5][:250] if r[5] else ''}")
        print(f"  artifact: {r[6]}")
        if r[6]:
            # try to find artifact file
            base = r"C:\Users\Ota\.omniroute"
            # artifact_relpath is like 2026-09-03/xxx.json - check several possible locations
            candidates = [os.path.join(base, r[6]), os.path.join(base, "artifacts", r[6]), os.path.join(base, "logs", r[6])]
            for c in candidates:
                if os.path.exists(c):
                    print(f"  FOUND: {c}")
                    try:
                        txt = open(c, encoding='utf-8', errors='ignore').read()
                        print(txt[:3000])
                    except Exception as e: print(e)
                    break
            else:
                # glob search
                m = glob.glob(os.path.join(base, "**", os.path.basename(r[6])), recursive=True)
                print(f"  glob: {m[:3]}")

print("\n=== provider_connections provider_specific_data ===")
cur.execute("SELECT provider, name, provider_specific_data FROM provider_connections WHERE provider IN ('opencode-go','opencode-zen','opencode')")
for r in cur.fetchall():
    try: d=json.loads(r[2]) if r[2] else {}
    except: d=r[2]
    print(f"{r[0]} | {r[1]} | {json.dumps(d, indent=2)[:2000] if isinstance(d, dict) else str(d)[:2000]}")

conn.close()
