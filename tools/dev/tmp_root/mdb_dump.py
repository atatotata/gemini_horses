import sqlite3
from collections import Counter
con = sqlite3.connect(r'G:\Games\steamapps\common\UmamusumePrettyDerby_Jpn\UmamusumePrettyDerby_Jpn_Data\Persistent\master\master.mdb')
cur = con.cursor()

tables = ['single_mode_story_data','chara_story_data','main_story_data','campaign_story_data',
          'story_event_story_data','story_extra_story_data','story_extra_event_movie',
          'story_extra_movie_data','map_event_story_data','main_story_custom_load']

def prefix_of(sid):
    return str(sid).zfill(9)[:2]

for t in tables:
    cols = [c[1] for c in cur.execute(f'PRAGMA table_info("{t}")')]
    nrows = cur.execute(f'SELECT COUNT(*) FROM "{t}"').fetchone()[0]
    ncol = {c: None for c in cols}
    print(f"\n=== {t} ({nrows} rows) ===")
    types = [c for c in cols if c.startswith('story_type')]
    ids = [c for c in cols if c.startswith('story_id')]
    has_pair = False
    if types and ids:
        has_pair = True
        d_ne0 = set(); d_t1 = set(); dist_ne0_per_col = Counter()
        for num in sorted({c.replace('story_type_','') for c in types}, key=int):
            tc = f'story_type_{num}'; ic = f'story_id_{num}'
            if ic not in cols: continue
            ne0 = [r[0] for r in cur.execute(f'SELECT "{ic}" FROM "{t}" WHERE "{tc}"!=0 AND "{ic}"!=0')]
            t1  = [r[0] for r in cur.execute(f'SELECT "{ic}" FROM "{t}" WHERE "{tc}"=1 AND "{ic}"!=0')]
            d_ne0.update(ne0); d_t1.update(t1)
            dist_ne0_per_col[tc] = len(set(ne0))
        print("  type!=0 distinct ids:", len(d_ne0), " by prefix:", dict(sorted(Counter(prefix_of(x) for x in d_ne0).items())))
        print("  type==1 distinct ids:", len(d_t1), " by prefix:", dict(sorted(Counter(prefix_of(x) for x in d_t1).items())))
        print("  per-col type!=0:", dict(dist_ne0_per_col))
    else:
        # maybe direct story id columns like story_id or id that embeds timeline
        cand = [c for c in cols if 'story' in c.lower()]
        print("  no type pair. story-ish cols:", cand)
        print("  all cols:", cols)
