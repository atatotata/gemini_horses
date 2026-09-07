import os

base_dir = r"C:\Users\Ota\AppData\Local\pnpm\global\v11\3d68-1a057194ffe-925c3c4f3f829bae\node_modules\omniroute"
target = os.path.join(base_dir, r"dist\.build\next\server\chunks\_08_y1bx._.js")

with open(target, 'r', encoding='utf-8', errors='ignore') as f:
    text = f.read()

idx = text.find('Object.entries(m)')
if idx != -1:
    print("Found Object.entries(m):", repr(text[idx-100:idx+400]))
else:
    # search for parseEffortLevel logic
    idx2 = text.find('${level}')
    if idx2 == -1: idx2 = text.find('`${')
    print("Search around EFFORT_TIERS:")
    idx3 = text.find('"muse-spark-1.2-contributor":')
    print(repr(text[idx3:idx3+1500]))
