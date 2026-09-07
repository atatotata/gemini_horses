import apsw, sqlite3, os
DB_BASE_KEY = b'\xF1\x70\xCE\xA4\xDF\xCE\xA3\xE1\xA5\xD8\xC7\x0B\xD1\x00\x00\x00'
DB_KEY = b'\x6D\x5B\x65\x33\x63\x36\x63\x25\x54\x71\x2D\x73\x50\x53\x63\x38\x6D\x34\x37\x7B\x35\x63\x70\x23\x37\x34\x53\x29\x73\x43\x36\x33'
key = bytearray(DB_KEY)
for i in range(len(key)):
    key[i] ^= DB_BASE_KEY[i % 13]
conn = apsw.Connection(r'G:\Games\steamapps\common\UmamusumePrettyDerby_Jpn\UmamusumePrettyDerby_Jpn_Data\Persistent\meta')
conn.pragma('cipher', 'chacha20'); conn.pragma('hexkey', bytes(key).hex())
c = conn.cursor()

meta_ids = set()
for (n,) in c.execute("SELECT n FROM a WHERE n LIKE 'story/data/%' AND n NOT LIKE '%resourcelist%'"):
    base = n.split('/')[-1]
    if base.startswith('storytimeline_'):
        meta_ids.add(base[len('storytimeline_'):])
print('meta timeline ids:', len(meta_ids))

mc = sqlite3.connect(r'G:\Games\steamapps\common\UmamusumePrettyDerby_Jpn\UmamusumePrettyDerby_Jpn_Data\Persistent\master\master.mdb')
mcur = mc.cursor()

# main story: check story/data/10/0000 etc
print()
print('=== main story timelines sample (10/0000) ===')
for r in c.execute("SELECT n FROM a WHERE n LIKE 'story/data/10/0000/%' AND n NOT LIKE '%resourcelist%' LIMIT 6"):
    print(r[0])
print('=== main story: which story_id_1 values look like timeline ids? ===')
s1 = set(str(r[0]) for r in mcur.execute("SELECT DISTINCT story_id_1 FROM main_story_data WHERE story_id_1 != 0"))
print('story_id_1 sample:', sorted(s1)[:10])
# check id column too
ids_col = set(str(r[0]) for r in mcur.execute("SELECT DISTINCT id FROM main_story_data"))
print('main_story_data.id sample:', sorted(ids_col)[:10], 'in meta:', len(ids_col & meta_ids))

# maybe main story timeline ids are like 1001xxx / 1002xxx
pref = {}
for i in meta_ids:
    p = i[:3]
    pref[p] = pref.get(p, 0) + 1
print()
print('=== timeline id 3-digit prefixes (top 25) ===')
for p, cnt in sorted(pref.items(), key=lambda x: -x[1])[:25]:
    print(' ', p, cnt)

# chara: zero-pad check
ch_ids = set(str(r[0]) for r in mcur.execute("SELECT DISTINCT story_id FROM chara_story_data WHERE story_id != 0"))
ch_pad = set(i.zfill(9) for i in ch_ids)
print()
print('chara ids:', len(ch_ids), 'padded in meta:', len(ch_pad & meta_ids), 'padded not in meta:', len(ch_pad - meta_ids))
print('padded missing sample:', sorted(ch_pad - meta_ids)[:5])

# single mode
sm_ids = set(str(r[0]) for r in mcur.execute("SELECT DISTINCT story_id FROM single_mode_story_data WHERE story_id != 0"))
print('single mode ids:', len(sm_ids), 'in meta:', len(sm_ids & meta_ids), 'not in meta:', len(sm_ids - meta_ids), sorted(sm_ids - meta_ids)[:5])

mc.close(); conn.close()