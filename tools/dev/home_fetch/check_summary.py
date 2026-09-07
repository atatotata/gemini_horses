import json
with open(r'C:\TMP\home_fetch\extraction_summary.json', 'r', encoding='utf-8') as f:
    data = json.load(f)
print('=== SUMMARY ===')
for k, v in data.items():
    if k not in ('tasks', 'extract_errors'):
        print(f'  {k}: {v}')
errs = data.get('extract_errors', [])
if errs:
    print(f'\nExtract errors ({len(errs)}):')
    for e in errs[:10]:
        print(f'  {e}')
