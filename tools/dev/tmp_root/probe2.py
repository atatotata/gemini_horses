import json, urllib.request, urllib.error, ssl
API_BASE='http://127.0.0.1:20128/v1'
API_KEY='sk-ae42a2661869ce17-4433c6-9b6f4115'
MODEL='antigravity/gemini-3.7-flash-low'
body = {
    "model": MODEL,
    "messages": [
        {"role": "system", "content": "You are a translator."},
        {"role": "user", "content": 'Translate to EN: {"translations":[{"id":"test","jp_name":"trainer","jp_text":"hello","jp_choices":[]}]}  \nReturn JSON: {"translations":[{"id":"test","name":"Trainer","text":"Hello","choices":[]}]}'}
    ],
    "temperature": 0.2,
    "max_tokens": 2000
}
payload = json.dumps(body).encode()
req = urllib.request.Request(f'{API_BASE}/chat/completions', data=payload, headers={'Authorization': f'Bearer {API_KEY}', 'Content-Type': 'application/json'})
ctx = ssl._create_unverified_context()
with urllib.request.urlopen(req, context=ctx, timeout=30) as resp:
    raw = resp.read()
    print(f"RAW len {len(raw)} status {resp.status}")
    print(repr(raw[:2000]))
    data = json.loads(raw.decode())
    print("choices:", len(data.get('choices',[])))
    content = data['choices'][0]['message']['content']
    print(f"CONTENT len {len(content)}")
    print(repr(content[:1000]))
