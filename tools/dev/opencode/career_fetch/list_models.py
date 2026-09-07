import os, json, urllib.request, pathlib
env_path = r"C:\Users\Ota\.omniroute\.env"
api_key=""
if os.path.exists(env_path):
    for line in open(env_path, encoding="utf-8", errors="ignore"):
        line=line.strip()
        if line.startswith("API_KEY="):
            api_key=line.split("=",1)[1].strip('"\' ')
            break
print(f"key prefix {api_key[:10]}...")
req = urllib.request.Request("http://localhost:20128/v1/models", headers={"Authorization": f"Bearer {api_key}"})
data = json.loads(urllib.request.urlopen(req, timeout=10).read().decode())
models = [m["id"] for m in data["data"]]
# filter cheaper/fast candidates
for m in models:
    print(m)
print(f"\nTotal {len(models)}")
# print candidates
cands = [m for m in models if any(k in m for k in ["flash-low","flash-lite","muse-spark","mistral","qwen","kimi","haiku","mini"])]
print("\n--- candidates ---")
for c in cands[:80]:
    print(c)
