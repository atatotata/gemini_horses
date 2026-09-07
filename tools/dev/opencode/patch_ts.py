import os

base_dir = r"C:\Users\Ota\AppData\Local\pnpm\global\v11\3d68-1a057194ffe-925c3c4f3f829bae\node_modules\omniroute"
sanitizer_ts = os.path.join(base_dir, r"open-sse\services\opencodeReasoningSanitizer.ts")

with open(sanitizer_ts, 'r', encoding='utf-8', errors='ignore') as f:
    code = f.read()

new_func = """export function stripBooleanReasoning(body: JsonRecord): JsonRecord {
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

import re
code_patched = re.sub(
    r'export function stripBooleanReasoning\(body: JsonRecord\): JsonRecord \{[\s\S]*?\n\}',
    new_func,
    code
)

with open(sanitizer_ts, 'w', encoding='utf-8') as f:
    f.write(code_patched)

print("Updated open-sse/services/opencodeReasoningSanitizer.ts successfully.")
