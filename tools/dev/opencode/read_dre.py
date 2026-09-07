import os

base_dir = r"C:\Users\Ota\AppData\Local\pnpm\global\v11\3d68-1a057194ffe-925c3c4f3f829bae\node_modules\omniroute"
for rel in [r"open-sse\services\defaultReasoningEffort.ts", r"open-sse\services\model.ts"]:
    p = os.path.join(base_dir, rel)
    if os.path.exists(p):
        with open(p, 'r', encoding='utf-8', errors='ignore') as f:
            print(f"=== {rel} ===")
            print(f.read().encode('ascii', errors='replace').decode('ascii'))
