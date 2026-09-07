import os, re

base_dir = r"C:\Users\Ota\AppData\Local\pnpm\global\v11\3d68-1a057194ffe-925c3c4f3f829bae\node_modules\omniroute"

for root, dirs, files in os.walk(base_dir):
    for file in files:
        if file.endswith(('.js', '.ts', '.mjs', '.cjs')):
            path = os.path.join(root, file)
            try:
                with open(path, 'r', encoding='utf-8', errors='ignore') as f:
                    content = f.read()
                    if 'model_capability_overrides' in content:
                        print(f"Found in {os.path.relpath(path, base_dir)}")
                        matches = [m.start() for m in re.finditer(r'model_capability_overrides', content)]
                        for m in matches[:5]:
                            start = max(0, m - 100)
                            end = min(len(content), m + 300)
                            print("  Snippet:", content[start:end].replace('\n', ' '))
            except: pass
