import os

base_dir = r"C:\Users\Ota\AppData\Local\pnpm\global\v11\3d68-1a057194ffe-925c3c4f3f829bae\node_modules\omniroute\dist"
target = os.path.join(base_dir, r".build\next\server\chunks\_117kw-7._.js")

with open(target, 'r', encoding='utf-8', errors='ignore') as f:
    text = f.read()

idx = text.find('stripStore')
print(repr(text[idx-100:idx+400]))
