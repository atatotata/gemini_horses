import os

base_dir = r"C:\Users\Ota\AppData\Local\pnpm\global\v11\3d68-1a057194ffe-925c3c4f3f829bae\node_modules\omniroute"
target = os.path.join(base_dir, r"dist\.build\next\server\chunks\_08_y1bx._.js")

with open(target, 'r', encoding='utf-8', errors='ignore') as f:
    text = f.read()

idx = text.find('"muse-spark-1.2-contributor":')
if idx != -1:
    print("Code around EFFORT_TIERS:")
    print(repr(text[idx-200:idx+800]))
