#!/usr/bin/env python3
"""Get API key and verify endpoint."""
import re, urllib.request, json

# Read env
env = {}
for line in open(r'C:\Users\Ota\.omniroute\.env', 'r'):
    line = line.strip()
    if line and not line.startswith('#') and '=' in line:
        k, v = line.split('=', 1)
        env[k.strip()] = v.strip()

api_key = env.get('VISION_BRIDGE_API_KEY', '')
print(f"API key: {api_key[:8]}...{api_key[-4:]}")

# Test endpoint
API_URL = "http://127.0.0.1:20128/v1/chat/completions"
try:
    data = {
        "model": "gemini-2.5-flash-lite-preview",
        "messages": [{"role": "user", "content": "Say hello"}],
        "max_tokens": 10,
        "temperature": 0.1
    }
    req = urllib.request.Request(
        API_URL,
        data=json.dumps(data).encode("utf-8"),
        headers={
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json"
        }
    )
    with urllib.request.urlopen(req, timeout=10) as resp:
        body = json.loads(resp.read().decode("utf-8"))
        print(f"API response: {body['choices'][0]['message']['content'][:100]}")
        print(f"Model used: {body.get('model', 'unknown')}")
except Exception as e:
    print(f"API error: {e}")

# Try to get available models
try:
    req2 = urllib.request.Request(
        "http://127.0.0.1:20128/v1/models",
        headers={"Authorization": f"Bearer {api_key}"}
    )
    with urllib.request.urlopen(req2, timeout=10) as resp2:
        models = json.loads(resp2.read().decode("utf-8"))
        for m in models.get('data', []):
            print(f"  Model: {m.get('id', '?')}")
except Exception as e:
    print(f"Models list error: {e}")
