import os, re

base_dir = r"C:\Users\Ota\AppData\Local\pnpm\global\v11\3d68-1a057194ffe-925c3c4f3f829bae\node_modules\omniroute"

# 1. Patch open-sse\services\opencodeReasoningSanitizer.ts
sanitizer_ts = os.path.join(base_dir, r"open-sse\services\opencodeReasoningSanitizer.ts")
if os.path.exists(sanitizer_ts):
    with open(sanitizer_ts, 'r', encoding='utf-8') as f:
        src = f.read()
    
    new_src = src.replace(
        """export function stripBooleanReasoning(body: JsonRecord): JsonRecord {
  if (!body || typeof body !== "object") return body;
  if (!("reasoning" in body)) return body;
  const reasoning = body.reasoning;
  // Only strip when reasoning is a boolean ? object/string forms are valid
  // for the Go struct and should be forwarded as-is.
  if (typeof reasoning !== "boolean") return body;
  const next = { ...body };
  delete next.reasoning;
  return next;
}""",
        """export function stripBooleanReasoning(body: JsonRecord): JsonRecord {
  if (!body || typeof body !== "object") return body;
  const next = { ...body };
  if ("reasoning" in next && typeof next.reasoning === "boolean") {
    delete next.reasoning;
  }
  if ("reasoning_effort" in next) {
    delete next.reasoning_effort;
  }
  return next;
}"""
    )
    if new_src != src:
        with open(sanitizer_ts, 'w', encoding='utf-8') as f:
            f.write(new_src)
        print("Patched open-sse/services/opencodeReasoningSanitizer.ts")
    else:
        print("opencodeReasoningSanitizer.ts already up to date or pattern mismatch")

# 2. Patch chunks in dist/
for root, dirs, files in os.walk(os.path.join(base_dir, "dist")):
    for file in files:
        if file.endswith(('.js', '.mjs', '.cjs')):
            path = os.path.join(root, file)
            with open(path, 'r', encoding='utf-8', errors='ignore') as f:
                content = f.read()
            
            modified = False
            
            # Pattern 1
            p1 = 'function(e){if(!e||"object"!=typeof e||!("reasoning"in e)||"boolean"!=typeof e.reasoning)return e;let t={...e};return delete t.reasoning,t}'
            r1 = 'function(e){if(!e||"object"!=typeof e)return e;let t={...e};if("reasoning"in t&&"boolean"==typeof t.reasoning)delete t.reasoning;if("reasoning_effort"in t)delete t.reasoning_effort;return t}'
            if p1 in content:
                content = content.replace(p1, r1)
                modified = True
                
            # Pattern 2 (where function is defined with named parameters or helper)
            # Let's search for any remaining delete .reasoning in dist
            if modified:
                with open(path, 'w', encoding='utf-8') as f:
                    f.write(content)
                print(f"Patched chunk {os.path.relpath(path, base_dir)}")

