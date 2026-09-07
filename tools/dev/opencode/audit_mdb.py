import sqlite3, sys, json, re
from collections import defaultdict

DB = r"G:\Games\steamapps\common\UmamusumePrettyDerby_Jpn\UmamusumePrettyDerby_Jpn_Data\Persistent\master\master.mdb"
DICT = r"G:\Games\steamapps\common\UmamusumePrettyDerby_Jpn\gemini_horses\localized_data\text_data_dict.json"

JP_RE = re.compile(r"[\u3040-\u309f\u30a0-\u30ff\u4e00-\u9fff]")

con = sqlite3.connect(DB)
con.text_factory = lambda b: b.decode("utf-8", errors="replace")
cur = con.cursor()

# ---- Step 0: text_data schema ----
print("=== text_data schema ===")
cols = cur.execute('PRAGMA table_info(text_data)').fetchall()
for c in cols:
    print("  ", c[1], c[2])
print("text_data row count:", cur.execute('SELECT COUNT(*) FROM text_data').fetchone()[0])

# distinct categories
cats = [r[0] for r in cur.execute('SELECT DISTINCT "category" FROM text_data ORDER BY "category"')]
print("distinct categories:", len(cats))

# ---- Step 1: find TEXT columns across tables, sample for JP ----
print("\n=== ALL TABLES: TEXT columns with JP detection ===")
tables = [r[0] for r in cur.execute("SELECT name FROM sqlite_master WHERE type='table' ORDER BY name")]

report = []  # (table, col, jp_count, total)
for t in tables:
    try:
        tcols = cur.execute(f'PRAGMA table_info("{t}")').fetchall()
    except Exception as e:
        print("  !! pragma fail", t, e)
        continue
    tcount = cur.execute(f'SELECT COUNT(*) FROM "{t}"').fetchone()[0]
    for c in tcols:
        cname, ctype = c[1], c[2]
        if ctype.upper() not in ("TEXT", "CLOB", "VARCHAR", "NVARCHAR", "CHAR"):
            continue
        if cname in ("index",):  # reserved-ish but read as text col ok
            pass
        # count rows containing JP
        n = cur.execute(f'SELECT COUNT(*) FROM "{t}" WHERE "{cname}" IS NOT NULL AND "{cname}" != \'\'').fetchone()[0]
        # sample scan for JP - count via python to avoid LIKE 8000 issue; do efficient scan
        jp = 0
        samples = []
        if n > 0:
            rows = cur.execute(f'SELECT "{cname}" FROM "{t}" WHERE "{cname}" IS NOT NULL AND "{cname}" != \'\'').fetchall()
            for (v,) in rows:
                if JP_RE.search(str(v)):
                    jp += 1
                    if len(samples) < 3:
                        samples.append(str(v)[:120])
        if jp > 0:
            report.append((t, cname, jp, tcount))
            print(f"  {t}.{cname}: {jp}/{n} JP rows (table total {tcount})  samples: {samples}")

print(f"\nTotal text tables with JP: {len(report)}")
