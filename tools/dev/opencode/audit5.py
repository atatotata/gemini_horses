import sqlite3, json, re, os
from collections import defaultdict

DB = r"G:\Games\steamapps\common\UmamusumePrettyDerby_Jpn\UmamusumePrettyDerby_Jpn_Data\Persistent\master\master.mdb"
LD = r"G:\Games\steamapps\common\UmamusumePrettyDerby_Jpn\gemini_horses\localized_data"

JP_RE = re.compile(r"[\u3040-\u309f\u30a0-\u30ff\u4e00-\u9fff]")
con = sqlite3.connect(DB)
con.text_factory = lambda b: b.decode("utf-8", errors="replace")
cur = con.cursor()
def q(i): return '"' + i.replace('"','""') + '"'

tables = [r[0] for r in cur.execute("SELECT name FROM sqlite_master WHERE type='table' ORDER BY name")]

# ---- 1) Inspect the 5 missing categories ----
print("=== MISSING CATEGORIES CONTENT (299,300,328,373,415) ===")
for c in ["299","300","328","373","415"]:
    n = cur.execute(f'SELECT COUNT(*) FROM text_data WHERE category={c}').fetchone()[0]
    rows = cur.execute(f'SELECT "index", text FROM text_data WHERE category={c}').fetchall()
    jp = sum(1 for _, tx in rows if JP_RE.search(tx))
    print(f"\ncat {c}: {n} rows, {jp} JP")
    for idx, tx in rows[:12]:
        print(f"   idx={idx}: {tx[:90]!r}")

# ---- 2) FULL scan: ALL columns (any type) for JP ----
print("\n=== FULL JP SCAN: ALL columns, ALL types ===")
hits = []
for t in tables:
    cols = cur.execute(f'PRAGMA table_info({q(t)})').fetchall()
    for c in cols:
        cname = c[1]
        try:
            rows = cur.execute(f'SELECT {q(cname)} FROM {q(t)} WHERE {q(cname)} IS NOT NULL').fetchall()
        except Exception as e:
            continue
        jp, s = 0, []
        for (v,) in rows:
            vs = str(v)
            if JP_RE.search(vs):
                jp += 1
                if len(s) < 3: s.append(vs[:80])
        if jp:
            hits.append((t, cname, jp, s))
            print(f"  {t}.{cname}: JP={jp}  ex={s}")

# ---- 3) race_jikkyo missing id analysis ----
print("\n=== race_jikkyo missing id distribution ===")
for t, d, f in [("race_jikkyo_comment", json.load(open(os.path.join(LD,"race_jikkyo_comment_dict.json"),encoding="utf-8")), "id"),
                ("race_jikkyo_message", json.load(open(os.path.join(LD,"race_jikkyo_message_dict.json"),encoding="utf-8")), "id")]:
    ids = [r[0] for r in cur.execute(f'SELECT {f} FROM {q(t)}')]
    miss = [i for i in ids if str(i) not in d]
    print(f"{t}: total ids {len(ids)}, missing {len(miss)}, missing range {min(miss) if miss else None}-{max(miss) if miss else None}")
    print(f"   dict key range: {min(int(k) for k in d if k.isdigit())}-{max(int(k) for k in d if k.isdigit())}")
    print(f"   sample missing ids: {sorted(miss)[:20]}")