import os, re

base_dir = r"C:\Users\Ota\AppData\Local\pnpm\global\v11\3d68-1a057194ffe-925c3c4f3f829bae\node_modules\omniroute"
target = os.path.join(base_dir, r"dist\.build\next\server\chunks\_08_y1bx._.js")

with open(target, 'r', encoding='utf-8', errors='ignore') as f:
    text = f.read()

idx = text.find('muse-spark-1.2-contributor')
if idx != -1:
    print("EFFORT_TIERS snippet:", repr(text[idx-50:idx+250]))

idx2 = text.find('reasoning_effort===void 0')
if idx2 != -1:
    print("buildRequestBody snippet:", repr(text[idx2-100:idx2+200]))
else:
    # search for reasoning_effort
    for m in re.finditer(r'reasoning_effort', text):
        st = m.start()
        print("Match:", repr(text[max(0, st-100):min(len(text), st+150)]))
