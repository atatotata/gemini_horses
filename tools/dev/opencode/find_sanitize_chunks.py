import os, re

base_dir = r"C:\Users\Ota\AppData\Local\pnpm\global\v11\3d68-1a057194ffe-925c3c4f3f829bae\node_modules\omniroute\dist"

found = []
for root, dirs, files in os.walk(base_dir):
    for f in files:
        if f.endswith('.js'):
            p = os.path.join(root, f)
            with open(p, 'r', encoding='utf-8', errors='ignore') as fp:
                txt = fp.read()
            if 'mapped reasoning_effort minimal' in txt or 'sanitizeReasoningEffortForProvider' in txt:
                found.append(os.path.relpath(p, base_dir))

print("Found in dist chunks:", found)
