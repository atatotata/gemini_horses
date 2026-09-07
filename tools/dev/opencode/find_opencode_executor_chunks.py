import os, re

base_dir = r"C:\Users\Ota\AppData\Local\pnpm\global\v11\3d68-1a057194ffe-925c3c4f3f829bae\node_modules\omniroute"

found = []
for root, dirs, files in os.walk(os.path.join(base_dir, "dist")):
    for f in files:
        if f.endswith('.js'):
            p = os.path.join(root, f)
            with open(p, 'r', encoding='utf-8', errors='ignore') as fp:
                txt = fp.read()
            if 'parseEffortLevel' in txt or 'muse-spark-1.2-contributor":[' in txt or 'muse-spark-1.2-contributor": ["' in txt:
                found.append(os.path.relpath(p, base_dir))

print("Found chunks with parseEffortLevel / EFFORT_TIERS:", found)
