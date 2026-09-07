import sqlite3, json, os, io, re
from collections import Counter

DB = r'G:/Games/steamapps/common/UmamusumePrettyDerby_Jpn/UmamusumePrettyDerby_Jpn_Data/Persistent/master/master.mdb'
LD = r'G:/Games/steamapps/common/UmamusumePrettyDerby_Jpn/gemini_horses/localized_data'
OUT = r'C:\TMP\opencode\audit_final.txt'

buf = io.StringIO()
def p(*a): print(*a, file=buf)

JP = re.compile(r'[\u3040-\u30ff\u3400-\u9fff\uf900-\ufaff]')

con = sqlite3.connect(DB)
cur = con.cursor()

cur.execute("SELECT name FROM sqlite_master WHERE type='table'")
tables = sorted(r[0] for r in cur.fetchall())

def load(f):
    return json.load(open(os.path.join(LD, f), encoding='utf-8'))

msg_dict = load('race_jikkyo_message_dict.json')
com_dict = load('race_jikkyo_comment_dict.json')

def summarize(name, table, d):
    cur.execute('SELECT "id" FROM "%s"' % table)
    ids = [r[0] for r in cur.fetchall()]
    distinct = sorted(set(ids))
    dup = len(ids) - len(distinct)
    idset = set(distinct)
    keyset = set(d.keys())
    cov = len(idset & {int(k) for k in keyset if str(k).isdigit()})
    miss = sorted(idset - {int(k) for k in keyset if str(k).isdigit()})
    extra = sorted(int(k) for k in keyset if str(k).isdigit() and int(k) not in idset)
    pct = 100.0 * cov / len(distinct) if distinct else 0.0
    p("[%s] table=%s" % (name, table))
    p("  master rows=%d  distinct_ids=%d  dup_id_rows=%d  id_range=%s..%s"
      % (len(ids), len(distinct), dup, min(distinct), max(distinct)))
    p("  localized keys=%d  keys in dict that match master id=%d  coverage=%.1f%%"
      % (len(d), cov, pct))
    p("  GAP: master ids UNTRANSLATED=%d   EXTRA/stale dict keys=%d"
      % (len(miss), len(extra)))
    p("  untranslated sample ids=%s" % miss[:12])
    p("  stale sample keys=%s" % extra[:12])
    return cov, len(distinct), len(d), pct, miss

p("### 1. FOCUS TABLES vs their localized dicts ###")
m = summarize('race_jikkyo_message_dict.json', 'race_jikkyo_message', msg_dict)
p("")
c = summarize('race_jikkyo_comment_dict.json', 'race_jikkyo_comment', com_dict)

p("")
p("### 2. Which master tables exist among the 5 focus names? ###")
for t in ['race_jikkyo_message','race_jikkyo_message_window','race_jikkyo_phase_condition',
          'race_comment_group','race_jikkyo_comment']:
    p("  %-32s %s" % (t, "EXISTS" if t in tables else "NOT IN DB"))

p("")
p("### 3. Untranslated message rows context (Venus/new content check) ###")
cur.execute('SELECT "id","group_id","comment_group" FROM race_jikkyo_message')
rows = cur.fetchall()
miss_rows = [r for r in rows if str(r[0]) not in msg_dict]
cg = Counter(r[2] for r in miss_rows)
p("  untranslated rows=%d / total=%d" % (len(miss_rows), len(rows)))
p("  by comment_group: %s" % sorted(cg.items(), key=lambda x: -x[1])[:15])
# peek race_jikkyo_base_venus ids to see if new-mode rows cluster at high ids
cur.execute('SELECT MIN("id"), MAX("id") FROM race_jikkyo_base_venus')
p("  race_jikkyo_base_venus id range: %s" % (cur.fetchone(),))

p("")
p("### 4. Untranslated message samples ###")
cur.execute('SELECT "id","message","group_id","comment_group" FROM race_jikkyo_message ORDER BY "id"')
shown = 0
for r in cur.fetchall():
    if str(r[0]) in msg_dict: continue
    p("  id=%-6s group_id=%-7s cg=%s :: %s" % (r[0], r[2], r[3], (r[1] or '')[:90].replace('\n', '\\n')))
    shown += 1
    if shown >= 8: break

p("")
p("### 5. ALL keyword tables (jikkyo/live/race/comment) JP-text scan ###")
kw = ['jikkyo', 'live', 'race', 'comment']
jp_tables = []
for t in tables:
    if not any(k in t for k in kw): continue
    cur.execute('SELECT COUNT(*) FROM "%s"' % t)
    n = cur.fetchone()[0]
    tcols = [r[1] for r in cur.execute('PRAGMA table_info("%s")' % t) if 'TEXT' in r[2].upper()]
    jpn = 0
    for c in tcols:
        try:
            cur.execute('SELECT "%s" FROM "%s" WHERE "%s" IS NOT NULL' % (c, t, c))
            jpn += sum(1 for (v,) in cur.fetchall() if isinstance(v, str) and JP.search(v))
        except Exception:
            pass
    if jpn:
        jp_tables.append((t, n, jpn))
        p("  %-42s rows=%-6d JPtext_rows~%d" % (t, n, jpn))
p("  (non-JP tables omitted; JP-bearing count=%d)" % len(jp_tables))

p("")
p("### 6. JP-bearing table sample text + which localized dict could cover it ###")
# union of all top-level dict values to test overlap
allvals = set()
for f in os.listdir(LD):
    if f.endswith('.json') and f not in ('config.json','info.json'):
        try:
            d = json.load(open(os.path.join(LD, f), encoding='utf-8'))
        except Exception:
            continue
        if isinstance(d, dict):
            for k, v in d.items():
                if isinstance(v, str): allvals.add(v)
for t, n, jpn in jp_tables:
    tcols = [r[1] for r in cur.execute('PRAGMA table_info("%s")' % t) if 'TEXT' in r[2].upper()]
    found_overlap = 0
    p("[%s] rows=%d textcols=%s" % (t, n, tcols))
    for c in tcols[:2]:
        cur.execute('SELECT "%s" FROM "%s" WHERE "%s" IS NOT NULL' % (c, t, c))
        vals = [v for (v,) in cur.fetchall() if isinstance(v, str) and JP.search(v)]
        found_overlap += sum(1 for v in vals if v in allvals)
        for v in vals[:2]:
            p("    %s: %s" % (c, v[:110].replace('\n','\\n')))
    p("    -> JP strings also present in any localized dict value: %d (exact match)" % found_overlap)

with open(OUT, 'w', encoding='utf-8') as fh:
    fh.write(buf.getvalue())
print("done ->", OUT)
