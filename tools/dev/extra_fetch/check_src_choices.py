import json, os, io, sys
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
root = 'C:/TMP/extra_fetch/story_json'
targets = {'90016001','90021001','90032001','90054007',
    '100006001','100006002','100006003',
    '100007001','100007002','100007003',
    '100008001','100008002','100008003',
    '100009001','100009002','100009003','100009004',
    '100010001','100010002','100010003',
    '100011001','100011002','100011003',
    '140001001','140001002','140001003'}
total = 0
for r, d, files in os.walk(root):
    for f in files:
        if not f.startswith('storytimeline_') or not f.endswith('.json'):
            continue
        sid = f.replace('storytimeline_', '').replace('.json', '')
        if sid not in targets:
            continue
        d2 = json.load(open(os.path.join(r, f), 'r', encoding='utf-8'))
        for i, b in enumerate(d2.get('text_block_list', [])):
            cdl = b.get('choice_data_list', [])
            nc = len([c for c in cdl if c])
            if nc > 0:
                total += nc
                print(f'{f} block {i}: {nc} choices')
                for ci, c in enumerate(cdl):
                    if c:
                        print(f'  [{ci}]: {c}')
print(f'Total non-empty choices: {total}')
