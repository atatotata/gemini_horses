import sqlite3, json, os, io

DB = r'G:/Games/steamapps/common/UmamusumePrettyDerby_Jpn/UmamusumePrettyDerby_Jpn_Data/Persistent/master/master.mdb'
LD = r'G:/Games/steamapps/common/UmamusumePrettyDerby_Jpn/gemini_horses/localized_data'
OUT = r'C:\TMP\opencode\audit_out.txt'

buf = io.StringIO()
def p(*a):
    print(*a, file=buf)

con = sqlite3.connect(DB)
cur = con.cursor()

cur.execute("SELECT name FROM sqlite_master WHERE type='table'")
tables = sorted(r[0] for r in cur.fetchall())
kw = ['jikkyo', 'live', 'race', 'comment']
kwtables = [t for t in tables if any(k in t for k in kw)]

p("=== KEYWORD TABLES (name contains jikkyo/live/race/comment) ===")
for t in kwtables:
    try:
        cur.execute('SELECT COUNT(*) FROM "%s"' % t)
        c = cur.fetchone()[0]
        p("%s\trows=%d" % (t, c))
    except Exception as e:
        p("%s\tERR %s" % (t, e))

p("")
p("=== ENCODING CHECK on race_jikkyo_message ===")
cur.execute('SELECT * FROM race_jikkyo_message LIMIT 1')
row = cur.fetchone()
for i, v in enumerate(row):
    if isinstance(v, str):
        found = False
        for enc in ('utf-8', 'shift-jis', 'cp932', 'utf-16-le'):
            try:
                dec = v.encode('latin-1').decode(enc)
                p("col%d repr=%r  latin1->%s=%r" % (i, v[:40], enc, dec[:40]))
                found = True
                break
            except Exception:
                continue
        if not found:
            p("col%d repr=%r" % (i, v[:60]))
    else:
        p("col%d %s = %s" % (i, type(v).__name__, v))

p("")
focus = ['race_jikkyo_message','race_jikkyo_message_window','race_jikkyo_phase_condition','race_comment_group','race_jikkyo_comment']
p("=== FOCUS TABLES schema ===")
for t in focus:
    if t not in tables:
        p("%s\tMISSING IN DB" % t)
        continue
    cur.execute('SELECT COUNT(*) FROM "%s"' % t)
    c = cur.fetchone()[0]
    p("")
    p("[%s] rows=%d" % (t, c))
    for r in cur.execute('PRAGMA table_info("%s")' % t):
        p("   col=%s type=%s" % (r[1], r[2]))
    cols = [d[1] for d in cur.execute('PRAGMA table_info("%s")' % t)]
    try:
        cur.execute('SELECT MIN("%s"), MAX("%s") FROM "%s"' % (cols[0], cols[0], t))
        mn, mx = cur.fetchone()
        p("   col0 %s range=%s..%s" % (cols[0], mn, mx))
    except Exception as e:
        p("   range ERR %s" % e)

p("")
p("=== LOCALIZED JSON FILES (top-level of localized_data) ===")
for f in sorted(os.listdir(LD)):
    if not f.endswith('.json'):
        continue
    full = os.path.join(LD, f)
    try:
        d = json.load(open(full, encoding='utf-8'))
    except Exception as e:
        p("[%s] LOAD ERR %s" % (f, e))
        continue
    if isinstance(d, dict):
        p("[%s] dict len=%d sample_keys=%s" % (f, len(d), list(d.keys())[:6]))
    elif isinstance(d, list):
        p("[%s] list len=%d" % (f, len(d)))
    else:
        p("[%s] type=%s" % (f, type(d).__name__))

with open(OUT, 'w', encoding='utf-8') as fh:
    fh.write(buf.getvalue())
print("done ->", OUT)
