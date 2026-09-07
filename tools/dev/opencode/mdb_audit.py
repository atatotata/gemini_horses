import sqlite3, json, re, sys, time
sys.stdout.reconfigure(encoding='utf-8', errors='replace')

DB = r'G:\Games\steamapps\common\UmamusumePrettyDerby_Jpn\UmamusumePrettyDerby_Jpn_Data\Persistent\master\master.mdb'
DICT = r'G:\Games\steamapps\common\UmamusumePrettyDerby_Jpn\gemini_horses\localized_data\text_data_dict.json'
DICTS = {
    'character_system_text': r'G:\Games\steamapps\common\UmamusumePrettyDerby_Jpn\gemini_horses\localized_data\character_system_text_dict.json',
    'race_jikkyo_message': r'G:\Games\steamapps\common\UmamusumePrettyDerby_Jpn\gemini_horses\localized_data\race_jikkyo_message_dict.json',
    'race_jikkyo_comment': r'G:\Games\steamapps\common\UmamusumePrettyDerby_Jpn\gemini_horses\localized_data\race_jikkyo_comment_dict.json',
}
JPRE = re.compile(r'[\u3040-\u30FF\u4E00-\u9FFF]')
KNOWN_JP = {('text_data','text'), ('character_system_text','text'),
            ('race_jikkyo_message','message'), ('race_jikkyo_comment','message')}
PRIOR = {'text_data':97029, 'character_system_text':33287, 'single_mode_story_data':16481,
         'chara_story_data':931, 'story_event_story_data':56}

con = sqlite3.connect('file:' + DB.replace('\\','/') + '?mode=ro', uri=True)
cur = con.cursor()
t0 = time.time()

tables = [r[0] for r in cur.execute("SELECT name FROM sqlite_master WHERE type='table' AND name NOT LIKE 'sqlite_%' ORDER BY name")]
all_tbls = [r[0] for r in cur.execute("SELECT name FROM sqlite_master WHERE type='table' ORDER BY name")]
print('user tables:', len(tables), '| all sqlite_master tables:', len(all_tbls))
print('sqlite internal tables:', [t for t in all_tbls if t.startswith('sqlite_')])

# ---- PART 1 row counts ----
print('\n=== PART 1: row counts ===')
rows = {}
for t in tables:
    rows[t] = cur.execute('SELECT COUNT(*) FROM "%s"' % t).fetchone()[0]
for t in PRIOR:
    curv = rows.get(t, -1)
    d = curv - PRIOR[t]
    print('%-26s now=%-7d prior=%-7d delta=%+d' % (t, curv, PRIOR[t], d))
print('(all tables counted; total rows scanned)')

# ---- PART 2 text_data categories vs dict ----
print('\n=== PART 2: text_data categories ===')
cats = [r[0] for r in cur.execute('SELECT DISTINCT category FROM text_data ORDER BY category')]
cat_counts = dict(cur.execute('SELECT category, COUNT(*) FROM text_data GROUP BY category').fetchall())
d = json.load(open(DICT, encoding='utf-8'))
dict_cats = set(int(k) for k in d.keys())
master_cats = set(cats)
missing = sorted(master_cats - dict_cats)
extra = sorted(dict_cats - master_cats)
print('master categories: %d  dict categories: %d' % (len(master_cats), len(dict_cats)))
print('master categories MISSING from dict: %d -> %s' % (len(missing), missing))
print('dict categories NOT in master: %d -> %s' % (len(extra), extra))
for c in missing[:15]:
    n = cat_counts.get(c, 0)
    samp = None
    for (txt,) in cur.execute('SELECT text FROM text_data WHERE category=? AND text != "" LIMIT 60', (c,)):
        if JPRE.search(txt):
            samp = txt; break
    if samp is None:
        samp = cur.execute('SELECT text FROM text_data WHERE category=? LIMIT 1', (c,)).fetchone()
        samp = samp[0] if samp else ''
    print('  missing cat %-4d rows=%-5d JP_sample=%r' % (c, n, samp[:120]))
if missing:
    # overall row counts in missing categories
    mrow = sum(cat_counts[c] for c in missing)
    print('total rows in missing categories: %d of %d' % (mrow, rows['text_data']))

# ---- PART 3 JP column scan ----
print('\n=== PART 3: JP scan across all tables (TEXT-ish columns) ===')
jp_hits = {}
for t in tables:
    cols = [r for r in cur.execute('PRAGMA table_info("%s")' % t)]
    cand = [(c[1], c[2]) for c in cols if c[2] and not ('INT' in c[2].upper() and 'TEXT' not in c[2].upper())]
    if not cand:
        continue
    names = [c[0] for c in cand]
    sel = ','.join('"%s"' % n for n in names)
    try:
        cur.execute('SELECT %s FROM "%s"' % (sel, t))
    except sqlite3.Error as e:
        print('  ERR table', t, e); continue
    col_counts = {n: 0 for n in names}
    while True:
        chunk = cur.fetchmany(2000)
        if not chunk:
            break
        for row in chunk:
            for n, v in zip(names, row):
                if isinstance(v, str) and JPRE.search(v):
                    col_counts[n] += 1
    for n in names:
        if col_counts[n] > 0:
            jp_hits[(t, n)] = col_counts[n]
print('tables with any JP text column: %d of %d' % (len({t for t,_ in jp_hits}), len(tables)))
print('%-32s %-24s %10s  %s' % ('table','column','jp_rows','known/new'))
for (t, n), cnt in sorted(jp_hits.items()):
    tag = 'KNOWN' if (t, n) in KNOWN_JP else '>>> NEW'
    print('%-32s %-24s %10d  %s' % (t, n, cnt, tag))
new_cols = [(t, n) for (t, n) in jp_hits if (t, n) not in KNOWN_JP]
print('columns with JP outside the 4 known: %d -> %s' % (len(new_cols), new_cols))

# ---- PART 4 story ids ----
print('\n=== PART 4: story id extraction ===')
def story_pairs(tbl, rowid_note=''):
    """Find story_type_N/story_id_N columns; return list of (type, id)."""
    cols = [c[1] for c in cur.execute('PRAGMA table_info("%s")' % tbl)]
    res = []
    for cname in cols:
        if re.fullmatch(r'story_type_\d+', cname):
            n = cname.rsplit('_', 1)[1]
            idcol = 'story_id_' + n
            if idcol in cols:
                res.append((cname, idcol))
    return res

def distinct_story_ids(tbl):
    """story_type_N != 0 -> story_id_N, all distinct."""
    pairs = story_pairs(tbl)
    ids = set()
    if not pairs:
        # direct story_id column
        cols = [c[1] for c in cur.execute('PRAGMA table_info("%s")' % tbl)]
        if 'story_id' in cols:
            return 'direct story_id', {r[0] for r in cur.execute('SELECT DISTINCT story_id FROM "%s" WHERE story_id != 0' % tbl)}
        return 'none', set()
    for tn, idn in pairs:
        for (x,) in cur.execute('SELECT DISTINCT %s FROM "%s" WHERE %s != 0' % (idn, tbl, tn)):
            ids.add(x)
    return 'type_N pattern (%d slots)' % len(pairs), ids

for tbl in ['single_mode_story_data', 'chara_story_data', 'main_story_data',
            'story_event_story_data', 'story_extra_story_data']:
    if tbl not in tables:
        print('%-24s table absent' % tbl); continue
    r = rows[tbl]
    if tbl == 'single_mode_story_data':
        d_sid = set(x[0] for x in cur.execute('SELECT DISTINCT story_id FROM single_mode_story_data WHERE story_id != 0'))
        d_ssid = set(x[0] for x in cur.execute('SELECT DISTINCT short_story_id FROM single_mode_story_data WHERE short_story_id != 0'))
        print('%-24s rows=%-6d distinct story_id=%-5d  distinct short_story_id=%-5d  combined=%-5d' %
              (tbl, r, len(d_sid), len(d_ssid), len(d_sid | d_ssid)))
    elif tbl == 'chara_story_data':
        d_sid = set(x[0] for x in cur.execute('SELECT DISTINCT story_id FROM chara_story_data WHERE story_id != 0'))
        print('%-24s rows=%-6d distinct story_id=%-5d' % (tbl, r, len(d_sid)))
    else:
        kind, ids = distinct_story_ids(tbl)
        print('%-24s rows=%-6d %-24s distinct story ids (type!=0)=%-5d' % (tbl, r, kind, len(ids)))

# ---- PART 5 new tables heuristic ----
print('\n=== PART 5: table count vs prior 627 ===')
print('current user tables: %d (prior known claim: 627) -> delta %+d' % (len(tables), len(tables) - 627))

con.close()
print('\nfinished in %.1fs' % (time.time() - t0))
