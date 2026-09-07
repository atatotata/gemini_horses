import json, glob, os, unicodedata, statistics, random

root = r"G:\Games\steamapps\common\UmamusumePrettyDerby_Jpn\gemini_horses\localized_data\assets\story\data"

def dispw(s):
    w = 0
    for ch in s:
        if unicodedata.combining(ch):
            continue
        w += 2 if unicodedata.east_asian_width(ch) in ('W', 'F') else 1
    return w

def analyze(d):
    files = glob.glob(os.path.join(root, d, '*', '*.json'))
    files = [f for f in files if 'storytimeline' in os.path.basename(f)]
    random.seed(7)
    sample = random.sample(files, min(8, len(files)))
    maxw = 0
    worst = None
    linews = []
    for f in sample:
        data = json.load(open(f, encoding='utf-8'))
        for blk in data.get('text_block_list', []):
            t = blk.get('text') or ''
            for line in t.split('\n'):
                w = dispw(line)
                if w > 0:
                    linews.append((w, os.path.basename(f)))
                    if w > maxw:
                        maxw = w
                        worst = (f, line)
    if linews:
        ws = sorted(x[0] for x in linews)
        print(f"== data/{d}: files {len(sample)}/{len(files)} | lines n={len(ws)} max={max(ws)} median={statistics.median(ws):.0f} p90={ws[int(len(ws)*0.9)]:.0f}")
        print("   worst:", worst[1][:100])
    else:
        print(f"== data/{d}: no lines")

for d in ('00', '04', '09', '83'):
    analyze(d)

print("\n== no_wrap:false trio (data/04/1042) max block display width ==")
for f in sorted(glob.glob(os.path.join(root, '04', '1042', '*.json'))):
    data = json.load(open(f, encoding='utf-8'))
    for bi, blk in enumerate(data.get('text_block_list', [])):
        t = blk.get('text') or ''
        w = dispw(t)
        if w > 60:
            print(f"  {os.path.basename(f)} block {bi}: width {w} :: {t[:80]}")
