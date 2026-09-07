import urllib.request
import json
import os
import time

key = ""
env_path = r"C:\Users\Ota\.omniroute\.env"
if os.path.exists(env_path):
    with open(env_path, encoding="utf-8", errors="ignore") as f:
        for line in f:
            line = line.strip()
            if line.startswith("API_KEY="):
                key = line.split("=", 1)[1].strip('"\' ')
                break

test_payload = {
    "model": "opencode-go/muse-spark-1.2-contributor",
    "messages": [
        {
            "role": "system",
            "content": "You are an expert Japanese to English translator for Umamusume Pretty Derby.\nTranslate the following JSON array of dialogue and choice texts into English.\nPreserve tags like <chrname>, <support>, and newline \\n exactly.\nReturn ONLY a JSON array of objects: [{\"id\": <id>, \"en\": \"<translated>\"}]."
        },
        {
            "role": "user",
            "content": json.dumps([
                {"id": 1, "jp": "アグネスタキオンの見せた輝きは、会場中の注目を集めていた――！"},
                {"id": 2, "jp": "フー！　こんなものかな！"},
                {"id": 3, "jp": "ぜえ、ぜえ……なんでいきなり登山……？"},
                {"id": 4, "jp": "うおおおお！！　ラストスパ――――ート！！"},
                {"id": 5, "jp": "お誘いありがとうございます。\nしかし教官の先生より、『継続は力なり』と教わりましたので。"}
            ], ensure_ascii=False)
        }
    ],
    "max_tokens": 1000,
    "temperature": 0.2
}

req = urllib.request.Request(
    "http://localhost:20128/v1/chat/completions",
    headers={"Authorization": f"Bearer {key}", "Content-Type": "application/json"},
    data=json.dumps(test_payload).encode("utf-8")
)

t0 = time.time()
try:
    with urllib.request.urlopen(req, timeout=30) as resp:
        t1 = time.time()
        res = json.loads(resp.read().decode("utf-8"))
        raw = res["choices"][0]["message"]["content"]
        print(f"Elapsed: {t1-t0:.2f}s")
        import sys
        sys.stdout.buffer.write(raw.encode('utf-8') + b'\n')
        # Try parse
        if "```json" in raw:
            raw = raw.split("```json")[1].split("```")[0].strip()
        elif "```" in raw:
            raw = raw.split("```")[1].split("```")[0].strip()
        parsed = json.loads(raw)
        print("Parsed count:", len(parsed))
except Exception as e:
    print("Error:", e)
