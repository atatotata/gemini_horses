#!/usr/bin/env python3
"""Verification: check all extracted files."""
import os, json, glob

OUTPUT_BASE = r"C:\TMP\remaining_fetch\story_json"
PREFIXES = ["50", "40", "11", "80", "83"]

# Count files per prefix
total_files = 0
total_blocks = 0
total_choices = 0
total_chars = 0
crlf_count = 0
invalid_json = 0
empty_files = 0
no_wrap_true = 0
has_title = 0
has_name = 0
has_text = 0

# Check for no 04/09 UmaTL overwrite (should not exist in this output)
uma04_09_count = 0

# Check no home/storyrace/lyrics
home_count = 0

for pfx in PREFIXES:
    pfx_dir = os.path.join(OUTPUT_BASE, pfx)
    if not os.path.isdir(pfx_dir):
        print(f"  {pfx}: DIR NOT FOUND")
        continue
    
    pfx_files = 0
    pfx_blocks = 0
    pfx_choices = 0
    
    for root, dirs, files in os.walk(pfx_dir):
        for fn in files:
            if fn.startswith("storytimeline_") and fn.endswith(".json"):
                pfx_files += 1
                fpath = os.path.join(root, fn)
                
                # Check CRLF
                with open(fpath, "rb") as f:
                    raw_bytes = f.read()
                
                if b"\r\n" in raw_bytes:
                    crlf_count += 1
                
                # Check valid JSON
                try:
                    text = raw_bytes.decode("utf-8")
                    data = json.loads(text)
                except (json.JSONDecodeError, UnicodeDecodeError):
                    invalid_json += 1
                    continue
                
                # Check no_wrap
                if data.get("no_wrap") == True:
                    no_wrap_true += 1
                
                # Check title
                if "title" in data:
                    has_title += 1
                
                # Count blocks and choices
                tbl = data.get("text_block_list", [])
                pfx_blocks += len(tbl)
                for blk in tbl:
                    if blk.get("name"):
                        has_name += 1
                    if blk.get("text"):
                        has_text += 1
                    cdl = blk.get("choice_data_list", [])
                    pfx_choices += len(cdl)
                    total_chars += len(blk.get("text", ""))
    
    print(f"  {pfx}: {pfx_files} files, {pfx_blocks} blocks, {pfx_choices} choices")
    total_files += pfx_files
    total_blocks += pfx_blocks
    total_choices += pfx_choices

print(f"\n=== VERIFICATION SUMMARY ===")
print(f"Total files: {total_files} (expected: 4280)")
print(f"Total blocks: {total_blocks}")
print(f"Total choices: {total_choices}")
print(f"Total text chars: {total_chars}")
print(f"CRLF files: {crlf_count} (expected: 0)")
print(f"Invalid JSON: {invalid_json} (expected: 0)")
print(f"no_wrap=true: {no_wrap_true}")
print(f"Has title: {has_title}")
print(f"Blocks with name: {has_name}")
print(f"Blocks with text: {has_text}")

# Spot check a few files
print(f"\n=== SPOT CHECK ===")
import random
random.seed(42)
for pfx in PREFIXES:
    pfx_dir = os.path.join(OUTPUT_BASE, pfx)
    if not os.path.isdir(pfx_dir):
        continue
    all_jsons = []
    for root, dirs, files in os.walk(pfx_dir):
        for fn in files:
            if fn.startswith("storytimeline_") and fn.endswith(".json"):
                all_jsons.append(os.path.join(root, fn))
    if all_jsons:
        sample = random.choice(all_jsons)
        with open(sample, "r", encoding="utf-8") as f:
            data = json.load(f)
        tbl = data.get("text_block_list", [])
        first_text = tbl[0].get("text", "")[:50] if tbl else "(empty)"
        print(f"  {pfx}: {os.path.basename(sample)} -> {len(tbl)} blocks, first: {first_text}")

# Check no home/lyrics/storyrace directories
all_dirs = set()
for root, dirs, files in os.walk(OUTPUT_BASE):
    for d in dirs:
        all_dirs.add(d)
print(f"\nAll subdirectories: {sorted(all_dirs)}")
