# FINAL: Umamusume meta DB + localized_data coverage audit
import apsw, os, sqlite3
from collections import Counter

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
meta_rows = c.execute("SELECT n FROM a").fetchall()
print('total meta rows:', len(meta_rows))

# ---- classify each meta path ----
def classify(n):
    if n.startswith('//'):
        return ('manifest', None)
    parts = n.split('/')
    top = parts[0]
    base = parts[-1]
    if top == 'story':
        if 'resourcelist' in n:
            return ('story resourcelist', None)
        if base.startswith('storytimeline_'):
            return ('story/data timeline', base[len('storytimeline_'):])
        if base.startswith('ast_ruby_') or base.startswith('ast_dot_'):
            return ('story ast_ruby/dot', None)
        return ('story other', None)
    if top == 'home':
        if 'resourcelist' in n:
            return ('home resourcelist', None)
        if base.startswith('hometimeline_'):
            return ('home/data timeline', base[len('hometimeline_'):])
        if '_hometimeline_' in base:
            return ('home ast_* hometimeline', None)
        return ('home other', None)
    if top == 'race':
        if base.startswith('ast_storyrace_performance_'):
            return ('race storyrace perf', base[len('ast_storyrace_performance_'):])
        if base.startswith('storyrace_'):
            return ('race storyrace other', None)
        return ('race other', None)
    if top == 'live':
        if base.endswith('_lyrics'):
            return ('live lyrics', base)
        return ('live other', None)
    if top == 'lipsync':
        return ('lipsync', None)
    if top == 'sound':
        return ('sound', None)
    if top == 'chara':
        return ('chara', None)
    if top == '3d' or top == 'cutt' or top == 'mob':
        return ('3d/cutt/mob', None)
    if top == 'sourceresources':
        return ('sourceresources', None)
    if top == 'outgame':
        return ('outgame', None)
    if top == 'uianimation':
        return ('uianimation', None)
    if top == 'single':
        return ('single', None)
    if top == 'supportcard':
        return ('supportcard', None)
    if top == 'bg':
        return ('bg', None)
    if top == 'paddock':
        return ('paddock', None)
    if top == 'item':
        return ('item', None)
    if top == 'gacha' or top == 'gachaselect':
        return ('gacha', None)
    if top == 'movie':
        return ('movie', None)
    if top == 'guide':
        return ('guide', None)
    if top == 'storyevent':
        return ('storyevent', None)
    if top == 'atlas':
        return ('atlas', None)
    if top == 'heroes':
        return ('heroes', None)
    if top == 'teambuilding':
        return ('teambuilding', None)
    if top == 'collectevent':
        return ('collectevent', None)
    if top == 'transferevent':
        return ('transferevent', None)
    if top == 'ratingrace':
        return ('ratingrace', None)
    if top == 'minigame':
        return ('minigame', None)
    if top == 'jobs':
        return ('jobs', None)
    if top == 'mapevent':
        return ('mapevent', None)
    if top == 'announce':
        return ('announce', None)
    if top == 'loginbonus':
        return ('loginbonus', None)
    if top == 'font':
        return ('font', None)
    if top == 'imageeffect':
        return ('imageeffect', None)
    if top == 'shader':
        return ('shader', None)
    return ('other:' + top, None)

meta_cls = Counter()
meta_ids = {}
for (n,) in meta_rows:
    cls, idv = classify(n)
    meta_cls[cls] += 1
    if idv is not None:
        meta_ids.setdefault(cls, set()).add(idv)

# ---- localized files ----
local_files = []
for root, dirs, files in os.walk(LOCAL):
    for f in files:
        rel = os.path.relpath(os.path.join(root, f), LOCAL).replace('\\', '/')
        local_files.append(rel)

def local_cls(rel):
    parts = rel.split('/')
    base = parts[-1]
    top = parts[0]
    if top == 'story' and base.startswith('storytimeline_') and base.endswith('.json'):
        return ('story/data timeline', base[len('storytimeline_'):-5])
    if top == 'home' and base.startswith('hometimeline_') and base.endswith('.json'):
        return ('home/data timeline', base[len('hometimeline_'):-5])
    if top == 'race' and base.startswith('storyrace_') and base.endswith('.json'):
        return ('race storyrace perf', base[len('storyrace_'):-5])
    if top == 'lyrics' and base.endswith('_lyrics.json'):
        return ('live lyrics', base[:-5])
    if top == 'movies':
        return ('movie', None)
    if top == 'textures':
        return ('textures', None)
    if top == 'atlas':
        return ('atlas', None)
    if top == 'an_texture_sets':
        return ('an_texture_sets', None)
    return ('local-other:' + top, None)

local_cls_count = Counter()
local_ids = {}
for rel in local_files:
    cls, idv = local_cls(rel)
    local_cls_count[cls] += 1
    if idv is not None:
        local_ids.setdefault(cls, set()).add(idv)

print()
print('%-32s %8s %8s %8s %8s' % ('asset bucket', 'meta', 'local', 'cov%', 'gap'))
print('-' * 70)
order = ['story/data timeline', 'home/data timeline', 'race storyrace perf', 'live lyrics',
         'story resourcelist', 'home resourcelist', 'story ast_ruby/dot', 'home ast_* hometimeline',
         'lipsync', 'sound', 'chara', '3d/cutt/mob', 'sourceresources', 'outgame', 'uianimation',
         'race other', 'live other', 'single', 'supportcard', 'bg', 'paddock', 'item', 'gacha',
         'movie', 'guide', 'storyevent', 'atlas', 'heroes', 'teambuilding', 'collectevent',
         'transferevent', 'ratingrace', 'minigame', 'jobs', 'mapevent', 'announce', 'loginbonus',
         'font', 'imageeffect', 'shader', 'manifest', 'story other', 'home other', 'textures',
         'an_texture_sets', 'local-other:lyrics']
tot_meta = tot_local = tot_cov = 0
for cls in order:
    m = meta_cls.get(cls, 0)
    l = local_cls_count.get(cls, 0)
    cov = (min(l, m) / m * 100) if m else 0.0
    if cls in ('story/data timeline', 'home/data timeline', 'race storyrace perf', 'live lyrics'):
        gap = len(meta_ids.get(cls, set()) - local_ids.get(cls, set()))
    else:
        gap = max(0, m - l)
    tot_meta += m; tot_local += l
    if m:
        tot_cov += min(m, l)
    print('%-32s %8d %8d %7.1f%% %8d' % (cls, m, l, cov, gap))

print('-' * 70)
print('%-32s %8d %8d %7.1f%%' % ('TOTAL', tot_meta, tot_local, tot_cov / tot_meta * 100 if tot_meta else 0))

# ---- step 2: story/data detail ----
print()
print('=== STORY/DATA DETAIL ===')
st_meta = meta_ids.get('story/data timeline', set())
st_local = local_ids.get('story/data timeline', set())
print('meta storytimeline ids:', len(st_meta))
print('localized storytimeline files:', len(st_local))
print('covered:', len(st_meta & st_local), ' gap:', len(st_meta - st_local))

mc = sqlite3.connect(MASTER)
mcur = mc.cursor()
sm_ids = set(str(r[0]) for r in mcur.execute("SELECT DISTINCT story_id FROM single_mode_story_data WHERE story_id != 0"))
ch_ids = set(str(r[0]).zfill(9) for r in mcur.execute("SELECT DISTINCT story_id FROM chara_story_data WHERE story_id != 0"))
mn_ids = set(str(r[0]) for r in mcur.execute("SELECT DISTINCT story_id_1 FROM main_story_data WHERE story_id_1 != 0"))
print()
print('single_mode_story_data: %d ids -> in meta %d, in localized %d, meta-not-localized %d' % (
    len(sm_ids), len(sm_ids & st_meta), len(sm_ids & st_local), len((sm_ids & st_meta) - st_local)))
sm_gap = sorted((sm_ids & st_meta) - st_local)
print('  sample gaps:', sm_gap[:15])
print()
print('chara_story_data (padded 9): %d ids -> in meta %d, in localized %d, meta-not-localized %d' % (
    len(ch_ids), len(ch_ids & st_meta), len(ch_ids & st_local), len((ch_ids & st_meta) - st_local)))
ch_gap = sorted((ch_ids & st_meta) - st_local)
print('  sample gaps:', ch_gap[:15])
print()
print('main_story_data story_id_1: %d ids -> in meta %d (story_id_1 is NOT a timeline id; main story timelines live under 100/ prefix)' % (
    len(mn_ids), len(mn_ids & st_meta)))
mn_timelines = sorted(i for i in st_meta if i.startswith('100'))
print('  main-story timeline ids (100 prefix):', len(mn_timelines), 'in localized:', len(set(mn_timelines) & st_local))

print()
print('=== HOME/DATA DETAIL ===')
hm_meta = meta_ids.get('home/data timeline', set())
hm_local = local_ids.get('home/data timeline', set())
print('meta hometimeline ids:', len(hm_meta))
print('localized hometimeline files:', len(hm_local))
print('covered:', len(hm_meta & hm_local), 'gap:', len(hm_meta - hm_local))
print('sample gaps:', sorted(hm_meta - hm_local)[:10])

mc.close(); conn.close()