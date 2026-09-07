"""Verify extracted home timeline JSON files."""
import json, os, sys
from pathlib import Path

OUT_DIR = Path(r"C:\TMP\home_fetch\story_json\home")

# Count files
all_files = sorted(OUT_DIR.rglob("hometimeline_*.json"))
print(f"Total output files: {len(all_files)}")

# Verify JSON validity + stats
total_blocks = 0
total_choices = 0
non_japanese = 0
empty_files = 0
schema_deviation = 0
sample_shown = 0

for f in all_files:
    try:
        with open(f, "r", encoding="utf-8") as fh:
            data = json.load(fh)
        tbl = data.get("text_block_list", [])
        nb = len(tbl)
        nc = sum(len(b.get("choice_data_list", [])) for b in tbl)
        total_blocks += nb
        total_choices += nc
        if nb == 0:
            empty_files += 1
        # Check for name being non-empty
        for b in tbl:
            name = b.get("name", "")
            if name:
                # Check if name has Japanese characters (CJK range)
                has_jp = any(0x3040 <= ord(c) <= 0x9FFF or 0xF900 <= ord(c) <= 0xFAFF for c in name)
                if not has_jp:
                    non_japanese += 1
                    if sample_shown < 3:
                        print(f"  Non-JP name in {f.name}: {name}")
                        sample_shown += 1
                        break
        # Check schema: should have text_block_list, no_wrap
        keys = set(data.keys())
        expected = {"text_block_list", "no_wrap"}
        if not expected.issubset(keys):
            schema_deviation += 1
            if schema_deviation <= 3:
                print(f"  Schema deviation {f.name}: keys={keys}")
    except json.JSONDecodeError as ex:
        print(f"  INVALID JSON: {f.name}: {ex}")
    except Exception as ex:
        print(f"  ERROR: {f.name}: {ex}")

# Also check existing localized files
LOC_DIR = Path(r"G:\Games\steamapps\common\UmamusumePrettyDerby_Jpn\gemini_horses\localized_data\assets\home\data")
loc_files = sorted(LOC_DIR.rglob("hometimeline_*.json"))
loc_blocks = 0
loc_choices = 0
for f in loc_files:
    with open(f, "r", encoding="utf-8") as fh:
        data = json.load(fh)
    tbl = data.get("text_block_list", [])
    loc_blocks += len(tbl)
    loc_choices += sum(len(b.get("choice_data_list", [])) for b in tbl)

combined_blocks = total_blocks + loc_blocks
combined_choices = total_choices + loc_choices

print(f"\n=== VERIFICATION ===")
print(f"Extracted files: {len(all_files)}")
print(f"Localized files: {len(loc_files)}")
print(f"Combined: {len(all_files) + len(loc_files)}")
print(f"")
print(f"Extracted blocks: {total_blocks}")
print(f"Extracted choices: {total_choices}")
print(f"Localized blocks: {loc_blocks}")
print(f"Localized choices: {loc_choices}")
print(f"Combined blocks: {combined_blocks}")
print(f"Combined choices: {combined_choices}")
print(f"")
print(f"Empty files (0 blocks): {empty_files}")
print(f"Non-JP names: {non_japanese}")
print(f"Schema deviations: {schema_deviation}")

# Show sample file content
print(f"\n=== SAMPLE FILE ===")
sample = all_files[len(all_files)//2]
print(f"File: {sample.name}")
with open(sample, "r", encoding="utf-8") as f:
    data = json.load(f)
print(json.dumps(data, ensure_ascii=False, indent=2)[:1500])

# CRLF check
print(f"\n=== CRLF CHECK ===")
crlf_count = 0
for f in all_files[:20]:
    with open(f, "rb") as fh:
        raw = fh.read()
    if b"\r\n" in raw:
        crlf_count += 1
print(f"Files with CRLF (first 20): {crlf_count}/20")
