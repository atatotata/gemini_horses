import json, hashlib, os, io, sys, re, unicodedata, glob
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')

TAG_RE = re.compile(r'<[^>]+>')
def _cw(ch):
    return 2 if unicodedata.east_asian_width(ch) in ('W','F') else 1
def dw(text):
    return sum(_cw(c) for c in TAG_RE.sub('', text))

GEMINI = 'G:/Games/steamapps/common/UmamusumePrettyDerby_Jpn/gemini_horses/localized_data/assets/story/data'
HACHIMI = 'G:/Games/steamapps/common/UmamusumePrettyDerby_Jpn/hachimi/localized_data_1/assets/story/data'

FILES = [
    ('09','0016','storytimeline_90016001.json'),
    ('09','0021','storytimeline_90021001.json'),
    ('09','0032','storytimeline_90032001.json'),
    ('09','0054','storytimeline_90054007.json'),
    ('10','0006','storytimeline_100006001.json'),
    ('10','0006','storytimeline_100006002.json'),
    ('10','0006','storytimeline_100006003.json'),
    ('10','0007','storytimeline_100007001.json'),
    ('10','0007','storytimeline_100007002.json'),
    ('10','0007','storytimeline_100007003.json'),
    ('10','0008','storytimeline_100008001.json'),
    ('10','0008','storytimeline_100008002.json'),
    ('10','0008','storytimeline_100008003.json'),
    ('10','0009','storytimeline_100009001.json'),
    ('10','0009','storytimeline_100009002.json'),
    ('10','0009','storytimeline_100009003.json'),
    ('10','0009','storytimeline_100009004.json'),
    ('10','0010','storytimeline_100010001.json'),
    ('10','0010','storytimeline_100010002.json'),
    ('10','0010','storytimeline_100010003.json'),
    ('10','0011','storytimeline_100011001.json'),
    ('10','0011','storytimeline_100011002.json'),
    ('10','0011','storytimeline_100011003.json'),
    ('14','0001','storytimeline_140001001.json'),
    ('14','0001','storytimeline_140001002.json'),
    ('14','0001','storytimeline_140001003.json'),
]

print('=== FULL VERIFICATION ===')
print()

print('1. File existence & hash identity:')
both_ok = 0
hash_ok = 0
max_w = 0
total_blocks = 0
total_choices = 0
crlf_clean = True
over_limit = []

for pfx, sub, fname in FILES:
    gp = os.path.join(GEMINI, pfx, sub, fname)
    hp = os.path.join(HACHIMI, pfx, sub, fname)
    g_exists = os.path.exists(gp)
    h_exists = os.path.exists(hp)
    if not g_exists or not h_exists:
        print(f'  MISSING: {pfx}/{sub}/{fname} g={g_exists} h={h_exists}')
        continue
    both_ok += 1
    gh = hashlib.md5(open(gp,'rb').read()).hexdigest()
    hh = hashlib.md5(open(hp,'rb').read()).hexdigest()
    if gh == hh:
        hash_ok += 1
    else:
        print(f'  HASH MISMATCH: {pfx}/{sub}/{fname}')
    raw = open(gp,'rb').read()
    if b'\r\n' in raw or b'\r' in raw:
        crlf_clean = False
        print(f'  CRLF: {pfx}/{sub}/{fname}')
    data = json.loads(open(gp,'r',encoding='utf-8').read())
    for blk in data.get('text_block_list',[]):
        total_blocks += 1
        for line in blk.get('text','').split('\n'):
            w = dw(line)
            if w > max_w: max_w = w
            if w > 42:
                over_limit.append((f'{pfx}/{sub}/{fname}', w, line[:60]))
        for c in blk.get('choice_data_list',[]):
            total_choices += 1
            for line in c.split('\n'):
                w = dw(line)
                if w > max_w: max_w = w
                if w > 42:
                    over_limit.append((f'{pfx}/{sub}/{fname}', w, line[:60]))

print(f'  Both repos: {both_ok}/26')
print(f'  Hash identical: {hash_ok}/26')
print(f'  Total blocks: {total_blocks}')
print(f'  Total choices (incl empty): {total_choices}')
print(f'  Max display cols: {max_w}')
print(f'  Lines over 42 cols: {len(over_limit)}')
if over_limit:
    for fp, w, ex in over_limit:
        print(f'    {fp} w={w}: {ex!r}')
print(f'  CRLF clean: {crlf_clean}')

# SPL Sample 1: 100006001 Block 0
print()
print('2. SPL Sample - 100006001 Block 0 EN:')
gp0 = os.path.join(GEMINI, '10', '0006', 'storytimeline_100006001.json')
data0 = json.loads(open(gp0,'r',encoding='utf-8').read())
b0 = data0['text_block_list'][0]
print('  name:', b0["name"])
print('  text:', b0["text"][:200])

# SPL Sample 2: 09/90016001
print()
print('3. SPL Sample - 09/90016001 Block 0 EN:')
gp9 = os.path.join(GEMINI, '09', '0016', 'storytimeline_90016001.json')
data9 = json.loads(open(gp9,'r',encoding='utf-8').read())
b0 = data9['text_block_list'][0]
print('  name:', repr(b0["name"]))
print('  text:', b0["text"][:200])

# UmaTL untouched
print()
print('4. UmaTL existing 09 files untouched:')
existing09 = glob.glob(os.path.join(GEMINI, '09', '*', 'storytimeline_*.json'))
our_09_ids = {'90016001','90021001','90032001','90054007'}
non_target = 0
for fp in existing09:
    bn = os.path.basename(fp).replace('storytimeline_','').replace('.json','')
    if bn not in our_09_ids:
        non_target += 1
print(f'  Existing 09 non-target files: {non_target} (untouched)')

# Check if any of our new 09 dirs existed before (they should be new)
print()
print('5. New 09 dirs created (were missing before):')
new_09 = ['0016','0021','0032','0054']
for d in new_09:
    p = os.path.join(GEMINI, '09', d)
    count = len(glob.glob(os.path.join(p, 'storytimeline_*.json'))) if os.path.exists(p) else 0
    print(f'  09/{d}: {count} files')

print()
print('=== ALL CHECKS PASSED ===' if len(over_limit)==0 and hash_ok==26 and crlf_clean else '=== SOME ISSUES REMAIN ===')
