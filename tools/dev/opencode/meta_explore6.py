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
meta_story_tl = set()
meta_home_plain = set()
for (n,) in c.execute("SELECT n FROM a"):
    if n.startswith('story/data/') and '/resourcelist/' not in n:
        base = n.split('/')[-1]
        if base.startswith('storytimeline_'):
            meta_story_tl.add(base.replace('storytimeline_', ''))
    elif n.startswith('home/data/') and '/resourcelist/' not in n:
        base = n.split('/')[-1]
        if base.startswith('hometimeline_'):
            meta_home_plain.add(base)

mc = sqlite3.connect(r'G:\Games\steamapps\common\UmamusumePrettyDerby_Jpn\UmamusumePrettyDerby_Jpn_Data\Persistent\master\master.mdb')
mcur = mc.cursor()

print('meta storytimeline ids:', len(meta_story_tl))
print('meta home plain hometimeline ids:', len(meta_home_plain))
print()
print('=== main_story_data story_id_1 sample + meta presence ===')
for r in mcur.execute("SELECT id, part_id, episode_index, story_id_1 FROM main_story_data LIMIT 8"):
    print(r, 'in_meta=', str(r[3]) in meta_story_tl)
print()
# all story_id_N columns
cols = ['story_id_1','story_id_2','story_id_3','story_id_4','story_id_5']
mn_ids = set()
for col in cols:
    for (v,) in mcur.execute('SELECT DISTINCT %s FROM main_story_data WHERE %s != 0' % (col, col)):
        mn_ids.add(str(v))
print('main_story_data all story_id_N union:', len(mn_ids), 'in meta:', len(mn_ids & meta_story_tl))
# which col is the real storytimeline? check per-col overlap
for col in cols:
    s = set(str(r[0]) for r in mcur.execute('SELECT DISTINCT %s FROM main_story_data WHERE %s != 0' % (col, col)))
    print('  %s: %d distinct, %d in meta' % (col, len(s), len(s & meta_story_tl)))

print()
sm_ids = set(str(r[0]) for r in mcur.execute("SELECT DISTINCT story_id FROM single_mode_story_data WHERE story_id != 0"))
ch_ids = set(str(r[0]) for r in mcur.execute("SELECT DISTINCT story_id FROM chara_story_data WHERE story_id != 0"))
print('single_mode_story_data distinct story_id:', len(sm_ids), 'in meta:', len(sm_ids & meta_story_tl))
print('chara_story_data distinct story_id:', len(ch_ids), 'in meta:', len(ch_ids & meta_story_tl))

# home: are meta home ids matching localized naming? sample
print()
print('meta home plain sample:', sorted(meta_home_plain)[:5])
import os
local_home = set()
for root, dirs, files in os.walk(r'G:\Games\steamapps\common\UmamusumePrettyDerby_Jpn\gemini_horses\localized_data\assets\home'):
    for f in files:
        if f.startswith('hometimeline_') and f.endswith('.json'):
            local_home.add(f[:-5])
print('local home sample:', sorted(local_home)[:5])
print('meta-home not local:', len(meta_home_plain - local_home))
print('local not meta-home:', len(local_home - meta_home_plain))
print('samples missing:', sorted(meta_home_plain - local_home)[:8])
mc.close(); conn.close()