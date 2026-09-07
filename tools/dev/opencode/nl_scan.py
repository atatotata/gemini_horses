import json, glob, os

root = r"G:\Games\steamapps\common\UmamusumePrettyDerby_Jpn\gemini_horses\localized_data\assets\story\data"

def scan(d):
    files = [f for f in glob.glob(os.path.join(root, d, '*', '*.json')) if 'storytimeline' in os.path.basename(f)]
    blocks = 0
    has_nl = 0
    space_before_nl = 0
    for f in files:
        data = json.load(open(f, encoding='utf-8'))
        for blk in data.get('text_block_list', []):
            t = blk.get('text')
            if not t:
                continue
            blocks += 1
            if '\n' in t:
                has_nl += 1
                # every newline preceded by space?
                parts = t.split('\n')
                if all(p == '' or p.endswith(' ') for p in parts[:-1]):
                    space_before_nl += 1
    print(f"data/{d}: blocks={blocks} with \\n={has_nl} all-newlines-space-prefixed={space_before_nl}")

scan('04')
scan('09')
