import urllib.request
import json
import os

key = ""
env_path = r"C:\Users\Ota\.omniroute\.env"
if os.path.exists(env_path):
    with open(env_path, encoding="utf-8", errors="ignore") as f:
        for line in f:
            line = line.strip()
            if line.startswith("API_KEY="):
                key = line.split("=", 1)[1].strip('"\' ')
                break

print(f"Key found: {key[:8]}...")

req = urllib.request.Request(
    "http://localhost:20128/v1/chat/completions",
    headers={"Authorization": f"Bearer {key}", "Content-Type": "application/json"},
    data=json.dumps({
        "model": "opencode-go/muse-spark-1.2-contributor",
        "messages": [{"role": "user", "content": "Translate to English: おはようございます！今日も一日頑張りましょう！"}],
        "max_tokens": 100
    }).encode("utf-8")
)

try:
    with urllib.request.urlopen(req, timeout=15) as resp:
        res = json.loads(resp.read().decode("utf-8"))
        print("Success!")
        print("Content:", res["choices"][0]["message"]["content"])
except Exception as e:
    print("Error:", e)
    if hasattr(e, "read"):
        print("Error body:", e.read().decode("utf-8"))
