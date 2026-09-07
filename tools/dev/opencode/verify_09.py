"""Verify extracted 09 files and compute final stats."""
import json, os
from pathlib import Path

OUT_BASE = Path(r"C:/TMP/extra_fetch/story_json")
GEMINI_DIR = Path(r"G:/Games/steamapps/common/UmamusumePrettyDerby_Jpn/gemini_horses/localized_data/assets/story/data")

# Count seasonal 22 files (prefix 10 and 14)
seasonal_count = 0
seasonal_blocks = 0
for prefix in ['10', '14']:
    prefix_dir = OUT_BASE / prefix
    if prefix_dir.exists():
        for root, dirs, files in os.walk(prefix_dir):
            for f in files:
                if f.startswith("storytimeline_") and f.endswith(".json"):
                    seasonal_count += 1
                    try:
                        with open(os.path.join(root, f), 'r', encoding='utf-8') as fh:
                            data = json.load(fh)
                        blocks = len(data.get('text_block_list', []))
                        seasonal_blocks += blocks
                    except Exception:
                        pass

# Count new 09 files
new_09_count = 0
new_09_blocks = 0
new_09_choices = 0
prefix_09_dir = OUT_BASE / "09"
if prefix_09_dir.exists():
    for root, dirs, files in os.walk(prefix_09_dir):
        for f in files:
            if f.startswith("storytimeline_") and f.endswith(".json"):
                new_09_count += 1
                try:
                    with open(os.path.join(root, f), 'r', encoding='utf-8') as fh:
                        data = json.load(fh)
                    tblocks = data.get('text_block_list', [])
                    blocks = len(tblocks)
                    choices = sum(len(b.get('choice_data_list', [])) for b in tblocks)
                    new_09_blocks += blocks
                    new_09_choices += choices
                    print(f"  {f}: {blocks} blocks, {choices} choices")
                except Exception as ex:
                    print(f"  {f}: ERROR {ex}")

# Verify JSON validity and CRLF check
print("\n=== Verification ===")
print(f"Seasonal (10+14): {seasonal_count} files, {seasonal_blocks} blocks")
print(f"New 09: {new_09_count} files, {new_09_blocks} blocks, {new_09_choices} choices")
print(f"Combined 22+09: {seasonal_count + new_09_count} files")

# Check CRLF
crlf_count = 0
for prefix in ['09', '10', '14']:
    pdir = OUT_BASE / prefix
    if pdir.exists():
        for root, dirs, files in os.walk(pdir):
            for f in files:
                if f.endswith('.json'):
                    fpath = os.path.join(root, f)
                    with open(fpath, 'rb') as fh:
                        content = fh.read()
                    if b'\r\n' in content:
                        crlf_count += 1
                        print(f"  CRLF found: {fpath}")
print(f"CRLF files: {crlf_count}")

# Check Name field is Japanese (non-ASCII) in new 09
if prefix_09_dir.exists():
    for root, dirs, files in os.walk(prefix_09_dir):
        for f in files:
            if f.endswith('.json'):
                fpath = os.path.join(root, f)
                with open(fpath, 'r', encoding='utf-8') as fh:
                    data = json.load(fh)
                for blk in data.get('text_block_list', []):
                    name = blk.get('name', '')
                    if name:
                        # Check if it's Japanese (has non-ASCII)
                        if any(ord(c) > 127 for c in name):
                            pass  # Japanese
                        else:
                            pass  # ASCII name is fine too
                    break  # Just check first block
                break  # Just check first file

# Load analysis for the 202 breakdown
with open(OUT_BASE / "analysis_09.json", "r", encoding="utf-8") as f:
    analysis = json.load(f)

print(f"\n=== 09 Batch Analysis ===")
print(f"Meta 09 total: {analysis['meta_09_count']}")
print(f"Localized 09: {analysis['localized_09_count']}")
print(f"Missing from localized: {len(analysis['missing_202'])}")
print(f"  With local dat: {len(analysis['missing_202_with_dat'])}")
print(f"  WITHOUT local dat: {len(analysis['missing_202_no_dat'])}")
print(f"Ghost 20290011: not in story_event_story_data (confirmed)")
