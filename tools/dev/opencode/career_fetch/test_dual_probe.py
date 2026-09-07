import os
import sys
import json
import time
import urllib.request

env_path = r"C:\Users\Ota\.omniroute\.env"
key = ""
if os.path.exists(env_path):
    with open(env_path, encoding="utf-8", errors="ignore") as f:
        for line in f:
            line = line.strip()
            if line.startswith("API_KEY="):
                key = line.split("=", 1)[1].strip('"\' ')
                break

headers = {"Authorization": f"Bearer {key}", "Content-Type": "application/json"}

sample_items = [
    {"id": 1, "jp": "アグネスタキオンの見せた輝きは、会場中の注目を集めていた――！"},
    {"id": 2, "jp": "フー！　こんなものかな！"},
    {"id": 3, "jp": "ぜえ、ぜえ……なんでいきなり登山……？"},
    {"id": 4, "jp": "うおおおお！！　ラストスパ――――ート！！"},
    {"id": 5, "jp": "お誘いありがとうございます。\nしかし教官の先生より、『継続は力なり』と教わりましたので。"},
    {"id": 6, "jp": "息抜きもトレーニングのうち！"},
    {"id": 7, "jp": "よし、じゃあみんなで美味しいアイスを食べに行こう！"},
    {"id": 8, "jp": "今日のトレーニングメニューはどうする？"},
    {"id": 9, "jp": "全力で駆け抜けるぞ！"},
    {"id": 10, "jp": "トレーナー、見ててくれた？"}
]

system_prompt = """You are an expert Japanese-to-English translator for Umamusume: Pretty Derby.
Translate the following JSON array of Japanese texts into natural, engaging English.
Preserve tokens like <chrname>, <support>, \\n, and formatting tags exactly.
Return strictly a JSON array of objects: [{"id": <id>, "en": "<translated_text>"}]."""

def test_model(model_name):
    payload = {
        "model": model_name,
        "messages": [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": json.dumps(sample_items, ensure_ascii=False)}
        ],
        "temperature": 0.2,
        "max_tokens": 1500
    }
    req = urllib.request.Request("http://localhost:20128/v1/chat/completions", headers=headers, data=json.dumps(payload).encode("utf-8"))
    t0 = time.time()
    try:
        with urllib.request.urlopen(req, timeout=30) as resp:
            t1 = time.time()
            data = json.loads(resp.read().decode("utf-8"))
            content = data["choices"][0]["message"]["content"]
            # clean json
            clean = content.strip()
            if "```json" in clean:
                clean = clean.split("```json")[1].split("```")[0].strip()
            elif "```" in clean:
                clean = clean.split("```")[1].split("```")[0].strip()
            parsed = json.loads(clean)
            print(f"[{model_name}] SUCCESS in {t1-t0:.2f}s! Parsed {len(parsed)} items.")
            return True
    except Exception as ex:
        print(f"[{model_name}] ERROR: {ex}")
        return False

print("Testing Gemini Flash Low...")
test_model("antigravity/gemini-3.7-flash-low")

print("\nTesting Muse Spark Contributor...")
test_model("opencode-go/muse-spark-1.2-contributor")
