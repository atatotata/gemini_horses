import sqlite3
conn = sqlite3.connect(r'G:\Games\steamapps\common\UmamusumePrettyDerby_Jpn\UmamusumePrettyDerby_Jpn_Data\Persistent\master\master.mdb')
c = conn.cursor()
tbls = [r[0] for r in c.execute("SELECT name FROM sqlite_master WHERE type='table'")]
print('tables:', len(tbls))
for t in ['single_mode_story_data','chara_story_data','main_story_data','text_data','race_jikkyo_comment','race_jikkyo_message','character_system_text','lyrics','race_movie']:
    if t in tbls:
        n = c.execute('SELECT count(*) FROM %s' % t).fetchone()[0]
        print('%s: %d rows' % (t, n))
conn.close()