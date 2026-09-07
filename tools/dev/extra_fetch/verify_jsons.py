#!/usr/bin/env python3
"""Quick validation."""
import json, os, pathlib

base = r'C:\TMP\extra_fetch\story_json'
for sid in [90009001, 90025004, 90048001, 90056008]:
    s = str(sid).zfill(9)
    p = os.path.join(base, '09', s[2:6], f'storytimeline_{s}.json')
    if os.path.exists(p):
        with open(p, 'r', encoding='utf-8') as f:
            d = json.load(f)
        bl = d.get('text_block_list', [])
        nc = sum(len(b.get('choice_data_list', [])) for b in bl)
        title = d.get('title', '')
        print(f'SID {sid}: {len(bl)} blocks, {nc} choices, title="{title[:30]}"')
    else:
        print(f'SID {sid}: MISSING!')

p04 = os.path.join(base, '04')
print(f'04 dir exists: {os.path.exists(p04)}')
for prefix in ['10', '14']:
    d = os.path.join(base, prefix)
    if os.path.exists(d):
        cnt = sum(1 for _ in pathlib.Path(d).rglob('storytimeline_*.json'))
        print(f'{prefix} files: {cnt}')
