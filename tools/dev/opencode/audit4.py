import sqlite3, json, os
DB = r'G:/Games/steamapps/common/UmamusumePrettyDerby_Jpn/UmamusumePrettyDerby_Jpn_Data/Persistent/master/master.mdb'
LD = r'G:/Games/steamapps/common/UmamusumePrettyDerby_Jpn/gemini_horses/localized_data'
def load(f): return json.load(open(os.path.join(LD, f), encoding='utf-8'))
msg_d, com_d = load('race_jikkyo_message_dict.json'), load('race_jikkyo_comment_dict.json')
con = sqlite3.connect(DB); cur = con.cursor()

for table, d, name in [('race_jikkyo_message', msg_d, 'message'), ('race_jikkyo_comment', com_d, 'comment')]:
    cur.execute('SELECT "id" FROM "%s" ORDER BY "id"' % table)
    ids = [r[0] for r in cur.fetchall()]
    tr = [i for i in ids if str(i) in d]
    untr = [i for i in ids if str(i) not in d]
    print("== %s: translated ids count=%d  untranslated=%d" % (name, len(tr), len(untr)))
    print("   max translated id=%d  min untranslated id=%d  max untranslated id=%d"
          % (max(tr) if tr else -1, untr[0] if untr else -1, untr[-1] if untr else -1))
    # is translated set a prefix of ascending ids? -> translated ids all < min untranslated?
    print("   prefix-consistent (all translated ids < all untranslated ids):",
          (max(tr) < min(untr)) if tr and untr else None)
    print("   dict keys sample sorted head/tail:", sorted(int(k) for k in d)[:5], sorted(int(k) for k in d)[-5:])

# other *_jikkyo tables: do their TEXT columns reference message ids or contain JP?
for t in ['race_jikkyo_base','race_jikkyo_base_venus','race_jikkyo_cue','race_jikkyo_race','race_jikkyo_trigger']:
    cols = [(r[1], r[2]) for r in cur.execute('PRAGMA table_info("%s")' % t)]
    print("\n[%s] cols=%s" % (t, [(c, ty) for c, ty in cols][:20]))
    cur.execute('SELECT * FROM "%s" LIMIT 1' % t)
    print("   row0:", cur.fetchone())
