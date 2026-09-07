import os, re

base_dir = r"C:\Users\Ota\AppData\Local\pnpm\global\v11\3d68-1a057194ffe-925c3c4f3f829bae\node_modules\omniroute"

for root, dirs, files in os.walk(base_dir):
    for f in files:
        if f.endswith(('.ts', '.js')):
            p = os.path.join(root, f)
            with open(p, 'r', encoding='utf-8', errors='ignore') as fp:
                txt = fp.read()
            if 'executor' in txt and 'opencode-go' in txt:
                print(f"Found in {os.path.relpath(p, base_dir)}")
