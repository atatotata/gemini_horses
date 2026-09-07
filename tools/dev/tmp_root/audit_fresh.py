#!/usr/bin/env python3
"""Fresh meta vs localized_data audit after full data download."""
import apsw, sqlite3, json, os, re
from pathlib import Path
from collections import Counter

KEY = "9c2bab97bcf8c0c4f1a9ea7881a213f6c9ebf9d8d4c6a8e43ce5a259bde7e9fd"
META = r'C:\TMP\meta_fresh.bin'
MDB = r'G:\Games\steamapps\common\UmamusumePrettyDerby_Jpn\UmamusumePrettyDerby_Jpn_Data\Persistent\master\master.mdb'
DAT = Path(r'G:\Games\steamapps\common\UmamusumePrettyDerby_Jpn\UmamusumePrettyDerby_Jpn_Data\Persistent\dat')
LOC = Path(r'G:\Games\steamapps\common\UmamusumePrettyDerby_Jpn\gemini_horses\localized_data')

re_plain = re.compile(r'^storytimeline_(\d+)\.json$')
re_ast = re.compile(r'^ast_(dot|ruby)_storytimeline_(\d+)\.json$')
re_home = re.compile(r'^hometimeline_[^/]+\.json$')
re_lyric = re.compile(r'^m(\d+)_lyrics\.json$')
re_sr = re.compile(r'^storyrace_(\d+)\.json$')

out = {}

# ============ 1. META ============
conn = apsw.Connection(f'file:{META}?hexkey={KEY}', flags=apsw.SQLITE_OPEN_READONLY | apsw.SQLITE_OPEN_URI)
cur = conn.cursor()
out['meta_total'] = cur.execute('SELECT COUNT(*) FROM a').fetchone()[0]

meta_plain = {}   # sid(str9) -> prefix
meta_prefix = Counter()
meta_by_prefix_plain = Counter()
rows = cur.execute("SELECT n FROM a WHERE n LIKE 'story/data/%'").fetchall()
ast_story = Counter()
res_count = 0
for (n,) in rows:
    p = n.split('/')
    if len(p) == 5 and p[4].startswith('storytimeline_'):
        sid = p[4][len('storytimeline_'):]
        if sid.isdigit():
            meta_plain[sid] = p[2]
            meta_by_prefix_plain[p[2]] += 1
    elif len(p) == 6 and p[4] == 'resourcelist':
        res_count += 1
    elif len(p) == 5 and p[4].startswith('ast_'):
        ast_story[p[2]] += 1
out['meta_story_plain_total'] = len(meta_plain)
out['meta_story_plain_by_prefix'] = dict(sorted(meta_by_prefix_plain.items()))
out['meta_story_ast'] = dict(ast_story)
out['meta_story_resources'] = res_count

# home hometimeline plain
rows = cur.execute("SELECT n FROM a WHERE n LIKE 'home/data/%'").fetchall()
home_meta = 0
for (n,) in rows:
    p = n.split('/')
    if len(p) == 5 and p[4].startswith('hometimeline_'):
        home_meta += 1
out['meta_home_plain'] = home_meta

# lyrics meta
lyr = cur.execute("SELECT n FROM a WHERE n LIKE 'live/musicscores/%/m%_lyrics'").fetchall()
out['meta_lyrics'] = len(lyr)
# storyrace text meta
sr_rows = cur.execute("SELECT n FROM a WHERE n LIKE 'race/storyrace/text/%'").fetchall()
sr_meta_ids = set()
for (n,) in sr_rows:
    b = n.split('/')[-1]
    if b.startswith('storyrace_'):
        sr_meta_ids.add(b[len('storyrace_'):])
out['meta_storyrace_text'] = len(sr_meta_ids)
conn.close()

# ============ 2. LOCALIZED ============
local_plain = {}; local_ast = 0; other = 0
prefix_counter = Counter()
for f in (LOC / 'assets' / 'story' / 'data').rglob('*.json'):
    m = re_plain.match(f.name)
    if m:
        sid = m.group(1)
        local_plain[sid] = f.parts[-4] if len(f.parts) >= 4 else '?'
        prefix_counter[sid[:2]] += 1
    elif re_ast.match(f.name):
        local_ast += 1
    else:
        other += 1
# prefix via directory structure instead of sid[:2] (same for 9-digit, safer dir-based)
dir_prefix = Counter()
for f in (LOC / 'assets' / 'story' / 'data').rglob('storytimeline_*.json'):
    rel = f.relative_to(LOC / 'assets' / 'story' / 'data')
    dir_prefix[rel.parts[0]] += 1
out['local_story_total_files'] = sum(dir_prefix.values())
out['local_story_plain_ids'] = len(local_plain)
out['local_story_ast'] = local_ast
out['local_story_other'] = other
out['local_story_by_prefix'] = dict(sorted(dir_prefix.items()))

# per-prefix localized distinct plain ids (using dir prefix)
loc_ids_by_prefix = Counter()
for sid in local_plain:
    loc_ids_by_prefix[sid[:2]] += 1
out['local_story_plain_by_prefix'] = dict(sorted(loc_ids_by_prefix.items()))

# home localized
home_local = list((LOC / 'assets' / 'home' / 'data').rglob('*.json'))
out['local_home_files'] = len(home_local)
# lyrics localized
lyr_local = list((LOC / 'assets' / 'lyrics').glob('*_lyrics.json'))
out['local_lyrics'] = len(lyr_local)
# storyrace localized
sr_local = list((LOC / 'assets' / 'race' / 'storyrace').rglob('storyrace_*.json'))
out['local_storyrace'] = len(sr_local)

# ============ 3. MASTER SOURCE GAPS ============
con = sqlite3.connect(MDB)
mc = con.cursor()

def distinct_pairs(table):
    cols = [c[1] for c in mc.execute(f'PRAGMA table_info("{table}")')]
    types = sorted({c.replace('story_type_', '') for c in cols if c.startswith('story_type_')}, key=int)
    s = set()
    for num in types:
        tc, ic = f'story_type_{num}', f'story_id_{num}'
        if ic in cols:
            s.update(r[0] for r in mc.execute(f'SELECT "{ic}" FROM "{table}" WHERE "{tc}"!=0 AND "{ic}"!=0'))
    return {str(x).zfill(9) for x in s}

single = {str(x).zfill(9) for x in
          (r[0] for r in mc.execute('SELECT DISTINCT story_id FROM single_mode_story_data WHERE story_id!=0'))}
chara = {str(x).zfill(9) for x in (r[0] for r in mc.execute('SELECT DISTINCT story_id FROM chara_story_data WHERE story_id!=0'))}
main = distinct_pairs('main_story_data')
event = distinct_pairs('story_event_story_data')
extra = distinct_pairs('story_extra_story_data')
map2 = {str(x).zfill(9) for x in (r[0] for r in mc.execute('SELECT DISTINCT story_id FROM map_event_story_data WHERE story_id!=0'))}
con.close()

def cover(name, s):
    im = s & set(meta_plain)
    il = s & set(local_plain)
    gap_ids = im - set(local_plain)
    rec = {
        'source_total': len(s),
        'in_meta': len(im),
        'in_local': len(il),
        'gap_meta_not_local': len(gap_ids),
        'gap_sample': sorted(gap_ids)[:12],
        'not_in_meta': len(s - im),
    }
    out[f'cov_{name}'] = rec
    print(f"{name:12s} src={len(s):6d} meta={len(im):6d} local={len(il):6d} gap={len(gap_ids):6d} notInMeta={rec['not_in_meta']:6d}")
    return rec

print("== master source coverage (ids 9-digit) ==")
cover('single_mode', single)
cover('chara', chara)
cover('main', main)
cover('event', event)
cover('extra', extra)
cover('map_event', map2)
union = single | chara | main | event | extra | map2
print(f"union all sources={len(union)} ; meta story plain={len(meta_plain)}")

# Also single_mode distinct incl short_story_id
con = sqlite3.connect(MDB); mc = con.cursor()
single2 = set()
for r in mc.execute('SELECT DISTINCT story_id, short_story_id FROM single_mode_story_data'):
    a, b = r
    if a and a != 0: single2.add(str(a).zfill(9))
    if b and b != 0: single2.add(str(b).zfill(9))
con.close()
print(f"single_mode distinct story_id (no short): {len(single)} ; incl short_story_id: {len(single2)}")
im2 = single2 & set(meta_plain)
print(f"single2 in meta: {len(im2)}")

# ============ 4. DAT bundle count ============
n_files = 0
for root, dirs, files in os.walk(DAT):
    n_files += len(files)
out['dat_file_count'] = n_files
print("dat bundle files:", n_files)

with open(r'C:\TMP\audit_fresh_results.json', 'w') as f:
    json.dump(out, f, indent=1, default=str)
print("saved C:\\TMP\\audit_fresh_results.json")
