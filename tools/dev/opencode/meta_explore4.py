import apsw

DB_BASE_KEY = b'\xF1\x70\xCE\xA4\xDF\xCE\xA3\xE1\xA5\xD8\xC7\x0B\xD1\x00\x00\x00'
DB_KEY = b'\x6D\x5B\x65\x33\x63\x36\x63\x25\x54\x71\x2D\x73\x50\x53\x63\x38\x6D\x34\x37\x7B\x35\x63\x70\x23\x37\x34\x53\x29\x73\x43\x36\x33'
key = bytearray(DB_KEY)
for i in range(len(key)):
    key[i] ^= DB_BASE_KEY[i % 13]
final = bytes(key)

conn = apsw.Connection(r'G:\Games\steamapps\common\UmamusumePrettyDerby_Jpn\UmamusumePrettyDerby_Jpn_Data\Persistent\meta')
conn.pragma('cipher', 'chacha20')
conn.pragma('hexkey', final.hex())
c = conn.cursor()

print('=== race/storyrace entries ===')
for r in c.execute("SELECT n, m FROM a WHERE n LIKE 'race/storyrace/%' LIMIT 15"):
    print(r)

print()
print('=== jikkyo in meta ===')
for r in c.execute("SELECT n, m FROM a WHERE n LIKE '%jikkyo%' LIMIT 15"):
    print(r)
print('count jikkyo:', c.execute("SELECT count(*) FROM a WHERE n LIKE '%jikkyo%'").fetchone()[0])

print()
print('=== lyrics in meta ===')
for r in c.execute("SELECT n, m FROM a WHERE n LIKE '%lyric%' LIMIT 10"):
    print(r)
print('count lyric:', c.execute("SELECT count(*) FROM a WHERE n LIKE '%lyric%'").fetchone()[0])

print()
print('=== text/msg/comment assets (cygames text) ===')
for r in c.execute("SELECT n, m FROM a WHERE (n LIKE '%text_data%' OR n LIKE '%textdata%') LIMIT 10"):
    print(r)
print()
for r in c.execute("SELECT n, m FROM a WHERE n LIKE 'outgame/%' AND (n LIKE '%text%' OR n LIKE '%message%' OR n LIKE '%comment%' OR n LIKE '%word%' OR n LIKE '%name%') LIMIT 20"):
    print(r)

print()
print('=== uianimation/flash text-ish ===')
for r in c.execute("SELECT n, m FROM a WHERE n LIKE 'uianimation/flash/%' AND (n LIKE '%_txt_%' OR n LIKE '%text%' OR n LIKE '%word%' OR n LIKE '%msg%') LIMIT 15"):
    print(r)

print()
print('=== storyevent/collectevent/transferevent paths ===')
for r in c.execute("SELECT n, m FROM a WHERE n LIKE 'storyevent/%' LIMIT 8"):
    print(r)