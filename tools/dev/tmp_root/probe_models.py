import json, urllib.request, urllib.error, ssl, time
API_BASE='http://127.0.0.1:20128/v1'
API_KEY='sk-ae42a2661869ce17-4433c6-9b6f4115'
MODELS=[
    "antigravity/gemini-3.7-flash-low",
    "antigravity/gemini-3.1-flash-lite",
    "mistral/mistral-small-latest",
    "mistral/magistral-small-latest",
    "mistral/mistral-large-latest",
]
ctx = ssl._create_unverified_context()
for MODEL in MODELS:
    body = {
        "model": MODEL,
        "messages": [
            {"role": "system", "content": "You are a translator."},
            {"role": "user", "content": 'Return JSON: {"translations":[{"id":"test","name":"Trainer","text":"Hello","choices":[]}]}'}
        ],
        "temperature": 0.2,
        "max_tokens": 200,
    }
    payload = json.dumps(body).encode()
    req = urllib.request.Request(f'{API_BASE}/chat/completions', data=payload, headers={'Authorization': f'Bearer {API_KEY}', 'Content-Type': 'application/json'})
    t0=time.time()
    try:
        with urllib.request.urlopen(req, context=ctx, timeout=20) as resp:
            data=json.loads(resp.read().decode())
            content=data['choices'][0]['message']['content']
            dt=time.time()-t0
            print(f"OK  {MODEL:40} {resp.status} {dt:.1f}s -> {content[:120].replace(chr(10),' ')}")
    except urllib.error.HTTPError as e:
        dt=time.time()-t0
        try:
            body=e.read().decode()[:400].replace('\n',' ')
        except: body=""
        print(f"ERR {MODEL:40} {e.code} {dt:.1f}s {e.reason} {body[:200]}")
    except Exception as e:
        dt=time.time()-t0
        print(f"ERR {MODEL:40} {type(e).__name__} {dt:.1f}s {e}")
    time.sleep(0.5)
