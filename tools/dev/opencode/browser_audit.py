import sys
import json
import time

if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8')
if hasattr(sys.stderr, 'reconfigure'):
    sys.stderr.reconfigure(encoding='utf-8')

from playwright.sync_api import sync_playwright

def run_audit():
    results = {
        "console_errors": [],
        "console_warnings": [],
        "network_failures": [],
        "tests": []
    }
    
    out_f = open("C:/TMP/opencode/audit_log.txt", "w", encoding="utf-8")
    def my_print(*args):
        text = " ".join(str(a) for a in args)
        out_f.write(text + "\n")
        out_f.flush()
        print(text, flush=True)

    def log_test(name, status, details=None):
        results["tests"].append({
            "name": name,
            "status": "PASS" if status else "FAIL",
            "details": details or ""
        })
        status_str = "PASS" if status else "FAIL"
        my_print(f"[{status_str}] {name} {details or ''}")

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        context = browser.new_context(viewport={"width": 1440, "height": 900})
        page = context.new_page()

        # Listen to console
        page.on("console", lambda msg: (
            results["console_errors"].append(f"[{msg.type}] {msg.text} ({msg.location})")
            if msg.type in ["error"]
            else results["console_warnings"].append(f"[{msg.type}] {msg.text}")
            if msg.type in ["warning"]
            else None
        ))
        
        # Listen to page errors (uncaught exceptions)
        page.on("pageerror", lambda exc: results["console_errors"].append(f"[UNCAUGHT] {str(exc)}"))

        # Listen to failed requests
        page.on("requestfailed", lambda req: results["network_failures"].append(f"{req.method} {req.url} - {req.failure}"))
        page.on("response", lambda res: results["network_failures"].append(f"{res.status} {res.url}") if res.status >= 400 else None)

        my_print("--- Navigating to http://localhost:8000/editor.html ---")
        try:
            page.goto("http://localhost:8000/editor.html", wait_until="networkidle", timeout=10000)
            log_test("Page Load", True)
        except Exception as e:
            log_test("Page Load", False, str(e))
            browser.close()
            return results

        time.sleep(1)

        # 1. Check loaded scripts and libraries
        libs_loaded = page.evaluate("""() => {
            return {
                THEME_GRAPHICS: typeof window.THEME_GRAPHICS !== 'undefined',
                SvgCommon: typeof window.SvgCommon !== 'undefined',
                PARTS_CATALOG: typeof window.PARTS_CATALOG !== 'undefined',
                PARTS_CATEGORIES: typeof window.PARTS_CATEGORIES !== 'undefined'
            };
        }""")
        log_test("Global Libraries Loaded", all(libs_loaded.values()), json.dumps(libs_loaded))

        # 2. Check initial DOM state
        dom_initial = page.evaluate("""() => {
            const cards = document.querySelectorAll('.char-select-card');
            const placeholder = document.getElementById('stage-placeholder');
            const canvas = document.getElementById('stage-canvas');
            return {
                cardCount: cards.length,
                placeholderVisible: placeholder ? getComputedStyle(placeholder).display !== 'none' : false,
                canvasVisible: canvas ? getComputedStyle(canvas).display !== 'none' : false,
                canvasHasSvg: canvas ? !!canvas.querySelector('svg') : false,
                activeCard: document.querySelector('.char-select-card.selected') ? document.querySelector('.char-select-card.selected').dataset.char : null
            };
        }""")
        log_test("Initial Character Grid Rendered", dom_initial["cardCount"] > 0, f"Found {dom_initial['cardCount']} cards, active: {dom_initial['activeCard']}")

        # 3. Test Base Character selection
        card_click_result = page.evaluate("""() => {
            const mikuCard = Array.from(document.querySelectorAll('.char-select-card')).find(c => c.dataset.char === 'miku');
            if (!mikuCard) return { success: false, reason: 'miku card not found' };
            mikuCard.click();
            const canvas = document.getElementById('stage-canvas');
            const svg = canvas ? canvas.querySelector('svg') : null;
            return {
                success: true,
                selected: mikuCard.classList.contains('selected'),
                svgExists: !!svg,
                svgContentLength: svg ? svg.innerHTML.length : 0
            };
        }""")
        log_test("Select Character 'miku'", card_click_result.get("success") and card_click_result.get("svgExists"), json.dumps(card_click_result))

        # 4. Test Search & Filter Tabs
        filter_result = page.evaluate("""() => {
            // Click Vocaloid filter
            const vocaloidTab = Array.from(document.querySelectorAll('.theme-filter-tab')).find(t => t.textContent.includes('Vocaloid'));
            if (!vocaloidTab) return { success: false, reason: 'Vocaloid tab not found' };
            vocaloidTab.click();
            const vocaloidCount = Array.from(document.querySelectorAll('.char-select-card')).filter(c => c.style.display !== 'none').length;
            
            // Search 'rin'
            const searchInput = document.getElementById('char-search-input');
            if (!searchInput) return { success: false, reason: 'Search input not found' };
            searchInput.value = 'rin';
            searchInput.dispatchEvent(new Event('input', { bubbles: true }));
            const rinCount = Array.from(document.querySelectorAll('.char-select-card')).filter(c => c.style.display !== 'none').length;
            
            // Reset search and tab
            searchInput.value = '';
            searchInput.dispatchEvent(new Event('input', { bubbles: true }));
            const allTab = Array.from(document.querySelectorAll('.theme-filter-tab')).find(t => t.textContent.includes('All'));
            if (allTab) allTab.click();

            return {
                success: true,
                vocaloidCount,
                rinCount
            };
        }""")
        log_test("Character Search & Filter Tabs", filter_result.get("success") and filter_result.get("rinCount", 0) > 0, json.dumps(filter_result))

        # 5. Test Step 2: Expressions dropdown & preset buttons
        expr_result = page.evaluate("""() => {
            const eyesSelect = document.getElementById('eyes-select');
            const mouthSelect = document.getElementById('mouth-select');
            if (!eyesSelect || !mouthSelect) return { success: false, reason: 'Selects not found' };

            eyesSelect.value = 'wink';
            eyesSelect.dispatchEvent(new Event('change', { bubbles: true }));
            mouthSelect.value = 'shock';
            mouthSelect.dispatchEvent(new Event('change', { bubbles: true }));

            // Test quick preset chip
            const angryChip = Array.from(document.querySelectorAll('.expr-preset-btn')).find(b => b.textContent.includes('Angry'));
            if (angryChip) angryChip.click();

            return {
                success: true,
                eyesVal: eyesSelect.value,
                mouthVal: mouthSelect.value
            };
        }""")
        log_test("Expressions Dropdowns & Quick Presets", expr_result.get("success") and expr_result.get("eyesVal") == "angry", json.dumps(expr_result))

        # 6. Test Step 3: Color slots & Accessories
        color_acc_result = page.evaluate("""() => {
            const colorSlots = document.querySelectorAll('.color-slot-input');
            let colorChanged = false;
            if (colorSlots.length > 0) {
                const firstInput = colorSlots[0];
                const oldVal = firstInput.value;
                firstInput.value = '#FF0055';
                firstInput.dispatchEvent(new Event('input', { bubbles: true }));
                firstInput.dispatchEvent(new Event('change', { bubbles: true }));
                colorChanged = true;
            }

            // Test accessory toggle
            const blushCard = document.querySelector('.accessory-toggle-card[data-accessory="blush"]');
            let blushActive = false;
            if (blushCard) {
                blushCard.click();
                blushActive = blushCard.classList.contains('active');
            }

            const canvas = document.getElementById('stage-canvas');
            const svg = canvas ? canvas.querySelector('svg') : null;

            return {
                success: true,
                slotsCount: colorSlots.length,
                colorChanged,
                blushActive,
                hasSvg: !!svg
            };
        }""")
        log_test("Color Slots Recolor & Accessory Toggles", color_acc_result.get("slotsCount", 0) > 0 and color_acc_result.get("blushActive"), json.dumps(color_acc_result))

        # 7. Test Zoom & Pan controls
        zoom_result = page.evaluate("""() => {
            const zoomIn = document.getElementById('zoom-in');
            const zoomOut = document.getElementById('zoom-out');
            const zoomReset = document.getElementById('zoom-reset');
            const canvas = document.getElementById('stage-canvas');
            
            if (!zoomIn || !zoomReset || !canvas) return { success: false, reason: 'Zoom controls missing' };
            const initialTransform = canvas.style.transform;
            zoomIn.click();
            const afterInTransform = canvas.style.transform;
            zoomReset.click();
            const afterResetTransform = canvas.style.transform;

            return {
                success: true,
                initialTransform,
                afterInTransform,
                afterResetTransform,
                zoomWorked: afterInTransform !== initialTransform && afterInTransform !== afterResetTransform
            };
        }""")
        log_test("Zoom & Pan Stage Controls", zoom_result.get("zoomWorked", False), json.dumps(zoom_result))

        # 8. Test Mode Switcher: Scratch Builder
        scratch_mode_result = page.evaluate("""() => {
            const scratchTab = document.getElementById('tab-mode-scratch');
            if (!scratchTab) return { success: false, reason: 'tab-mode-scratch not found' };
            scratchTab.click();

            const scratchPanel = document.getElementById('panel-mode-scratch');
            const isVisible = scratchPanel && getComputedStyle(scratchPanel).display !== 'none';
            const templates = document.querySelectorAll('.scratch-template-btn');
            const parts = document.querySelectorAll('.scratch-part-card');

            // Click an anime school template
            const schoolTpl = Array.from(templates).find(t => t.textContent.includes('School'));
            if (schoolTpl) schoolTpl.click();

            const canvas = document.getElementById('stage-canvas');
            const svg = canvas ? canvas.querySelector('svg') : null;

            return {
                success: true,
                isVisible,
                templateCount: templates.length,
                partCount: parts.length,
                svgRenderedAfterTemplate: !!svg
            };
        }""")
        log_test("Scratch Builder Mode & Template Click", scratch_mode_result.get("isVisible", False) and scratch_mode_result.get("svgRenderedAfterTemplate", False), json.dumps(scratch_mode_result))

        # 9. Test Scratch Builder Part Category Tabs & Adding Parts
        scratch_cat_result = page.evaluate("""() => {
            const hairTab = Array.from(document.querySelectorAll('.scratch-cat-tab')).find(t => t.dataset.category === 'hair_front');
            if (!hairTab) return { success: false, reason: 'hair_front tab not found' };
            hairTab.click();

            const partsGrid = document.getElementById('scratch-parts-grid');
            const cards = partsGrid ? partsGrid.querySelectorAll('.scratch-part-card') : [];
            
            // Click first part card
            let partAdded = false;
            if (cards.length > 0) {
                cards[0].click();
                partAdded = true;
            }

            return {
                success: true,
                cardCount: cards.length,
                partAdded
            };
        }""")
        log_test("Scratch Part Categories & Selection", scratch_cat_result.get("cardCount", 0) > 0 and scratch_cat_result.get("partAdded"), json.dumps(scratch_cat_result))

        # 10. Test Layers Mode & Layer Stack
        layers_mode_result = page.evaluate("""() => {
            const layersTab = document.getElementById('tab-mode-layers');
            if (!layersTab) return { success: false, reason: 'tab-mode-layers not found' };
            layersTab.click();

            const layersPanel = document.getElementById('panel-mode-layers');
            const isVisible = layersPanel && getComputedStyle(layersPanel).display !== 'none';
            const layerItems = document.querySelectorAll('.layer-item');
            
            // Test selecting first layer to populate properties
            let propsPopulated = false;
            if (layerItems.length > 0) {
                layerItems[0].click();
                const nameInput = document.getElementById('layer-prop-name');
                const opacitySlider = document.getElementById('layer-prop-opacity');
                propsPopulated = !!(nameInput && nameInput.value);
            }

            // Test Add Layer modal button
            const addLayerBtn = document.getElementById('btn-add-layer');
            let modalOpened = false;
            if (addLayerBtn) {
                addLayerBtn.click();
                const modal = document.getElementById('add-layer-modal');
                modalOpened = modal && modal.classList.contains('active');
                
                // Close modal
                const closeBtn = document.getElementById('modal-close-add-layer');
                if (closeBtn) closeBtn.click();
            }

            return {
                success: true,
                isVisible,
                layerCount: layerItems.length,
                propsPopulated,
                modalOpened
            };
        }""")
        log_test("Layer Stack Manager & Add Layer Modal", layers_mode_result.get("isVisible", False) and layers_mode_result.get("layerCount", 0) > 0, json.dumps(layers_mode_result))

        # 11. Test Decompose to Layers from Remix Mode
        decompose_result = page.evaluate("""() => {
            // Switch back to Remix
            const remixTab = document.getElementById('tab-mode-remix');
            if (remixTab) remixTab.click();

            // Select a character first to ensure base is set
            const charCard = document.querySelector('.char-select-card');
            if (charCard) charCard.click();

            const decompBtn = document.getElementById('btn-decompose-remix');
            if (!decompBtn) return { success: false, reason: 'btn-decompose-remix not found' };
            decompBtn.click();

            const layersPanel = document.getElementById('panel-mode-layers');
            const isVisible = layersPanel && getComputedStyle(layersPanel).display !== 'none';
            const layerItems = document.querySelectorAll('.layer-item');

            return {
                success: true,
                isVisible,
                decomposedLayerCount: layerItems.length
            };
        }""")
        log_test("Decompose Remix Character to Layers", decompose_result.get("isVisible", False) and decompose_result.get("decomposedLayerCount", 0) >= 3, json.dumps(decompose_result))

        # 12. Test Export Modal
        export_modal_result = page.evaluate("""() => {
            const exportBtn = document.getElementById('btn-export');
            if (!exportBtn) return { success: false, reason: 'btn-export not found' };
            exportBtn.click();

            const modal = document.getElementById('export-modal');
            const isActive = modal && modal.classList.contains('active');
            const codeBox = document.getElementById('export-code-box');
            const hasSvgCode = codeBox && codeBox.value.includes('<svg');
            const downloadSvgBtn = document.getElementById('btn-download-svg');
            const downloadPngBtn = document.getElementById('btn-download-png');

            // Close modal
            const closeBtn = document.getElementById('btn-close-modal');
            if (closeBtn) closeBtn.click();

            return {
                success: true,
                isActive,
                hasSvgCode,
                downloadSvgBtn: !!downloadSvgBtn,
                downloadPngBtn: !!downloadPngBtn
            };
        }""")
        log_test("Export Modal & Generated SVG Code", export_modal_result.get("isActive", False) and export_modal_result.get("hasSvgCode", False), json.dumps(export_modal_result))

        # 13. Test Save/Randomize/Share State
        state_result = page.evaluate("""() => {
            const randBtn = document.getElementById('btn-randomize');
            if (randBtn) randBtn.click();

            const hashBefore = window.location.hash;
            const shareBtn = document.getElementById('btn-copy-link');
            if (shareBtn) shareBtn.click();
            const hashAfter = window.location.hash;

            return {
                success: true,
                hasHash: !!hashAfter && hashAfter.includes('#state=')
            };
        }""")
        log_test("Randomize & Share Link Hash Generation", state_result.get("hasHash", False), json.dumps(state_result))

        # Take audit screenshot
        page.screenshot(path="C:/TMP/opencode/audit_screenshot.png", full_page=True)
        my_print("Audit screenshot saved to C:/TMP/opencode/audit_screenshot.png")

        browser.close()

    my_print("\n--- Summary of Audit ---")
    my_print(f"Console Errors ({len(results['console_errors'])}):")
    for err in results["console_errors"]:
        my_print(f"  [ERROR] {err}")
    my_print(f"Console Warnings ({len(results['console_warnings'])}):")
    for warn in results["console_warnings"]:
        my_print(f"  [WARN] {warn}")
    my_print(f"Network Failures ({len(results['network_failures'])}):")
    for fail in results["network_failures"]:
        my_print(f"  [NET_FAIL] {fail}")

    out_f.close()
    return results

if __name__ == "__main__":
    run_audit()
