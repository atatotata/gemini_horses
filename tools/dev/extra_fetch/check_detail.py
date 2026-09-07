import json, io, sys
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
from pathlib import Path

G = Path('G:/Games/steamapps/common/UmamusumePrettyDerby_Jpn/gemini_horses/localized_data/assets/story/data')

# Check 90054007
d = json.loads((G/'09'/'0054'/'storytimeline_90054007.json').read_text('utf-8'))
print('90054007 blocks:', len(d['text_block_list']))
for i,b in enumerate(d['text_block_list'][:3]):
    nm = b.get('name','')
    tx = b.get('text','')[:80]
    print(f'  [{i}] name={nm!r} text={tx!r}')

# Check all files for choices
print()
for root, dirs, files in G.walk():
    for fn in sorted(files):
        if not fn.startswith('storytimeline_'): continue
        fp = Path(root)/fn
        rel = fp.relative_to(G)
        parts = str(rel).split('/')
        if len(parts) < 2: continue
        pfx, sub = parts[0], parts[1]
        # Only our 26
        sid = fn.replace('storytimeline_','').replace('.json','')
        if sid not in {'90016001','90021001','90032001','90054007',
            '100006001','100006002','100006003',
            '100007001','100007002','100007003',
            '100008001','100008002','100008003',
            '100009001','100009002','100009003','100009004',
            '100010001','100010002','100010003',
            '100011001','100011002','100011003',
            '140001001','140001002','140001003'}:
            continue
        data = json.loads(fp.read_text('utf-8'))
        for i, blk in enumerate(data.get('text_block_list', [])):
            cdl = blk.get('choice_data_list', [])
            if cdl and any(c for c in cdl):
                print(f'CHOICE {pfx}/{sub}/{fn} block {i}:')
                for ci, c in enumerate(cdl):
                    print(f'  choice[{ci}]: {c}')
