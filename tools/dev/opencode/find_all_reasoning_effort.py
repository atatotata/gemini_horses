import os, re

base_dir = r"C:\Users\Ota\AppData\Local\pnpm\global\v11\3d68-1a057194ffe-925c3c4f3f829bae\node_modules\omniroute"

for root, dirs, files in os.walk(base_dir):
    for file in files:
        if file.endswith(('.js', '.ts', '.mjs', '.cjs')):
            path = os.path.join(root, file)
            try:
                with open(path, 'r', encoding='utf-8', errors='ignore') as f:
                    content = f.read()
                    if 'reasoning_effort' in content:
                        print(f"\n=== {os.path.relpath(path, base_dir)} ===")
                        matches = [m.start() for m in re.finditer(r'reasoning_effort', content)]
                        for m in matches:
                            start = max(0, m - 150)
                            end = min(len(content), m + 250)
                            print("  Snippet:", content[start:end].replace('\n', ' '))
            except: pass
