import os, re

base_dir = r"C:\Users\Ota\AppData\Local\pnpm\global\v11\3d68-1a057194ffe-925c3c4f3f829bae\node_modules\omniroute"

# 1. Patch open-sse\executors\opencode.ts
target_ts = os.path.join(base_dir, r"open-sse\executors\opencode.ts")
if os.path.exists(target_ts):
    with open(target_ts, 'r', encoding='utf-8') as f:
        src = f.read()
    
    # In opencode.ts, ensure reasoning_effort is never set for opencode-go or muse-spark
    old_block = """    if (modifiedBody && typeof modifiedBody === "object" && !Array.isArray(modifiedBody)) {
      const mb = modifiedBody as Record<string, unknown>;
      const parsed = parseEffortLevel(model);
      if (parsed) {
        mb.model = parsed.baseModel;
        if (mb.reasoning_effort === undefined) {
          mb.reasoning_effort = parsed.effort;
        }
      }
    }"""
    
    new_block = """    if (modifiedBody && typeof modifiedBody === "object" && !Array.isArray(modifiedBody)) {
      const mb = modifiedBody as Record<string, unknown>;
      const parsed = parseEffortLevel(model);
      if (parsed) {
        mb.model = parsed.baseModel;
        if (this.provider !== "opencode-go" && !parsed.baseModel.startsWith("muse-spark") && mb.reasoning_effort === undefined) {
          mb.reasoning_effort = parsed.effort;
        }
      }
      if (this.provider === "opencode-go" || String(mb.model || "").startsWith("muse-spark")) {
        delete mb.reasoning_effort;
      }
    }"""
    
    if old_block in src:
        src = src.replace(old_block, new_block)
        with open(target_ts, 'w', encoding='utf-8') as f:
            f.write(src)
        print("Patched open-sse/executors/opencode.ts")
    else:
        print("open-sse/executors/opencode.ts pattern not found or already patched")

# 2. Patch all chunks in dist/
chunks = [
    r"dist\.build\next\server\chunks\_08_y1bx._.js",
    r"dist\.build\next\server\chunks\_0o8_5h8._.js",
    r"dist\.build\next\server\chunks\_0t1t5fj._.js",
    r"dist\.build\next\server\chunks\_18ct13i._.js",
    r"dist\.build\next\server\chunks\_1j_edf1._.js",
    r"dist\.build\next\server\chunks\_1luyz1c._.js"
]

pattern = r'n&&\s*\(t\.model=n\.baseModel,\s*void 0===t\.reasoning_effort&&\s*\(t\.reasoning_effort=n\.effort\)\)'
replacement = r'n&&(t.model=n.baseModel,"opencode-go"!==this.provider&&!n.baseModel.startsWith("muse-spark")&&void 0===t.reasoning_effort&&(t.reasoning_effort=n.effort)),("opencode-go"===this.provider||String(t.model||"").startsWith("muse-spark"))&&delete t.reasoning_effort'

for rel in chunks:
    p = os.path.join(base_dir, rel)
    if os.path.exists(p):
        with open(p, 'r', encoding='utf-8', errors='ignore') as f:
            code = f.read()
        
        new_code, count = re.subn(pattern, replacement, code)
        if count > 0:
            with open(p, 'w', encoding='utf-8') as f:
                f.write(new_code)
            print(f"Patched {rel} ({count} replacements)")
        else:
            print(f"No match in {rel}")

