import os, re

base_dir = r"C:\Users\Ota\AppData\Local\pnpm\global\v11\3d68-1a057194ffe-925c3c4f3f829bae\node_modules\omniroute"

# 1. Patch chatCore.ts
chatcore_ts = os.path.join(base_dir, r"open-sse\handlers\chatCore.ts")
if os.path.exists(chatcore_ts):
    with open(chatcore_ts, 'r', encoding='utf-8') as f:
        src = f.read()
    
    old_target = "stripStore(translatedBody, provider, targetFormat);"
    new_target = """stripStore(translatedBody, provider, targetFormat);
  if (isOpencodeGoProvider(provider) || provider === "opencode-go" || String(translatedBody.model || "").startsWith("muse-spark")) {
    delete (translatedBody as Record<string, unknown>).reasoning_effort;
    delete (translatedBody as Record<string, unknown>).reasoning;
  }"""
    if old_target in src and "startsWith(\"muse-spark\")" not in src:
        src = src.replace(old_target, new_target, 1)
        with open(chatcore_ts, 'w', encoding='utf-8') as f:
            f.write(src)
        print("Patched open-sse/handlers/chatCore.ts")

# 2. Patch all dist chunks
dist_dir = os.path.join(base_dir, "dist")
for root, dirs, files in os.walk(dist_dir):
    for file in files:
        if file.endswith('.js'):
            p = os.path.join(root, file)
            with open(p, 'r', encoding='utf-8', errors='ignore') as f:
                content = f.read()
            
            modified = False
            
            # Chunk pattern in _117kw-7._.js / _1pmq-qh._.js
            # (0,K.stripStore)(iw,rG,nx)
            if '(0,K.stripStore)(iw,rG,nx)' in content and 'delete iw.reasoning_effort' not in content:
                content = content.replace(
                    '(0,K.stripStore)(iw,rG,nx)',
                    '(0,K.stripStore)(iw,rG,nx),("opencode-go"===rG||(0,eb.isOpencodeGoProvider)(rG)||String(iw.model||"").startsWith("muse-spark"))&&(delete iw.reasoning_effort,delete iw.reasoning)'
                )
                modified = True
                
            # Chunk pattern in _11yn8eg._.js / _1l6l9wn._.js
            # (0,e$.stripStore)(ov,rz,nk) or similar
            # Let's search with regex for stripStore call: \(0,\w+\.stripStore\)\((\w+),(\w+),(\w+)\)
            matches = list(re.finditer(r'\(0,(\w+)\.stripStore\)\((\w+),(\w+),(\w+)\)', content))
            for m in matches:
                full_m = m.group(0)
                body_var = m.group(2)
                prov_var = m.group(3)
                inj = f'{full_m},("opencode-go"==={prov_var}||String({body_var}.model||"").startsWith("muse-spark"))&&(delete {body_var}.reasoning_effort,delete {body_var}.reasoning)'
                if inj not in content:
                    content = content.replace(full_m, inj, 1)
                    modified = True

            if modified:
                with open(p, 'w', encoding='utf-8') as f:
                    f.write(content)
                print(f"Patched chunk {os.path.relpath(p, base_dir)}")

