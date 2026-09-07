#!/usr/bin/env python3
"""Verify extracted JSON files."""
import json
from pathlib import Path

base = Path(r'C:\TMP\extra_fetch\story_json')
files = list(base.rglob('*.json'))
total_blocks = 0
total_choices = 0
for f in sorted(files):
    with open(f, 'r', encoding='utf-8') as fh:
        data = json.load(fh)
    bl = data.get('text_block_list', [])
    nb = len(bl)
    nc = sum(len(b.get('choice_data_list', [])) for b in bl)
    total_blocks += nb
    total_choices += nc
    print(f"  {f.relative_to(base)}: {nb} blocks, {nc} choices")

print(f"\nTotal files: {len(files)}")
print(f"Total blocks: {total_blocks}")
print(f"Total choices: {total_choices}")
