import urllib.request
import json
import os

env_path = r"C:\Users\Ota\.omniroute\.env"
api_key = ""
with open(env_path, encoding="utf-8", errors="ignore") as f:
    for line in f:
        line = line.strip()
        if line.startswith("VISION_BRIDGE_API_KEY="):
            api_key = line.split("=", 1)[1].strip("\"' ")
            break
        elif line.startswith("API_KEY="):
            api_key = line.split("=", 1)[1].strip("\"' ")

print(f"API key length: {len(api_key)}, last4: ...{api_key[-4:]}")
headers = {"Authorization": f"Bearer {api_key}", "Content-Type": "application/json"}
payload = {
    "model": "antigravity/gemini-3.7-flash-low",
    "messages": [{"role": "user", "content": "Say hi in 5 words"}],
    "temperature": 0.2,
    "max_tokens": 50
}
data = json.dumps(payload).encode("utf-8")
req = urllib.request.Request("http://localhost:20128/v1/chat/completions", headers=headers, data=data)
try:
    with urllib.request.urlopen(req, timeout=15) as resp:
        rd = json.loads(resp.read().decode("utf-8"))
        print(f"API OK: {rd['choices'][0]['message']['content']}")
except Exception as e:
    print(f"API ERROR: {e}")
