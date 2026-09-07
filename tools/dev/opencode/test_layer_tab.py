import sys
import json
from playwright.sync_api import sync_playwright

with sync_playwright() as p:
    browser = p.chromium.launch(headless=True)
    page = browser.new_page()
    page.goto('http://localhost:8000/editor.html')
    
    res = page.evaluate("""() => {
        const rin = document.querySelector('.char-select-card[data-char="rin"]');
        if (rin) rin.click();
        const tab = document.getElementById('tab-mode-layers');
        if (tab) tab.click();
        
        const list = document.getElementById('layer-stack-list');
        return {
            itemsCount: document.querySelectorAll('.layer-item').length,
            hasEmptyState: !!document.querySelector('.layer-empty-state'),
            innerHTMLSnippet: list ? list.innerHTML.substring(0, 100) : null
        };
    }""")
    with open('C:/TMP/opencode/layer_tab.json', 'w', encoding='utf-8') as f:
        json.dump(res, f, indent=2)
    browser.close()
