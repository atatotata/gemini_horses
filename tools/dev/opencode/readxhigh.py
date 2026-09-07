import re
txt = open(r'C:\Users\Ota\.config\opencode\opencode.jsonc', encoding='utf-8').read()
# Search for reasoning mentions
for i, line in enumerate(txt.splitlines(), 1):
    if 'reasoning' in line.lower():
        print(f"{i}: {line}")

# Find xhigh block
start = txt.find('"opencode-go/muse-spark-1.2-contributor-xhigh"')
print("\n=== xhigh block ===")
print(txt[start:start+3000])
