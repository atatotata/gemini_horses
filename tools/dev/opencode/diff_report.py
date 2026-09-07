import os, sys, json, sqlite3
from pathlib import Path
from collections import Counter

GAME_DIR = Path(r"G:/Games/steamapps/common/UmamusumePrettyDerby_Jpn")
GEMINI_DATA = GAME_DIR / "gemini_horses/localized_data"
HACHIMI_DATA = GAME_DIR / "hachimi/localized_data_1"
MASTER_PATH = GAME_DIR / "UmamusumePrettyDerby_Jpn_Data/Persistent/master/master.mdb"
UPSTREAM_CACHE = GAME_DIR / "gemini_horses/.upstream_cache.json"

print("==================================================")
print("COMPREHENSIVE TRANSLATION AUDIT & CROSSCHECK DIFF")
print("==================================================")

# 1. UPSTREAM UMATL VS GEMINI_HORSES DICTIONARIES
print("\n--- 1. DICTIONARY COMPARISON ---")

# text_data_dict
with open(GEMINI_DATA / "text_data_dict.json", 'r', encoding='utf-8') as f:
    g_text_data = json.load(f)

g_td_entries = sum(len(v) for v in g_text_data.values())
g_td_cats = len(g_text_data)
print(f"gemini_horses text_data_dict.json: {g_td_entries:,} entries across {g_td_cats} categories")

# CST dict
with open(GEMINI_DATA / "character_system_text_dict.json", 'r', encoding='utf-8') as f:
    g_cst = json.load(f)
g_cst_entries = sum(len(v) for v in g_cst.values())
g_cst_chars = len(g_cst)
print(f"gemini_horses character_system_text_dict.json: {g_cst_entries:,} voice lines across {g_cst_chars} characters")

# localize_dict
with open(GEMINI_DATA / "localize_dict.json", 'r', encoding='utf-8') as f:
    g_loc = json.load(f)
print(f"gemini_horses localize_dict.json: {len(g_loc):,} UI keys")

# 2. STORY TIMELINES
print("\n--- 2. STORY TIMELINES BREAKDOWN ---")
g_stories = {}
for root, dirs, files in os.walk(GEMINI_DATA / "assets/story/data"):
    for f in files:
        if f.startswith('storytimeline_') and f.endswith('.json'):
            sid = f.replace('storytimeline_', '').replace('.json', '')
            rel = os.path.relpath(os.path.join(root, f), GEMINI_DATA / "assets/story/data").replace('\\', '/')
            g_stories[sid] = rel

g_story_prefixes = Counter(sid[:2] for sid in g_stories)
print(f"Total story timeline files in gemini_horses: {len(g_stories):,}")
print("Breakdown by story prefix:")
for p, cnt in sorted(g_story_prefixes.items()):
    desc = "Other"
    if p == "00": desc = "Tutorial / Prologue"
    elif p == "01": desc = "Chara Intro Stories"
    elif p == "02": desc = "Main Story Chapters"
    elif p == "04": desc = "Chara Bond Stories (Ep 1-7)"
    elif p == "08": desc = "Event Prologues"
    elif p == "09": desc = "Chara Event Stories"
    elif p == "10": desc = "Special Animations/Movies"
    elif p == "40": desc = "Career Main Scenario Events"
    elif p == "50": desc = "Career Horsegirl Events"
    elif p == "80": desc = "Support Card Events (Group/Other)"
    elif p == "82": desc = "Support Card Events (SR)"
    elif p == "83": desc = "Support Card Events (SSR)"
    print(f"  Prefix {p} ({desc:35s}): {cnt:5d} files")

# Upstream cache
upstream_stories = {}
if UPSTREAM_CACHE.exists():
    with open(UPSTREAM_CACHE, 'r', encoding='utf-8') as f:
        uc = json.load(f)
    for p in uc:
        if 'assets/story/data/' in p and p.endswith('.json'):
            fname = os.path.basename(p)
            sid = fname.replace('storytimeline_', '').replace('.json', '')
            upstream_stories[sid] = p

print(f"\nTotal story timeline files in Upstream UmaTL: {len(upstream_stories):,}")
u_story_prefixes = Counter(sid[:2] for sid in upstream_stories)
print("Breakdown by story prefix in Upstream UmaTL:")
for p, cnt in sorted(u_story_prefixes.items()):
    print(f"  Prefix {p}: {cnt:5d} files")

# Check if ANY upstream file is missing from gemini_horses
missing_from_gemini = set(upstream_stories.keys()) - set(g_stories.keys())
print(f"\nUpstream stories missing from gemini_horses: {len(missing_from_gemini)}")
extra_in_gemini = set(g_stories.keys()) - set(upstream_stories.keys())
print(f"Additional stories translated in gemini_horses: {len(extra_in_gemini):,}")

# 3. OPTION B CANDIDATES IN MASTER.MDB
print("\n--- 3. CAREER EVENT SCOPE (SINGLE_MODE_STORY_DATA) ---")
mconn = sqlite3.connect(str(MASTER_PATH))
mc = mconn.cursor()

mc.execute("SELECT DISTINCT story_id FROM single_mode_story_data WHERE gallery_flag = 1 AND story_id != 0")
flag1_sids = set(str(r[0]) for r in mc.fetchall())

mc.execute("SELECT DISTINCT story_id FROM single_mode_story_data WHERE gallery_flag = 3 AND story_id != 0")
flag3_sids = set(str(r[0]) for r in mc.fetchall())
mconn.close()

f1_overlap = flag1_sids.intersection(g_stories.keys())
f1_net_missing = flag1_sids - g_stories.keys()
print(f"Horsegirl Career Events (gallery_flag = 1):")
print(f"  Total in master.mdb: {len(flag1_sids):,}")
print(f"  Already translated: {len(f1_overlap):,}")
print(f"  Net missing:        {len(f1_net_missing):,}")

f3_overlap = flag3_sids.intersection(g_stories.keys())
f3_net_missing = flag3_sids - g_stories.keys()
print(f"\nMain Scenario Career Events (gallery_flag = 3):")
print(f"  Total in master.mdb: {len(flag3_sids):,}")
print(f"  Already translated: {len(f3_overlap):,}")
print(f"  Net missing:        {len(f3_net_missing):,}")
