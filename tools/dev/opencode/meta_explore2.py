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

# distinct top-level prefixes of n (first 2 path segments)
rows = c.execute("SELECT substr(n,1, instr(n||'/','/')-1) AS top, count(*) FROM a GROUP BY top ORDER BY count(*) DESC").fetchall()
print('=== top-level prefixes ===')
for r in rows:
    print(f'{r[0]:40s} {r[1]}')

print()
print('=== samples: story/data ===')
for r in c.execute("SELECT n, m FROM a WHERE n LIKE 'story/data/%' LIMIT 8"):
    print(r)

print()
print('=== samples: home/data ===')
for r in c.execute("SELECT n, m FROM a WHERE n LIKE 'home/data/%' LIMIT 8"):
    print(r)

print()
print('=== samples: race ===')
for r in c.execute("SELECT n, m FROM a WHERE n LIKE 'race/%' LIMIT 8"):
    print(r)

print()
print('=== samples: live ===')
for r in c.execute("SELECT n, m FROM a WHERE n LIKE 'live/%' LIMIT 8"):
    print(r)

print()
print('=== samples: character/single_mode ===')
for r in c.execute("SELECT n, m FROM a WHERE n LIKE 'character/%' OR n LIKE 'single_mode/%' OR n LIKE 'singlemode/%' LIMIT 10"):
    print(r)