import apsw
DB_BASE_KEY = b'\xF1\x70\xCE\xA4\xDF\xCE\xA3\xE1\xA5\xD8\xC7\x0B\xD1\x00\x00\x00'
DB_KEY = b'\x6D\x5B\x65\x33\x63\x36\x63\x25\x54\x71\x2D\x73\x50\x53\x63\x38\x6D\x34\x37\x7B\x35\x63\x70\x23\x37\x34\x53\x29\x73\x43\x36\x33'
key = bytearray(DB_KEY)
for i in range(len(key)):
    key[i] ^= DB_BASE_KEY[i % 13]
conn = apsw.Connection(r'G:\Games\steamapps\common\UmamusumePrettyDerby_Jpn\UmamusumePrettyDerby_Jpn_Data\Persistent\meta')
conn.pragma('cipher', 'chacha20'); conn.pragma('hexkey', bytes(key).hex())
c = conn.cursor()
print('storytimeline_41001001:', c.execute("SELECT count(*) FROM a WHERE n LIKE 'story/data/%/storytimeline_41001001'").fetchone()[0])
print('410-prefixed timelines:', c.execute("SELECT count(*) FROM a WHERE n LIKE 'story/data/%/storytimeline_410%'").fetchone()[0])
print('timelines 41-prefixed:', c.execute("SELECT count(*) FROM a WHERE n LIKE 'story/data/%/storytimeline_41%'").fetchone()[0])
# distinct timeline id prefixes (first 2 digits)
rows = c.execute("SELECT substr(n, instr(n,'storytimeline_')+13, 2) AS p, count(*) FROM a WHERE n LIKE 'story/data/%/storytimeline_%' AND n NOT LIKE '%resourcelist%' GROUP BY p ORDER BY count(*) DESC").fetchall()
print('id-prefix distribution:')
for r in rows: print(' ', r[0], r[1])