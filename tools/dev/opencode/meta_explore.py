import apsw, sys

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

print('=== schema ===')
for r in c.execute("SELECT sql FROM sqlite_master WHERE type='table' AND name IN ('a','b','c','d')"):
    print(r[0])
print()
print('=== table a sample ===')
for r in c.execute("SELECT n, h, e, m FROM a LIMIT 15"):
    print(r)
print()
print('=== distinct m (top 60 by count) ===')
rows = c.execute("SELECT m, count(*) FROM a GROUP BY m ORDER BY count(*) DESC LIMIT 60").fetchall()
for r in rows:
    print(r[0], r[1])
