import re

with open(r'G:\Downloads\Documents\go-model-benchmarks.html', 'r', encoding='utf-8-sig') as f:
    html = f.read()

# Fix watchlist
old_watchlist = '<div class="note-box" style="margin-top:10px;"><strong>Watchlist (Sep 2):</strong>'
new_watchlist = '<div class="note-box" style="margin-top:10px;"><strong>Watchlist (Sep 3):</strong>'
html = html.replace(old_watchlist, new_watchlist, 1)

# Replace the Gemini 3.8 Flash "not yet released" text
old_wl_content = 'Gemini 3.8 Flash "Skimaki" \u2014 WSJ Sep 1: as soon as Sep 2 (not yet released at check) \u00b7 Hy4 GA still preview only (no change)'
new_wl_content = 'Hy4 GA still preview only (no change) \u00b7 Gemini 3.8 Flash Cyber (sister model, cyber-specialized) pending GA'
html = html.replace(old_wl_content, new_wl_content, 1)

with open(r'G:\Downloads\Documents\go-model-benchmarks.html', 'w', encoding='utf-8-sig') as f:
    f.write(html)

print("Watchlist fixed")
