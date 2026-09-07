import os, re

base_dir = r"C:\Users\Ota\AppData\Local\pnpm\global\v11\3d68-1a057194ffe-925c3c4f3f829bae\node_modules\omniroute\dist"

# Find every single place in dist where reasoning_effort is assigned
for root, dirs, files in os.walk(base_dir):
    for f in files:
        if f.endswith('.js'):
            p = os.path.join(root, f)
            with open(p, 'r', encoding='utf-8', errors='ignore') as fp:
                txt = fp.read()
            
            # Find assignments to reasoning_effort
            matches = [m.start() for m in re.finditer(r'\.reasoning_effort\s*=', txt)]
            if matches:
                print(f"=== {os.path.relpath(p, base_dir)} ({len(matches)} matches) ===")
                for m in matches:
                    print(" ", repr(txt[max(0, m-80):min(len(txt), m+120)]))
