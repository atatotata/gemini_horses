import os

base_dir = r"C:\Users\Ota\AppData\Local\pnpm\global\v11\3d68-1a057194ffe-925c3c4f3f829bae\node_modules\omniroute"

for root, dirs, files in os.walk(base_dir):
    for file in files:
        if 'opencode' in file.lower() or 'go' in file.lower():
            if file.endswith(('.ts', '.js')):
                print(os.path.relpath(os.path.join(root, file), base_dir))
