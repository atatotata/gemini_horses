import os

base_dir = r"C:\Users\Ota\AppData\Local\pnpm\global\v11\3d68-1a057194ffe-925c3c4f3f829bae\node_modules\omniroute"
target = os.path.join(base_dir, r"open-sse\handlers\chatCore.ts")
if os.path.exists(target):
    with open(target, 'r', encoding='utf-8') as f:
        lines = f.readlines()
        for i, l in enumerate(lines):
            if 'finalModelToUpstream' in l or 'reasoning_effort' in l or 'resolveSyncedModelIdAndEffort' in l:
                print(f"Line {i+1}: {l.strip()}")
                start = max(0, i - 10)
                end = min(len(lines), i + 20)
                for j in range(start, end):
                    print(f"  {j+1}: {lines[j].rstrip()}")
                print("="*40)
