import sqlite3, json, re, sys
sys.stdout.reconfigure(encoding='utf-8', errors='replace')
DB = r'G:\Games\steamapps\common\UmamusumePrettyDerby_Jpn\UmamusumePrettyDerby_Jpn_Data\Persistent\master\master.mdb'
JPRE = re.compile(r'[\u3040-\u30FF\u4E00-\u9FFF]')
con = sqlite3.connect('file:' + DB.replace('\\','/') + '?mode=ro', uri=True)
cur = con.cursor()

print('=== story_* related tables ===')
for t in [r[0] for r in cur.execute("SELECT name FROM sqlite_master WHERE type='table' AND name NOT LIKE 'sqlite_%' ORDER BY name")]:
    if re.search(r'story|single_mode|main_story|chara_story|jikkyo|text_data|character_system', t):
        n = cur.execute('SELECT COUNT(*) FROM "%s"' % t).fetchone()[0]
        print('%-40s %d' % (t, n))

print('\n=== missing categories JP detail ===')
for c in [299, 300, 328, 373, 415]:
    rows = cur.execute('SELECT "index", text FROM text_data WHERE category=? ORDER BY "index"', (c,)).fetchall()
    jp = [r for r in rows if JPRE.search(r[1] or '')]
    print('cat %-4d rows=%-5d JP_rows=%-5d' % (c, len(rows), len(jp)))
    for idx, txt in rows[:4]:
        print('   idx=%s: %r' % (idx, txt[:140]))

print('\n=== dict category 186 (in dict, not in master) ===')
d = json.load(open(r'G:\Games\steamapps\common\UmamusumePrettyDerby_Jpn\gemini_horses\localized_data\text_data_dict.json', encoding='utf-8'))
v = d.get('186', {})
print('entries:', len(v), 'sample:', list(v.items())[:3])

print('\n=== duplicates in single_mode_story_data (story_id) ===')
n_dup = cur.execute('SELECT COUNT(*)-COUNT(DISTINCT story_id) FROM single_mode_story_data').fetchone()[0]
print('rows - distinct story_id =', n_dup)
for sid, c in cur.execute('SELECT story_id, COUNT(*) c FROM single_mode_story_data GROUP BY story_id HAVING c>1 ORDER BY c DESC LIMIT 5'):
    print('  story_id', sid, 'appears', c, 'times')

con.close()
