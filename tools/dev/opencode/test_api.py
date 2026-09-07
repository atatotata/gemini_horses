import requests, json
API_URL = "http://127.0.0.1:20128/v1/chat/completions"
API_KEY = "sk-ae42a2661869ce17-4433c6-9b6f4115"
headers = {"Authorization": f"Bearer {API_KEY}", "Content-Type": "application/json"}
payload = {
    "model": "antigravity/gemini-3.7-flash-low",
    "messages": [
        {"role": "system", "content": "Translate JP to EN. Return JSON."},
        {"role": "user", "content": json.dumps({"Test001": "ゲーム開始"}, ensure_ascii=False)}
    ],
    "temperature": 0.2,
    "max_tokens": 4000,
    "response_format": {"type": "json_object"}
}
try:
    resp = requests.post(API_URL, json=payload, headers=headers, timeout=30)
    print(f"Status: {resp.status_code}")
    print(f"Body (first 1000): {resp.text[:1000]}")
except Exception as e:
    print(f"Error: {e}")
