import os

base_dir = r"C:\Users\Ota\AppData\Local\pnpm\global\v11\3d68-1a057194ffe-925c3c4f3f829bae\node_modules\omniroute"
target = os.path.join(base_dir, r"open-sse\executors\base.ts")

with open(target, 'r', encoding='utf-8') as f:
    lines = f.readlines()

for i, l in enumerate(lines):
    if 'appliedEffort' in l or 'applyReasoningEffort' in l or 'applyEffort' in l or 'effort' in l.lower():
        if any(w in l for w in ['appliedEffort', 'reasoning_effort', 'applyReasoningEffort', 'transformedBody']):
            print(f"L{i+1}: {l.strip().encode('ascii', errors='replace').decode('ascii')[:100]}")
