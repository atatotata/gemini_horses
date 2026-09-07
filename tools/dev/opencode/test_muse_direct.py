import sqlite3, json, urllib.request, urllib.error

conn = sqlite3.connect(r'C:\Users\Ota\.omniroute\storage.sqlite')
cur = conn.cursor()
cur.execute("SELECT key FROM registered_keys LIMIT 1")
row = cur.fetchone()
proxy_key = row[0] if row else "test"
conn.close()

url = "http://localhost:20128/v1/chat/completions"
# Send with reasoning_effort to test that the sanitizer strips it before upstream
payload = {
    "model": "opencode-go/muse-spark-1.2-contributor",
    "messages": [{"role": "user", "content": "Respond with single word: OK"}],
    "reasoning_effort": "xhigh",
    "max_tokens": 10
}

data = json.dumps(payload).encode('utf-8')
req = urllib.request.Request(
    url,
    data=data,
    headers={
        "Content-Type": "application/json",
        "Authorization": f"Bearer {proxy_key}"
    }
)

try:
    with urllib.request.urlopen(req, timeout=20) as resp:
        print("HTTP", resp.status)
        body = json.loads(resp.read().decode('utf-8'))
        print("Response:", body.get('choices', [{}])[0].get('message', {}).get('content', ''))
except urllib.error.HTTPError as e:
    print(f"HTTP {e.code}: {e.read().decode('utf-8', errors='ignore')}")
except Exception as e:
    print("Error:", e)
