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

print('=== story/data entries: pattern breakdown ===')
rows = c.execute("""
SELECT 
  CASE 
    WHEN n LIKE '%/resourcelist/%' THEN 'resourcelist'
    WHEN n LIKE '%storytimeline_%' THEN 'storytimeline'
    ELSE 'other'
  END AS pat, count(*)
FROM a WHERE n LIKE 'story/data/%' GROUP BY pat
""").fetchall()
for r in rows: print(r)

print()
print('=== sample storytimeline entries (non-resourcelist) ===')
for r in c.execute("SELECT n, m, d FROM a WHERE n LIKE 'story/data/%' AND n LIKE '%storytimeline_%' AND n NOT LIKE '%resourcelist%' LIMIT 10"):
    print(r)

print()
print('=== sample story/data other ===')
for r in c.execute("SELECT n, m, d FROM a WHERE n LIKE 'story/data/%' AND n NOT LIKE '%storytimeline_%' AND n NOT LIKE '%resourcelist%' LIMIT 10"):
    print(r)

print()
print('=== home/data pattern breakdown ===')
rows = c.execute("""
SELECT 
  CASE 
    WHEN n LIKE '%_hometimeline_%' THEN 'hometimeline'
    ELSE 'other'
  END AS pat, count(*)
FROM a WHERE n LIKE 'home/data/%' GROUP BY pat
""").fetchall()
for r in rows: print(r)
print('sample home/data other:')
for r in c.execute("SELECT n, m, d FROM a WHERE n LIKE 'home/data/%' AND n NOT LIKE '%_hometimeline_%' LIMIT 10"):
    print(r)

print()
print('=== race: subdir breakdown ===')
for r in c.execute("SELECT substr(n, 6, instr(substr(n,6)||'/','/')-1) AS sub, count(*) FROM a WHERE n LIKE 'race/%' GROUP BY sub ORDER BY count(*) DESC"):
    print(r)

print()
print('=== where are single_mode / character paths? ===')
for r in c.execute("SELECT n, m FROM a WHERE n LIKE '%single%' LIMIT 12"):
    print(r)
for r in c.execute("SELECT n, m FROM a WHERE n LIKE 'chara/%' AND (n LIKE '%story%' OR n LIKE '%timeline%') LIMIT 10"):
    print(r)