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
try:
    with urllib.request.urlopen(req, context=ctx, timeout=30) as resp:
        data = json.loads(resp.read().decode())
        print('OK', resp.status)
        print(data['choices'][0]['message']['content'][:500])
except urllib.error.HTTPError as e:
    print(f'HTTPError {e.code}: {e.reason}')
    try:
        print(e.read().decode()[:3000])
    except: pass
except Exception as e:
    import traceback; traceback.print_exc()
