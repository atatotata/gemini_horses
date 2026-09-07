import os

base_dir = r"C:\Users\Ota\AppData\Local\pnpm\global\v11\3d68-1a057194ffe-925c3c4f3f829bae\node_modules\omniroute"
target = os.path.join(base_dir, r"dist\.build\next\server\chunks\_08_y1bx._.js")

with open(target, 'r', encoding='utf-8', errors='ignore') as f:
    text = f.read()

idx = text.find('"muse-spark-1.2-contributor":')
if idx != -1:
    # Find the variable name holding EFFORT_TIERS
    var_start = text.rfind('let ', 0, idx)
    if var_start == -1: var_start = text.rfind('var ', 0, idx)
    if var_start == -1: var_start = text.rfind('const ', 0, idx)
    print("Declaration:", repr(text[var_start:idx+50]))
    # Now find where this variable is used in the file
    var_name = text[var_start:idx].split()[-1].split('=')[0].strip()
    print("Variable name:", var_name)
    pos = 0
    while True:
        idx_use = text.find(var_name, pos)
        if idx_use == -1: break
        print("Used at:", idx_use, repr(text[idx_use-20:idx_use+100]))
        pos = idx_use + len(var_name) + 1
