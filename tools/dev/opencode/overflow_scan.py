import json, glob, os, unicodedata

root = r"G:\Games\steamapps\common\UmamusumePrettyDerby_Jpn\gemini_horses\localized_data\assets\story\data"

def dispw(s):
    w = 0
    for ch in s:
        if unicodedata.combining(ch):
            continue
        w += 2 if unicodedata.east_asian_width(ch) in ('W', 'F') else 1
    return w

def scan(d):
    files = [f for f in glob.glob(os.path.join(root, d, '*', '*.json')) if 'storytimeline' in os.path.basename(f)]
    n_lines = 0
    over60 = 0
    over63 = 0
    over70 = 0
    maxw = 0
    blocks_no_newline = 0   # text blocks with no \n at all
    n_blocks = 0
    for f in files:
        data = json.load(open(f, encoding='utf-8'))
        for blk in data.get('text_block_list', []):
            t = blk.get('text')
            if not t:
                continue
            n_blocks += 1
            if '\n' not in t:
                blocks_no_newline += 1
            for line in t.split('\n'):
                w = dispw(line)
                if w == 0:
                    continue
                n_lines += 1
                maxw = max(maxw, w)
                if w > 60: over60 += 1
                if w > 63: over63 += 1
                if w > 70: over70 += 1
    print(f"data/{d}: files={len(files)} blocks={n_blocks} lines={n_lines}")
    print(f"   lines>60 cols: {over60} ({100.0*over60/max(1,n_lines):.1f}%)  >63: {over63} ({100.0*over63/max(1,n_lines):.1f}%)  >70: {over70} ({100.0*over70/max(1,n_lines):.1f}%)  max={maxw}")
    print(f"   text blocks with NO manual newline: {blocks_no_newline} ({100.0*blocks_no_newline/max(1,n_blocks):.1f}%)")

for d in ('04', '09'):
    scan(d)
