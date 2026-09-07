with open(r'G:\Downloads\Documents\go-model-benchmarks.html', 'rb') as f:
    html = f.read()
nl = b"\n"
print(f"HTML file: {len(html)} bytes, {html.count(nl)} lines")
print(f"parseCell found: {html.find(b'parseCell') > 0}")
print(f"sortable found: {html.find(b'sortable') > 0}")
print(f"hamburger found: {html.find(b'hamburger') > 0}")
print(f"FAB found: {html.find(b'back-to-top-fab') > 0}")
print(f"table-wrap found: {html.find(b'table-wrap') > 0}")
print(f"PayPal found: {html.find(b'PayPal') > 0}")
print(f"details tags: {html.count(b'<details>')}")
print(f"Gemini 3.8 Flash found: {html.find(b'Gemini 3.8 Flash') > 0}")
print(f"Sep 3 found: {html.find(b'Sep 3') > 0}")
print(f"not yet released: {html.find(b'not yet released') > 0}")
print(f"18 models remnant: {html.find(b'18 models') > 0}")

with open(r'G:\Downloads\Documents\go-model-benchmarks.md', 'rb') as f:
    md = f.read()
print(f"\nMD file: {len(md)} bytes, {md.count(nl)} lines")
print(f"Gemini 3.8 Flash found: {md.find(b'Gemini 3.8 Flash') > 0}")
print(f"Sep 3 header: {md.find(b'Updated Sep 3, 2026') > 0}")
print(f"18 models remnant: {md.find(b'18 models') > 0}")
print(f"em-dash found: {md.find(b'\\xe2\\x80\\x94') > 0}")
# Count Gemini 3.8 Flash occurrences
count = md.count(b'Gemini 3.8 Flash')
print(f"Gemini 3.8 Flash count: {count}")
