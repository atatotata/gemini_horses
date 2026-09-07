import os, re

base_dir = r"C:\Users\Ota\AppData\Local\pnpm\global\v11\3d68-1a057194ffe-925c3c4f3f829bae\node_modules\omniroute"

files_to_check = [
    r"dist\.build\next\server\chunks\_117kw-7._.js",
    r"dist\.build\next\server\chunks\_11yn8eg._.js",
    r"dist\.build\next\server\chunks\_1l6l9wn._.js",
    r"dist\.build\next\server\chunks\_1pmq-qh._.js",
]

for rel in files_to_check:
    full = os.path.join(base_dir, rel)
    if os.path.exists(full):
        with open(full, 'r', encoding='utf-8', errors='ignore') as f:
            text = f.read()
            matches = [m.start() for m in re.finditer(r'stripBooleanReasoning', text)]
            print(f"=== {rel} ({len(matches)} matches) ===")
            for m in matches:
                start = max(0, m - 100)
                end = min(len(text), m + 350)
                print(" ", repr(text[start:end]))
