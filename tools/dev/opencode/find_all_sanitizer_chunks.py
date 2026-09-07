import os, re

base_dir = r"C:\Users\Ota\AppData\Local\pnpm\global\v11\3d68-1a057194ffe-925c3c4f3f829bae\node_modules\omniroute"

for root, dirs, files in os.walk(base_dir):
    for file in files:
        if file.endswith(('.js', '.ts', '.mjs', '.cjs')):
            path = os.path.join(root, file)
            try:
                with open(path, 'r', encoding='utf-8', errors='ignore') as f:
                    content = f.read()
                    if 'isOpencodeGoProvider' in content or 'stripBooleanReasoning' in content:
                        print(f"Match in {os.path.relpath(path, base_dir)}")
            except: pass
