import apsw, sqlite3
DB_BASE_KEY = b'\xF1\x70\xCE\xA4\xDF\xCE\xA3\xE1\xA5\xD8\xC7\x0B\xD1\x00\x00\x00'
DB_KEY = b'\x6D\x5B\x65\x33\x63\x36\x63\x25\x54\x71\x2D\x73\x50\x53\x63\x38\x6D\x34\x37\x7B\x35\x63\x70\x23\x37\x34\x53\x29\x73\x43\x36\x33'
key = bytearray(DB_KEY)
for i in range(len(key)):
    key[i] ^= DB_BASE_KEY[i % 13]
conn = apsw.Connection(r'G:\Games\steamapps\common\UmamusumePrettyDerby_Jpn\UmamusumePrettyDerby_Jpn_Data\Persistent\meta')
conn.pragma('cipher', 'chacha20'); conn.pragma('hexkey', bytes(key).hex())
c = conn.cursor()

print('=== story other sample (3909) ===')
for r in c.execute("SELECT n FROM a WHERE n LIKE 'story/%' AND n NOT LIKE 'story/data/%' AND n NOT LIKE '%resourcelist%' AND n NOT LIKE '%storytimeline%' LIMIT 12"):
    print(r[0])
print()
print('=== story/data other (non-timeline non-ast non-resource) ===')
for r in c.execute("SELECT n FROM a WHERE n LIKE 'story/data/%' AND n NOT LIKE '%resourcelist%' AND n NOT LIKE '%storytimeline%' AND n NOT LIKE '%ast_%' LIMIT 10"):
    print(r[0])
print()
print('=== uianimation text-ish counts ===')
print('flash txt/text prefabs:', c.execute("SELECT count(*) FROM a WHERE n LIKE 'uianimation/flash/%' AND (n LIKE '%txt%' OR n LIKE '%text%' OR n LIKE '%msg%' OR n LIKE '%word%')").fetchone()[0])
print('all uianimation:', c.execute("SELECT count(*) FROM a WHERE n LIKE 'uianimation/%'").fetchone()[0])
print()
print('=== outgame text-ish ===')
print('honor textsettings:', c.execute("SELECT count(*) FROM a WHERE n LIKE 'outgame/%' AND (n LIKE '%textsetting%' OR n LIKE '%text_setting%')").fetchone()[0])
print('outgame name/message/comment-ish:', c.execute("SELECT count(*) FROM a WHERE n LIKE 'outgame/%' AND (n LIKE '%_name%' OR n LIKE '%message%' OR n LIKE '%comment%' OR n LIKE '%word%')").fetchone()[0])
print()
print('=== sourceresources flash text-ish ===')
print('as_uparam:', c.execute("SELECT count(*) FROM a WHERE n LIKE 'sourceresources/flash/%as_uparam%'").fetchone()[0])
print('as_umeshparam (mesh text):', c.execute("SELECT count(*) FROM a WHERE n LIKE 'sourceresources/flash/%as_umeshparam%'").fetchone()[0])
print()
print('=== race text-ish ===')
print('racetitle:', c.execute("SELECT count(*) FROM a WHERE n LIKE 'race/racetitle/%'").fetchone()[0])
print('champions:', c.execute("SELECT count(*) FROM a WHERE n LIKE 'race/champions/%'").fetchone()[0])
print('teamstadium:', c.execute("SELECT count(*) FROM a WHERE n LIKE 'race/teamstadium/%'").fetchone()[0])
print()
print('=== guide/jobs ===')
for r in c.execute("SELECT n FROM a WHERE n LIKE 'guide/%' LIMIT 5"):
    print(r[0])
print()
print('=== single (814) ===')
for r in c.execute("SELECT n FROM a WHERE n LIKE 'single/%' LIMIT 6"):
    print(r[0])
print()
print('=== master.mdb: text tables count vs localized dicts ===')
mc = sqlite3.connect(r'G:\Games\steamapps\common\UmamusumePrettyDerby_Jpn\UmamusumePrettyDerby_Jpn_Data\Persistent\master\master.mdb')
mcur = mc.cursor()
for t in ['text_data','character_system_text','race_jikkyo_comment','race_jikkyo_message']:
    n = mcur.execute('SELECT count(*) FROM %s' % t).fetchone()[0]
    print('%s: %d' % (t, n))
print('race_jikkyo_message unique race_instance_id:', mcur.execute('SELECT count(DISTINCT race_instance_id) FROM race_jikkyo_message').fetchone()[0])
mc.close()
conn.close()