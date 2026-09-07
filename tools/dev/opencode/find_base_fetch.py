import os, re

base_dir = r"C:\Users\Ota\AppData\Local\pnpm\global\v11\3d68-1a057194ffe-925c3c4f3f829bae\node_modules\omniroute"
target = os.path.join(base_dir, r"open-sse\executors\base.ts")

with open(target, 'r', encoding='utf-8', errors='ignore') as f:
    text = f.read()

lines = text.splitlines()
for i, l in enumerate(lines):
    if 'JSON.stringify(body' in l or 'JSON.stringify(finalBody' in l or 'fetch(' in l:
        print(f"Line {i+1}: {l.strip()}")
        for j in range(max(0, i-5), min(len(lines), i+15)):
            print(f"  {j+1}: {lines[j].strip().encode('ascii', errors='replace').decode('ascii')}")
