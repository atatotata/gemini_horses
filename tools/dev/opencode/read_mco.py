import os

base_dir = r"C:\Users\Ota\AppData\Local\pnpm\global\v11\3d68-1a057194ffe-925c3c4f3f829bae\node_modules\omniroute"
target = os.path.join(base_dir, r"src\lib\db\modelCapabilityOverrides.ts")
if os.path.exists(target):
    with open(target, 'r', encoding='utf-8') as f:
        print(f.read())
else:
    print("File not found")
