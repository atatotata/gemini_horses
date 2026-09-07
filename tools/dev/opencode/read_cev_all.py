import os

base_dir = r"C:\Users\Ota\AppData\Local\pnpm\global\v11\3d68-1a057194ffe-925c3c4f3f829bae\node_modules\omniroute"
target = os.path.join(base_dir, r"open-sse\handlers\chatCore\claudeEffortVariant.ts")

with open(target, 'r', encoding='utf-8') as f:
    text = f.read()

for l in text.splitlines():
    print("CV:", l.encode('ascii', errors='replace').decode('ascii'))
