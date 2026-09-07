import json
import traceback
from playwright.sync_api import sync_playwright

with open("C:/TMP/opencode/audit_deep_dive.log", "w", encoding="utf-8") as out:
    def log(*args):
        line = " ".join(str(a) for a in args)
        out.write(line + "\n")
        out.flush()

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        page = browser.new_page(viewport={"width": 1440, "height": 900})

        console_logs = []
        page.on("console", lambda msg: console_logs.append(f"[{msg.type}] {msg.text}"))
        page.on("pageerror", lambda exc: console_logs.append(f"[UNCAUGHT] {exc}"))

        page.goto("http://localhost:8000/editor.html", wait_until="networkidle")

        # 1. Inspect Export Flow
        log("\n--- 1. AUDIT: Export Flow ---")
        export_check = page.evaluate("""() => {
            try {
                const btn = document.getElementById('btn-export');
                btn.click();
                const codeBox = document.getElementById('export-code-box');
                const modal = document.getElementById('export-modal');
                const svgPreview = document.getElementById('export-svg-preview');
                const stats = document.getElementById('export-stats');
                
                return {
                    modalActive: modal ? modal.classList.contains('active') : false,
                    codeBoxExists: !!codeBox,
                    codeBoxVal: codeBox ? codeBox.value : null,
                    codeBoxLength: codeBox ? codeBox.value.length : 0,
                    svgPreviewHasChild: svgPreview ? svgPreview.children.length : 0,
                    statsText: stats ? stats.textContent : null
                };
            } catch(e) {
                return { error: e.toString() };
            }
        }""")
        log("Export check:", json.dumps(export_check, indent=2))

        # 2. Inspect Layers in Remix vs Decompose
        log("\n--- 2. AUDIT: Remix to Layers Decompose ---")
        decomp_check = page.evaluate("""() => {
            try {
                // Close export modal
                document.getElementById('btn-close-modal')?.click();

                // Click decompose button
                const decompBtn = document.getElementById('btn-decompose-remix');
                if (!decompBtn) return { error: 'btn-decompose-remix missing' };
                decompBtn.click();

                const layersTab = document.getElementById('tab-mode-layers');
                const layersList = document.getElementById('layer-stack-list');
                const layerItems = document.querySelectorAll('.layer-item');
                
                return {
                    layersTabActive: layersTab ? layersTab.classList.contains('active') : false,
                    layersCount: layerItems.length,
                    layerNames: Array.from(layerItems).map(el => el.querySelector('.layer-name')?.textContent)
                };
            } catch(e) {
                return { error: e.toString() };
            }
        }""")
        log("Decompose check:", json.dumps(decomp_check, indent=2))

        # 3. Inspect Scratch Builder
        log("\n--- 3. AUDIT: Scratch Builder ---")
        scratch_check = page.evaluate("""() => {
            try {
                const scratchTab = document.getElementById('tab-mode-scratch');
                scratchTab.click();

                // Click an anime template: 'Idol'
                const idolBtn = Array.from(document.querySelectorAll('.scratch-template-btn')).find(b => b.textContent.includes('Idol'));
                if (!idolBtn) return { error: 'Idol button not found' };
                idolBtn.click();

                const canvas = document.getElementById('stage-canvas');
                const svg = canvas ? canvas.querySelector('svg') : null;
                const layersBadge = document.getElementById('layer-count-badge')?.textContent;

                // Check category tab switching
                const catTabs = Array.from(document.querySelectorAll('.scratch-cat-tab'));
                const catNames = catTabs.map(t => t.dataset.category);
                
                // Click 'outfit' category
                const outfitTab = catTabs.find(t => t.dataset.category === 'outfit');
                if (outfitTab) outfitTab.click();

                const parts = Array.from(document.querySelectorAll('.scratch-part-card')).map(p => ({
                    id: p.dataset.partId,
                    name: p.querySelector('.scratch-part-name')?.textContent
                }));

                return {
                    svgRendered: !!svg,
                    svgContentLen: svg ? svg.innerHTML.length : 0,
                    layersBadge,
                    catNames,
                    outfitPartsCount: parts.length,
                    outfitParts: parts
                };
            } catch(e) {
                return { error: e.toString() };
            }
        }""")
        log("Scratch check:", json.dumps(scratch_check, indent=2))

        # 4. Inspect Layer Controls in Layers Mode
        log("\n--- 4. AUDIT: Layer Controls in Layers Mode ---")
        layer_controls_check = page.evaluate("""() => {
            try {
                const layersTab = document.getElementById('tab-mode-layers');
                layersTab.click();

                const items = document.querySelectorAll('.layer-item');
                if (items.length === 0) return { error: 'No layers in stack' };

                // Select first layer
                items[0].click();

                const nameInput = document.getElementById('layer-prop-name');
                const blendSelect = document.getElementById('layer-prop-blend');
                const opacitySlider = document.getElementById('layer-prop-opacity');
                const colorSlots = document.querySelectorAll('#layer-color-slots .color-slot-row');

                // Test changing opacity
                if (opacitySlider) {
                    opacitySlider.value = 50;
                    opacitySlider.dispatchEvent(new Event('input', { bubbles: true }));
                }

                // Test toggling visibility
                const visBtn = items[0].querySelector('.layer-vis-btn');
                const visBefore = visBtn ? visBtn.textContent : null;
                if (visBtn) visBtn.click();
                const visAfter = visBtn ? visBtn.textContent : null;

                // Test moving layer down
                const downBtn = items[0].querySelector('.layer-move-down');
                const hadDownBtn = !!downBtn;
                if (downBtn) downBtn.click();

                return {
                    layerCount: items.length,
                    selectedName: nameInput ? nameInput.value : null,
                    blendVal: blendSelect ? blendSelect.value : null,
                    opacityVal: opacitySlider ? opacitySlider.value : null,
                    colorSlotsCount: colorSlots.length,
                    visToggleWorked: visBefore !== visAfter,
                    hadDownBtn
                };
            } catch(e) {
                return { error: e.toString() };
            }
        }""")
        log("Layer controls check:", json.dumps(layer_controls_check, indent=2))

        # 5. Inspect Add Layer Modal
        log("\n--- 5. AUDIT: Add Layer Modal ---")
        add_modal_check = page.evaluate("""() => {
            try {
                const addBtn = document.getElementById('btn-add-layer');
                if (!addBtn) return { error: 'btn-add-layer not found' };
                addBtn.click();

                const modal = document.getElementById('add-layer-modal');
                const isActive = modal ? modal.classList.contains('active') : false;
                const partsInModal = document.querySelectorAll('#add-layer-parts-grid .scratch-part-card');

                // Click a part inside the modal to add it
                let addedPartId = null;
                if (partsInModal.length > 0) {
                    addedPartId = partsInModal[0].dataset.partId;
                    partsInModal[0].click();
                }

                const modalActiveAfterAdd = modal.classList.contains('active');
                const newLayerCount = document.querySelectorAll('.layer-item').length;

                return {
                    modalOpened: isActive,
                    partsCount: partsInModal.length,
                    addedPartId,
                    modalClosedAfterAdd: !modalActiveAfterAdd,
                    newLayerCount
                };
            } catch(e) {
                return { error: e.toString() };
            }
        }""")
        log("Add modal check:", json.dumps(add_modal_check, indent=2))

        # 6. Inspect Color Override on Remix
        log("\n--- 6. AUDIT: Color overrides on Remix ---")
        color_check = page.evaluate("""() => {
            try {
                // Switch to Remix
                document.getElementById('tab-mode-remix')?.click();
                
                // Select Rin (has clear colors)
                const rinCard = document.querySelector('.char-select-card[data-char="rin"]');
                if (rinCard) rinCard.click();

                const colorInputs = document.querySelectorAll('.color-slot-input');
                const beforeVal = colorInputs.length > 0 ? colorInputs[0].value : null;

                if (colorInputs.length > 0) {
                    colorInputs[0].value = '#123456';
                    colorInputs[0].dispatchEvent(new Event('input', { bubbles: true }));
                    colorInputs[0].dispatchEvent(new Event('change', { bubbles: true }));
                }

                const canvas = document.getElementById('stage-canvas');
                const svgHtml = canvas ? canvas.innerHTML : '';
                const colorReflectedInSvg = svgHtml.includes('#123456') || svgHtml.includes('#123456'.toLowerCase());

                return {
                    colorSlotsCount: colorInputs.length,
                    beforeVal,
                    changedTo: '#123456',
                    colorReflectedInSvg
                };
            } catch(e) {
                return { error: e.toString() };
            }
        }""")
        log("Color override check:", json.dumps(color_check, indent=2))

        # 7. Check All Captured Console Messages
        log("\n--- Captured Console Logs & Errors ---")
        for l in console_logs:
            log(" ", l)

        browser.close()
