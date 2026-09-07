import json
import traceback
from playwright.sync_api import sync_playwright

with open("C:/TMP/opencode/audit_comprehensive.log", "w", encoding="utf-8") as out:
    def log(*args):
        line = " ".join(str(a) for a in args)
        out.write(line + "\n")
        out.flush()
        print(line)

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        page = browser.new_page(viewport={"width": 1440, "height": 900})

        console_errors = []
        page.on("console", lambda msg: console_errors.append(f"[{msg.type}] {msg.text}") if msg.type in ["error", "warning"] else None)
        page.on("pageerror", lambda exc: console_errors.append(f"[PAGE_ERR] {exc}"))

        page.goto("http://localhost:8000/editor.html", wait_until="networkidle")

        # Test A: Stage toggles above stage in Remix mode
        log("=== TEST A: Stage Layer Toggles (Base, Eyes, Mouth, Accessories) ===")
        res_a = page.evaluate("""() => {
            const baseToggle = document.getElementById('layer-base-toggle');
            const eyesToggle = document.getElementById('layer-eyes-toggle');
            const mouthToggle = document.getElementById('layer-mouth-toggle');
            const accToggle = document.getElementById('layer-accessories-toggle');

            const canvas = document.getElementById('stage-canvas');
            
            // Toggle eyes off
            eyesToggle.click();
            const eyesHidden = eyesToggle.classList.contains('inactive');
            const svgAfterEyesOff = canvas.innerHTML;

            // Toggle eyes on
            eyesToggle.click();
            const eyesBackOn = !eyesToggle.classList.contains('inactive');

            return {
                baseToggleExists: !!baseToggle,
                eyesHidden,
                eyesBackOn,
                svgLen: svgAfterEyesOff.length
            };
        }""")
        log("Result A:", json.dumps(res_a))

        # Test B: Accessories in Remix mode
        log("\n=== TEST B: Accessories Toggle and Render ===")
        res_b = page.evaluate("""() => {
            const blushInput = document.querySelector('#accessory-toggles input[data-accessory="blush"]');
            const glassesInput = document.querySelector('#accessory-toggles input[data-accessory="glasses"]');
            
            if (!blushInput || !glassesInput) return { error: 'Accessory inputs not found' };

            blushInput.checked = true;
            blushInput.dispatchEvent(new Event('change', { bubbles: true }));

            const canvas = document.getElementById('stage-canvas');
            const hasBlushSvg = canvas.innerHTML.includes('layer-') && canvas.innerHTML.includes('blush');

            glassesInput.checked = true;
            glassesInput.dispatchEvent(new Event('change', { bubbles: true }));
            const hasGlassesSvg = canvas.innerHTML.includes('glasses');

            return {
                blushChecked: blushInput.checked,
                hasBlushSvg,
                hasGlassesSvg,
                canvasHtmlSnippet: canvas.innerHTML.substring(0, 300)
            };
        }""")
        log("Result B:", json.dumps(res_b))

        # Test C: Scratch Builder Search & Add Part
        log("\n=== TEST C: Scratch Builder Search & Part Addition ===")
        res_c = page.evaluate("""() => {
            document.getElementById('tab-mode-scratch')?.click();
            
            // Search 'halo'
            const search = document.getElementById('scratch-part-search');
            search.value = 'halo';
            search.dispatchEvent(new Event('input', { bubbles: true }));

            const partsGrid = document.getElementById('scratch-parts-grid');
            const visibleParts = Array.from(partsGrid.querySelectorAll('.scratch-part-card')).map(c => c.querySelector('.scratch-part-name')?.textContent);

            // Click the searched part
            const firstCard = partsGrid.querySelector('.scratch-part-card');
            if (firstCard) firstCard.click();

            // Check if layer was added
            const layerBadge = document.getElementById('layer-count-badge')?.textContent;

            // Reset search
            search.value = '';
            search.dispatchEvent(new Event('input', { bubbles: true }));

            return {
                searchedFor: 'halo',
                visibleParts,
                layerBadgeAfterAdd: layerBadge
            };
        }""")
        log("Result C:", json.dumps(res_c))

        # Test D: Direct Tab switch from Remix to Layers mode
        log("\n=== TEST D: Tab switch from Remix directly to Layers mode ===")
        # Reload page fresh
        page.goto("http://localhost:8000/editor.html", wait_until="networkidle")
        res_d = page.evaluate("""() => {
            // Select Rin
            const rinCard = document.querySelector('.char-select-card[data-char="rin"]');
            if (rinCard) rinCard.click();

            // Directly click Layers tab WITHOUT clicking Decompose first
            const layersTab = document.getElementById('tab-mode-layers');
            layersTab.click();

            const items = document.querySelectorAll('.layer-item');
            const emptyState = document.querySelector('.layer-empty-state');

            return {
                charSelected: 'rin',
                layerItemsCount: items.length,
                hasEmptyState: !!emptyState
            };
        }""")
        log("Result D:", json.dumps(res_d))

        # Test E: Layer Property Controls (Name, Blend, Opacity, Position X/Y, Scale, Color pickers)
        log("\n=== TEST E: Layer Properties Editing in Layers Mode ===")
        res_e = page.evaluate("""() => {
            // Decompose Rin
            document.getElementById('tab-mode-remix')?.click();
            document.getElementById('btn-decompose-remix')?.click();

            const items = document.querySelectorAll('.layer-item');
            if (items.length === 0) return { error: 'No layer items after decompose' };

            // Select base layer (bottom of visual stack = last in items)
            const baseItem = items[items.length - 1];
            baseItem.click();

            const nameInput = document.getElementById('layer-prop-name');
            const blendSelect = document.getElementById('layer-prop-blend');
            const opacitySlider = document.getElementById('layer-prop-opacity');
            const posX = document.getElementById('layer-prop-x');
            const posY = document.getElementById('layer-prop-y');
            const scale = document.getElementById('layer-prop-scale');
            const colorSlots = document.querySelectorAll('#layer-color-slots .color-slot');

            // Change name
            nameInput.value = 'Rin Custom Base';
            nameInput.dispatchEvent(new Event('input', { bubbles: true }));

            // Change opacity to 80%
            opacitySlider.value = 80;
            opacitySlider.dispatchEvent(new Event('input', { bubbles: true }));

            // Change pos X to 1
            posX.value = 1;
            posX.dispatchEvent(new Event('input', { bubbles: true }));

            // Change scale to 120%
            scale.value = 120;
            scale.dispatchEvent(new Event('input', { bubbles: true }));

            const canvas = document.getElementById('stage-canvas');
            const svgContent = canvas.innerHTML;

            return {
                nameUpdatedInItem: baseItem.querySelector('.layer-name')?.textContent,
                colorSlotsInProps: colorSlots.length,
                svgHasOpacity: svgContent.includes('opacity="0.8"') || svgContent.includes('opacity: 0.8'),
                svgHasTransform: svgContent.includes('translate') || svgContent.includes('scale')
            };
        }""")
        log("Result E:", json.dumps(res_e))

        # Test F: Export Modal for all 5 formats
        log("\n=== TEST F: Export Modal Formats ===")
        res_f = page.evaluate("""() => {
            const formatSelect = document.getElementById('export-format');
            const exportBtn = document.getElementById('btn-export');
            const modal = document.getElementById('export-modal');
            const modalTitle = document.getElementById('modal-title');
            const fileInfo = document.getElementById('modal-file-info');
            const copyBtn = document.getElementById('btn-copy-svg');
            const downloadBtn = document.getElementById('btn-download-file');

            const formats = ['svg-layered', 'svg-flattened', 'png-512', 'png-1024', 'variant-sheet'];
            const formatResults = {};

            formats.forEach(fmt => {
                formatSelect.value = fmt;
                formatSelect.dispatchEvent(new Event('change', { bubbles: true }));
                exportBtn.click();

                formatResults[fmt] = {
                    modalActive: modal.classList.contains('active'),
                    fileInfoText: fileInfo?.textContent,
                    copyBtnVisible: copyBtn ? getComputedStyle(copyBtn).display !== 'none' : false,
                    downloadBtnExists: !!downloadBtn
                };

                // Close modal
                document.getElementById('modal-close-btn')?.click();
            });

            return formatResults;
        }""")
        log("Result F:", json.dumps(res_f, indent=2))

        # Test G: Save Preset, Load Preset & Hash Share URL
        log("\n=== TEST G: Presets & Share URL Hash ===")
        res_g = page.evaluate("""() => {
            // Test hash copy
            const copyLinkBtn = document.getElementById('btn-copy-link');
            copyLinkBtn.click();
            const hash = window.location.hash;

            // Test randomize
            const randBtn = document.getElementById('btn-randomize');
            const activeCardBefore = document.querySelector('.char-select-card.selected')?.dataset.char;
            randBtn.click();
            const activeCardAfter = document.querySelector('.char-select-card.selected')?.dataset.char;

            return {
                hashGenerated: hash.startsWith('#state='),
                hashLen: hash.length,
                randCardBefore: activeCardBefore,
                randCardAfter: activeCardAfter
            };
        }""")
        log("Result G:", json.dumps(res_g))

        # Test H: Check Console Messages
        log("\n=== CONSOLE LOGS & ERRORS ===")
        log(f"Errors count: {len(console_errors)}")
        for err in console_errors:
            log("  [ERR]", err)

        browser.close()
