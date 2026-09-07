import os, re

base_dir = r"C:\Users\Ota\AppData\Local\pnpm\global\v11\3d68-1a057194ffe-925c3c4f3f829bae\node_modules\omniroute"

for rel in [r"dist\.build\next\server\chunks\_117kw-7._.js", r"dist\.build\next\server\chunks\_1pmq-qh._.js"]:
    p = os.path.join(base_dir, rel)
    with open(p, 'r', encoding='utf-8', errors='ignore') as f:
        t = f.read()
    idx = t.find('stripBooleanReasoning')
    print(f"=== {rel} ===")
    if idx != -1:
        print(repr(t[max(0, idx-500):idx+500]))
