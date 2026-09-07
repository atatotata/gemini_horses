import os

base_dir = r"C:\Users\Ota\AppData\Local\pnpm\global\v11\3d68-1a057194ffe-925c3c4f3f829bae\node_modules\omniroute"
target = os.path.join(base_dir, r"open-sse\executors\opencode.ts")

with open(target, 'r', encoding='utf-8', errors='ignore') as f:
    text = f.read()

lines = text.splitlines()
for i, l in enumerate(lines):
    if 'execute(' in l or 'buildRequestBody' in l or 'buildPayload' in l or 'preparePayload' in l:
        print(f"Line {i+1}: {l.strip()}")
        for j in range(i, min(i+40, len(lines))):
            print(f"  {j+1}: {lines[j].strip().encode('ascii', errors='replace').decode('ascii')}")
