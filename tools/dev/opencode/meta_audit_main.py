# Umamusume meta DB + localized_data coverage audit
import apsw, os, sqlite3, json, sys
from collections import Counter, defaultdict

GAME = r'G:\Games\steamapps\common\UmamusumePrettyDerby_Jpn'
META = GAME + r'\UmamusumePrettyDerby_Jpn_Data\Persistent\meta'
MASTER = GAME + r'\UmamusumePrettyDerby_Jpn_Data\Persistent\master\master.mdb'
LOCAL = GAME + r'\gemini_horses\localized_data\assets'

DB_BASE_KEY = b'\xF1\x70\xCE\xA4\xDF\xCE\xA3\xE1\xA5\xD8\xC7\x0B\xD1\x00\x00\x00'
DB_KEY = b'\x6D\x5B\x65\x33\x63\x36\x63\x25\x54\x71\x2D\x73\x50\x53\x63\x38\x6D\x34\x37\x7B\x35\x63\x70\x23\x37\x34\x53\x29\x73\x43\x36\x33'
key = bytearray(DB_KEY)
for i in range(len(key)):
    key[i] ^= DB_BASE_KEY[i % 13]
final = bytes(key)

conn = apsw.Connection(META)
conn.pragma('cipher', 'chacha20')
conn.pragma('hexkey', final.hex())
c = conn.cursor()

# ---------- 1. bucket meta by prefix ----------
def prefix_bucket(n):
    # top-level prefix with 2nd-level for the big ones
    parts = n.split('/')
    if len(parts) < 2:
        return n
    return parts[0] + '/' + parts[1]

rows = c.execute("SELECT n FROM a").fetchall()
meta_all = [r[0] for r in rows]
print('total meta rows:', len(meta_all))

buckets = Counter()
for n in meta_all:
    if n.startswith('//'):
        buckets['manifest'] += 1
    else:
        buckets[prefix_bucket(n)] += 1

# ---------- 2. localized_data inventory ----------
local_files = []
for root, dirs, files in os.walk(LOCAL):
    for f in files:
        rel = os.path.relpath(os.path.join(root, f), LOCAL).replace('\\', '/')
        local_files.append(rel)
print('localized_data total files:', len(local_files))

local_prefix = Counter()
for f in local_files:
    parts = f.split('/')
    local_prefix[parts[0] + ('/' + parts[1] if len(parts) > 1 else '')] += 1

# ---------- storytimeline / hometimeline sets ----------
meta_story_tl = set()
meta_story_res = set()
meta_home_tl = set()
meta_race_perf = set()
meta_lyrics = set()
meta_flash_txt = set()
meta_outgame_txt = set()

for n in meta_all:
    if n.startswith('story/data/'):
        base = n.split('/')[-1]
        if 'resourcelist' in n:
            if base.startswith('storytimeline_'):
                meta_story_res.add(base)
        elif base.startswith('storytimeline_'):
            meta_story_tl.add(base.replace('storytimeline_', ''))
    elif n.startswith('home/data/') and '_hometimeline_' in n:
        base = n.split('/')[-1]
        meta_home_tl.add(base)
    elif n.startswith('race/storyrace/performance/'):
        meta_race_perf.add(n.split('/')[-1])
    elif n.startswith('live/musicscores/') and n.endswith('_lyrics'):
        meta_lyrics.add(n.split('/')[-1])
    elif n.startswith('uianimation/flash/') and ('txt' in n.split('/')[-1] or 'text' in n.split('/')[-1]):
        meta_flash_txt.add(n)
    elif n.startswith('outgame/') and ('textsetting' in n or 'text_setting' in n):
        meta_outgame_txt.add(n)

# localized storytimeline ids
local_story_ids = set()
for f in local_files:
    base = os.path.basename(f)
    if base.startswith('storytimeline_') and base.endswith('.json'):
        local_story_ids.add(base[len('storytimeline_'):-len('.json')])
local_home_ids = set()
for f in local_files:
    base = os.path.basename(f)
    if base.startswith('hometimeline_') and base.endswith('.json'):
        local_home_ids.add(base[len('hometimeline_'):-len('.json')])
local_race = set()
for f in local_files:
    if f.startswith('race/') and f.endswith('.json'):
        local_race.add(os.path.basename(f))
local_lyric_names = set()
for f in local_files:
    if f.startswith('lyrics/') and f.endswith('.json'):
        local_lyric_names.add(os.path.basename(f))

print()
print('=== 2. story/data coverage ===')
print('meta storytimeline_* entries:', len(meta_story_tl))
print('meta storytimeline_*_resources:', len(meta_story_res))
print('localized storytimeline_*.json:', len(local_story_ids))
covered = len(meta_story_tl & local_story_ids)
print('storytimeline ids in BOTH:', covered)
print('in meta not localized:', len(meta_story_tl - local_story_ids))
print('localized not in meta (stale/extra):', len(local_story_ids - meta_story_tl))

print()
print('=== 2b. home/data coverage ===')
print('meta home hometimeline entries (incl ast_dot/ast_ruby variants):', len(meta_home_tl))
print('localized hometimeline_*.json:', len(local_home_ids))
# meta home timeline ids are like ast_dot_hometimeline_00000_01_1114003 -> hometimeline_00000_01_1114003
meta_home_ids = set()
for b in meta_home_tl:
    idx = b.find('hometimeline_')
    if idx >= 0:
        meta_home_ids.add(b[idx:])
print('meta home ids normalized:', len(meta_home_ids))
print('in meta not localized:', len(meta_home_ids - local_home_ids))
print('localized not in meta:', len(local_home_ids - meta_home_ids))

print()
print('=== 2c. race storyrace coverage ===')
print('meta race/storyrace/performance:', len(meta_race_perf))
print('localized race/*.json:', len(local_race))
perf_ids = set()
for b in meta_race_perf:
    if b.startswith('ast_storyrace_performance_'):
        perf_ids.add(b[len('ast_storyrace_performance_'):])
local_race_ids = set()
for b in local_race:
    if b.startswith('storyrace_') and b.endswith('.json'):
        local_race_ids.add(b[len('storyrace_'):-len('.json')])
print('meta perf ids:', len(perf_ids), 'localized storyrace ids:', len(local_race_ids))
print('perf in meta not localized:', len(perf_ids - local_race_ids))
print('localized not in meta:', len(local_race_ids - perf_ids))

print()
print('=== 2d. lyrics coverage ===')
print('meta lyrics assets:', len(meta_lyrics))
print('localized lyrics files:', len(local_lyric_names))
meta_lyr_ids = set()
for b in meta_lyrics:
    if b.endswith('_lyrics'):
        meta_lyr_ids.add(b)
local_lyr_ids = set()
for b in local_lyric_names:
    if b.endswith('_lyrics.json'):
        local_lyr_ids.add(b[:-len('.json')])
print('in meta not localized:', len(meta_lyr_ids - local_lyr_ids), sorted(meta_lyr_ids - local_lyr_ids)[:10])

print()
print('=== 3. master.mdb story id cross-check ===')
mconn = sqlite3.connect(MASTER)
mc = mconn.cursor()
def distinct_ids(table, col):
    return set(str(r[0]) for r in mc.execute('SELECT DISTINCT %s FROM %s WHERE %s != 0' % (col, table, col)))
sm_ids = distinct_ids('single_mode_story_data', 'story_id')
ch_ids = distinct_ids('chara_story_data', 'story_id')
mn_ids = distinct_ids('main_story_data', 'story_id')
print('single_mode_story_data distinct story_id:', len(sm_ids))
print('chara_story_data distinct story_id:', len(ch_ids))
print('main_story_data distinct story_id:', len(mn_ids))
all_master = sm_ids | ch_ids | mn_ids
print('union:', len(all_master))

in_meta = all_master & meta_story_tl
in_local = all_master & local_story_ids
print('master ids in meta:', len(in_meta))
print('master ids in localized:', len(in_local))
print('master ids NOT in meta:', len(all_master - meta_story_tl))
print('master ids in meta but NOT localized:', len(in_meta - local_story_ids))
print('  (chara:', len((ch_ids & meta_story_tl) - local_story_ids), 'single:', len((sm_ids & meta_story_tl) - local_story_ids), 'main:', len((mn_ids & meta_story_tl) - local_story_ids), ')')

# list gaps
gaps = sorted(in_meta - local_story_ids)
print('gap count:', len(gaps))
print('gap samples:', gaps[:30])

print()
print('=== 4. non-JSON-text asset buckets ===')
for b, cnt in buckets.most_common(40):
    print('%40s %8d' % (b, cnt))
mconn.close()
conn.close()