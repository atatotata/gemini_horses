import apsw, sqlite3

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

print('=== home/data: full path breakdown (row count by depth pattern) ===')
rows = c.execute("SELECT n FROM a WHERE n LIKE 'home/data/%'").fetchall()
from collections import Counter
pat = Counter()
for (n,) in rows:
    base = n.split('/')[-1]
    # classify
    if '_hometimeline_' in base:
        pat['hometimeline'] += 1
    elif 'resourcelist' in n:
        pat['resourcelist'] += 1
    else:
        pat['other:' + base[:30]] += 1
for k, v in pat.most_common(15):
    print(k, v)

print()
print('=== unique basename classes ===')
uniq = Counter()
for (n,) in rows:
    base = n.split('/')[-1]
    if '_hometimeline_' in base:
        cls = 'hometimeline'
    elif 'resourcelist' in n:
        cls = 'resourcelist'
    else:
        cls = 'other'
    uniq[cls] += 1
print('row counts by class:', dict(uniq))
uniq_bases = Counter()
seen = set()
for (n,) in rows:
    base = n.split('/')[-1]
    if base not in seen:
        seen.add(base)
        if '_hometimeline_' in base:
            uniq_bases['hometimeline'] += 1
        elif 'resourcelist' in n:
            uniq_bases['resourcelist'] += 1
        else:
            uniq_bases['other'] += 1
print('unique basenames by class:', dict(uniq_bases))

print()
print('=== sample unique hometimeline basenames (meta) ===')
seen = set()
cnt = 0
for (n,) in rows:
    base = n.split('/')[-1]
    if '_hometimeline_' in base and base not in seen:
        seen.add(base)
        print(base)
        cnt += 1
        if cnt >= 10: break

print()
print('=== localized hometimeline sample ===')
import os
local = r'G:\Games\steamapps\common\UmamusumePrettyDerby_Jpn\gemini_horses\localized_data\assets\home'
for f in sorted(os.listdir(local))[:5]:
    print(f)
for root, dirs, files in os.walk(local):
    for f in files[:3]:
        print(os.path.relpath(os.path.join(root, f), local))

print()
print('=== main_story_data schema ===')
mc = sqlite3.connect(r'G:\Games\steamapps\common\UmamusumePrettyDerby_Jpn\UmamusumePrettyDerby_Jpn_Data\Persistent\master\master.mdb')
mcur = mc.cursor()
print(mcur.execute("SELECT sql FROM sqlite_master WHERE name='main_story_data'").fetchone()[0])
print(mcur.execute("SELECT sql FROM sqlite_master WHERE name='chara_story_data'").fetchone()[0][:200])
print(mcur.execute("SELECT sql FROM sqlite_master WHERE name='single_mode_story_data'").fetchone()[0][:200])
mc.close()
conn.close()