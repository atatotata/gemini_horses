import os

base_dir = r"C:\Users\Ota\AppData\Local\pnpm\global\v11\3d68-1a057194ffe-925c3c4f3f829bae\node_modules\omniroute"
target = os.path.join(base_dir, r"open-sse\handlers\chatCore.ts")
if os.path.exists(target):
    with open(target, 'r', encoding='utf-8', errors='ignore') as f:
        lines = f.readlines()
        for j in range(2670, min(2740, len(lines))):
            print(f"  {j+1}: {lines[j].rstrip()}".encode('ascii', errors='replace').decode('ascii'))
