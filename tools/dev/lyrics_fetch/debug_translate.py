#!/usr/bin/env python3
"""Debug: test lyrics translation parse flow."""
import json, sys, urllib.request, os
sys.stdout.reconfigure(encoding='utf-8')

env = {}
for line in open(r'C:\Users\Ota\.omniroute\.env', 'r'):
    line = line.strip()
    if line and not line.startswith('#') and '=' in line:
        k, v = line.split('=', 1)
        env[k.strip()] = v.strip()
api_key = env.get('VISION_BRIDGE_API_KEY', '')

# Load one lyrics file
with open(r'C:\TMP\lyrics_fetch\story_json\lyrics\m1005_lyrics.json', 'r', encoding='utf-8') as f:
    data = json.load(f)

test = {k: v for k, v in list(data.items())[:8] if v.strip()}
print(f'Test payload ({len(test)} items):')
for k, v in test.items():
    print(f'  {k}: {v}')

system_prompt = """Translate Japanese song lyrics to English. These are timed lyrics. Return a JSON object with the SAME keys and English translations as values. Only return the JSON object."""

messages = [
    {"role": "system", "content": system_prompt},
    {"role": "user", "content": json.dumps(test, ensure_ascii=False)}
]
req_data = {
    "model": "antigravity/gemini-3.7-flash-low",
    "messages": messages,
    "temperature": 0.2,
    "max_tokens": 4000
}
req = urllib.request.Request(
    "http://127.0.0.1:20128/v1/chat/completions",
    data=json.dumps(req_data).encode("utf-8"),
    headers={"Authorization": f"Bearer {api_key}", "Content-Type": "application/json"}
)
with urllib.request.urlopen(req, timeout=30) as resp:
    body = json.loads(resp.read().decode("utf-8"))
    raw = body["choices"][0]["message"]["content"]
    print(f"\nRaw response ({len(raw)} chars):")
    print(raw[:800])
    
    # Parse like parse_translations does
    text = raw.strip()
    if text.startswith("```json"):
        text = text[7:]
    elif text.startswith("```"):
        text = text[3:]
    if text.endswith("```"):
        text = text[:-3]
    text = text.strip()
    
    parsed = json.loads(text)
    print(f"\nParsed type: {type(parsed)}")
    if isinstance(parsed, dict):
        print(f"Dict keys ({len(parsed)}): {list(parsed.keys())[:5]}")
        for k in test:
            if k in parsed:
                print(f"  MATCH: {k} -> {parsed[k][:60]}")
            else:
                print(f"  MISS: {k}")
    elif isinstance(parsed, list):
        print(f"List len: {len(parsed)}")
        for item in parsed[:3]:
            print(f"  {item}")
