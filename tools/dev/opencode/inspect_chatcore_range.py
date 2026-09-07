import os

base_dir = r"C:\Users\Ota\AppData\Local\pnpm\global\v11\3d68-1a057194ffe-925c3c4f3f829bae\node_modules\omniroute"
target = os.path.join(base_dir, r"open-sse\handlers\chatCore.ts")

with open(target, 'r', encoding='utf-8', errors='ignore') as f:
    lines = f.readlines()

for i in range(2620, min(2800, len(lines))):
    l = lines[i].rstrip()
    for word in ['reasoning', 'effort', 'executor', 'send', 'upstream', 'translate']:
        if word in l.lower():
            print(f"{i+1}: {l.encode('ascii', errors='replace').decode('ascii')}")
            break
