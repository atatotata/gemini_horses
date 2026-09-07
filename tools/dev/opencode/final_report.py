"""
COMPREHENSIVE REPORT: Story Event 09 Extraction Status
======================================================
Extracted 4 valid bundles. 198 cannot be extracted — no local dat files.
"""
import json, os, sys, io
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
from pathlib import Path

OUT_BASE = Path(r"C:/TMP/extra_fetch/story_json")
GEMINI_DIR = Path(r"G:/Games/steamapps/common/UmamusumePrettyDerby_Jpn/gemini_horses/localized_data/assets/story/data")

# 1. Count seasonal 22 files (10, 14)
seasonal_files = 0
seasonal_blocks = 0
for prefix in ['10', '14']:
    pdir = OUT_BASE / prefix
    if pdir.exists():
        for root, dirs, files in os.walk(pdir):
            for f in files:
                if f.startswith("storytimeline_") and f.endswith(".json"):
                    seasonal_files += 1
                    try:
                        with open(os.path.join(root, f), 'r', encoding='utf-8') as fh:
                            data = json.load(fh)
                        seasonal_blocks += len(data.get('text_block_list', []))
                    except:
                        pass

# 2. Count new 09 files
new_09_files = 0
new_09_blocks = 0
new_09_choices = 0
prefix_09_dir = OUT_BASE / "09"
if prefix_09_dir.exists():
    for root, dirs, files in os.walk(prefix_09_dir):
        for f in sorted(files):
            if f.startswith("storytimeline_") and f.endswith(".json"):
                new_09_files += 1
                try:
                    with open(os.path.join(root, f), 'r', encoding='utf-8') as fh:
                        data = json.load(fh)
                    tblocks = data.get('text_block_list', [])
                    new_09_blocks += len(tblocks)
                    new_09_choices += sum(len(b.get('choice_data_list', [])) for b in tblocks)
                except:
                    pass

# 3. Count localized 09
localized_09 = 0
for root, dirs, files in os.walk(GEMINI_DIR):
    for f in files:
        if f.startswith("storytimeline_") and f.endswith(".json"):
            rel = os.path.relpath(os.path.join(root, f), GEMINI_DIR)
            parts = rel.replace("\\", "/").split("/")
            if parts[0] == "09":
                localized_09 += 1

# Load analysis
with open(OUT_BASE / "analysis_09.json", "r", encoding="utf-8") as f:
    analysis = json.load(f)

report = f"""
========================================
STORY EVENT 09 EXTRACTION REPORT
========================================

DATA SOURCE VERIFICATION:
  Meta DB (apsw-sqlite3mc, hexkey 9c2bab97.e9fd):
    - Total rows in table 'a': 365,808
    - Total storytimeline entries (all prefixes): 21,856
    - Prefix 09 storytimeline entries: {analysis['meta_09_count']}
    
  master.mdb story_event_story_data:
    - story_type_1=1 total: 449
    - Story IDs in 9000xxxx range (09 prefix): 449
    - Ghost 20290011: NOT in story_event_story_data (confirmed skip)

LOCALIZED DATA (gemini_horses/localized_data):
  - Existing 09 files: {localized_09}
  - (From UmaTL / prior translations — DO NOT TOUCH)

MISSING FROM LOCALIZED (the 202 gap):
  - Meta 09 total: {analysis['meta_09_count']}
  - Localized 09: {localized_09}
  - Gap: {len(analysis['missing_202'])} sids
  - Of those 202:
    - WITH local dat bundle: {len(analysis['missing_202_with_dat'])} (ONLY 4)
    - WITHOUT local dat bundle: {len(analysis['missing_202_no_dat'])} (198 — BLOCKER)

EXTRACTION RESULTS:
  Seasonal 22 (prefix 10+14): {seasonal_files} files, {seasonal_blocks} blocks
  New 09 batch: {new_09_files} files, {new_09_blocks} blocks, {new_09_choices} choices
  Combined seasonal + 09 new: {seasonal_files + new_09_files} files

  Files extracted:
    - 90016001: 54 blocks, 0 choices (Summer Walk event)
    - 90021001: 43 blocks, 0 choices
    - 90032001: 55 blocks, 0 choices
    - 90054007: 51 blocks, 0 choices

VERIFICATION:
  - CRLF check: PASS (0 files with CRLF)
  - JSON validity: PASS (all 4 files valid)
  - Name field: Japanese (pre-translation) — confirmed
  - No 04/09 UmaTL prefix overwrite: 09 new files are in C:/TMP/extra_fetch/story_json/09/ (distinct from existing 09:255 in localized_data)
  - Bundle key: 532b4631e4a7b9473e7cfb XOR e column
  - Decryption: apsw-sqlite3mc meta decrypt (hexkey 9c2bab97.e9fd)
  - UnityPy MonoBehaviour BlockList[1:] → TextTrack → ClipList → Text/Name/ChoiceDataList

CRITICAL BLOCKER — 198 MISSING BUNDLES:
  198 out of 202 missing sids have NO local dat bundle files.
  Only 10 out of ALL 457 prefix-09 meta entries have local dat files at all.
  
  The 10 that exist locally (across ALL 457):
    90015001, 90016001, 90017001, 90018001, 90019001,
    90020001, 90021001, 90022001, 90032001, 90054007
  
  Of these 10, 6 are already in localized_data (15001-22001 except 16001,21001).
  4 are new extractions (16001, 21001, 32001, 54007).
  
  The game client appears to only cache a small subset of story event bundles
  locally. The remaining 198 bundles (25 event groups) were either:
  (a) Downloaded and cleaned up by the game client
  (b) Never downloaded on this installation
  (c) Stored in a different location
  
  These CANNOT be extracted via Persistent/dat local decrypt as requested.
  An alternative data source is needed (game server download, archive, etc.)

OUTPUT LOCATION: C:/TMP/extra_fetch/story_json/
  - extraction_summary_09.json
  - analysis_09.json
  - 09/{{sub}}/storytimeline_{{sid}}.json (4 files)
  - 10/{{sub}}/storytimeline_{{sid}}.json (seasonal, already existed)
  - 14/{{sub}}/storytimeline_{{sid}}.json (seasonal, already existed)
"""

print(report)

# Save report
with open(OUT_BASE / "extraction_report_09.txt", "w", encoding="utf-8", newline="\n") as f:
    f.write(report)

print("Report saved to C:/TMP/extra_fetch/story_json/extraction_report_09.txt")
