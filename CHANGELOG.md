# Changelog

## 2026-09-10 — Dialogue Font Restored
- **Font is back**: restored UmaTL's `RodinWanpakuPro` font bundles (`includes_win`/`android`, 3.6 MB). The text-only strip had dropped them, reverting all text to the stock game font. Arrives as a small incremental update — no wipe needed.
- **Sync-safe**: indexers now keep exactly these two non-JSON files; everything else stays text-only.

## 2026-09-10 — Text-Only Fast Install
- **Media stripped**: removed textures/atlases/movies + `includes_*` from git tree (25,166 → 23,401 JSON-only, ~38 MB). Fixes stat-number sprites overwritten by atlases and fits Hachimi download timeout.
- **Release zips untracked**: `releases/*.zip` now ship as GitHub Release assets only (gitignored), so branch zips stay ~13 MB.
- **Docs**: README flavors + Scope + Credits and `meta.json` Flagship blurb now say text-only; pair with UmaTL repo below for UI textures.

## 2026-09-07 — Lore Edition & Official Global Polish
- **Skill Data Priority**: Prioritized numerical Skill Data (SD) over Global narrative descriptions (`SD > Global > UmaTL > Gemini` for skill effects), ensuring exact speeds, accelerations, and trigger conditions display on Flagship & Community editions.
- **Lore Edition**: Added a formula-free flavor for folks who want pure story text and no math in skill boxes.
- **Global Official Text**: Dropped in 54k official Global lines over machine translations; kept all JP-exclusive content safe.
- **Multi-Flavor Menu**: Hachimi's repo menu now shows Flagship, Community, and Lore in one clean list.
- **Final Audit**: Cleaned up 104 remaining master lines and fixed zero-padded filenames.

## 2026-09-06 — 100% Story & Media Sweep
- **All Stories Covered**: Translated the last 4.2k story cutscenes. Every story in the game is now in English!
- **Home & Race Banter**: Added 938 home lobby chats, 1.2k race callouts, and 25 concert lyrics.
- **Text Wrap Fix**: Re-wrapped career dialogue at 42 columns so lines never clip off the edge of log boxes.

## 2026-09-05 — Career Stories & Alignment Fix
- **Career Mega-Drop**: Translated 14,136 career events and 395 support card stories.
- **Choice Alignment**: Fixed the dummy block offset so choices hook onto the right dialogue lines.
- **Name Cleanup**: Standardized names against official JRA records (Efforia, Curren Chan, Rhein Kraft).

## 2026-09-03 — Launch Day
- **Day One Sprint**: Built the full pipeline from scratch with 94k master strings, full voice lines, textures, and Android/PC support.
