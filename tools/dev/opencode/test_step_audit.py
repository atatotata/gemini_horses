import sys
import json
import traceback
from playwright.sync_api import sync_playwright

with open("C:/TMP/opencode/test_audit.log", "w", encoding="utf-8") as log_file:
    def log(msg):
        log_file.write(str(msg) + "\n")
        log_file.flush()
        print(msg)

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        page = browser.new_page(viewport={"width": 1440, "height": 900})

        console_errors = []
        page.on("console", lambda msg: console_errors.append(f"[{msg.type}] {msg.text} ({msg.location})") if msg.type in ["error", "warning"] else None)
        page.on("pageerror", lambda exc: console_errors.append(f"[UNCAUGHT] {exc}"))

        log("Step 1: Navigating to editor.html")
        page.goto("http://localhost:8000/editor.html", wait_until="networkidle")
        log(f"Page loaded. URL: {page.url}")

        log("Step 2: Checking global libraries")
        try:
            libs = page.evaluate("() => ({ THEME_GRAPHICS: !!window.THEME_GRAPHICS, SvgCommon: !!window.SvgCommon, PARTS_CATALOG: !!window.PARTS_CATALOG })")
            log(f"Libs: {libs}")
        except Exception as e:
            log(f"Error checking libs: {traceback.format_exc()}")

        log("Step 3: Checking initial DOM")
        try:
            dom = page.evaluate("() => ({ cards: document.querySelectorAll('.char-select-card').length, canvasSvg: !!document.querySelector('#stage-canvas svg'), placeholderDisplay: document.getElementById('stage-placeholder')?.style?.display })")
            log(f"DOM: {dom}")
        except Exception as e:
            log(f"Error checking DOM: {traceback.format_exc()}")

        log("Step 4: Selecting a character")
        try:
            res = page.evaluate("""() => {
                const card = document.querySelector('.char-select-card[data-char="miku"]');
                if (!card) return 'no miku card';
                card.click();
                return {
                    selected: card.classList.contains('selected'),
                    svgInCanvas: !!document.querySelector('#stage-canvas svg'),
                    svgHtmlLen: document.querySelector('#stage-canvas svg')?.innerHTML?.length
                };
            }""")
            log(f"Select Miku: {res}")
        except Exception as e:
            log(f"Error selecting miku: {traceback.format_exc()}")

        log("Step 5: Testing Expression dropdowns")
        try:
            res = page.evaluate("""() => {
                const eye = document.getElementById('eyes-select');
                const mouth = document.getElementById('mouth-select');
                eye.value = 'wink';
                eye.dispatchEvent(new Event('change', { bubbles: true }));
                mouth.value = 'shock';
                mouth.dispatchEvent(new Event('change', { bubbles: true }));
                return { eye: eye.value, mouth: mouth.value };
            }""")
            log(f"Expressions: {res}")
        except Exception as e:
            log(f"Error testing expressions: {traceback.format_exc()}")

        log("Step 6: Testing Scratch Builder tab")
        try:
            res = page.evaluate("""() => {
                const tab = document.getElementById('tab-mode-scratch');
                tab.click();
                const panel = document.getElementById('panel-mode-scratch');
                return {
                    tabActive: tab.classList.contains('active'),
                    panelDisplay: getComputedStyle(panel).display,
                    templatesCount: document.querySelectorAll('.scratch-template-btn').length,
                    partsCount: document.querySelectorAll('.scratch-part-card').length
                };
            }""")
            log(f"Scratch tab: {res}")
        except Exception as e:
            log(f"Error testing scratch tab: {traceback.format_exc()}")

        log("Step 7: Testing Layers tab & properties")
        try:
            res = page.evaluate("""() => {
                const tab = document.getElementById('tab-mode-layers');
                tab.click();
                const panel = document.getElementById('panel-mode-layers');
                const items = document.querySelectorAll('.layer-item');
                return {
                    tabActive: tab.classList.contains('active'),
                    panelDisplay: getComputedStyle(panel).display,
                    layerItemsCount: items.length
                };
            }""")
            log(f"Layers tab: {res}")
        except Exception as e:
            log(f"Error testing layers tab: {traceback.format_exc()}")

        log("Step 8: Testing Export modal")
        try:
            res = page.evaluate("""() => {
                const btn = document.getElementById('btn-export');
                btn.click();
                const modal = document.getElementById('export-modal');
                const code = document.getElementById('export-code-box');
                const isActive = modal ? modal.classList.contains('active') : false;
                const hasSvg = code ? code.value.includes('<svg') : false;
                // close modal
                document.getElementById('btn-close-modal')?.click();
                return { isActive, hasSvg, codePreview: code?.value?.substring(0, 80) };
            }""")
            log(f"Export modal: {res}")
        except Exception as e:
            log(f"Error testing export modal: {traceback.format_exc()}")

        log("Step 9: Console errors captured")
        log(f"Total console errors: {len(console_errors)}")
        for err in console_errors:
            log(f"  ERR: {err}")

        browser.close()
log("Audit finished.")
