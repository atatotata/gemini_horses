# Changelog

## 2026-09-11 — Fresh Translations
- **161 new UI strings** across title legal notices, trainer abilities, plan sheets, Android dumps, and Factor Research menus.

## 2026-09-11 — Fit Fixes
- **Shortened a dozen overflowing labels** (Delete, Visible, P2, Target…) and the Plan Sheet button, all pinned. Rewrapped one home dialogue line for narrow balloons. Two audit rounds standardized terms (sparks, Umamusume) and trimmed the rest.

## 2026-09-11 — Training Plan + Skill Set Menus
- **128 new UI strings** translated (TrainingRoadmap/SkillSet TextId keys captured via translator_mode dump, deepseek-v4.1-flash). Master-sourced menu text was already covered — update in-game and both menus flip to EN.

## 2026-09-11 — v6 Release Zips
- Fresh plug-and-play zips (Flagship/Community/Lore/Full-slim) with everything through the Phalaenopsis update. Primed caches re-verified zero-diffs.

## 2026-09-11 — New Horse Phalaenopsis (1149)
- **116 new stories + 6 home lines** translated (her character story, event 41149, career 82/83, misc). Stories via gemini-3.8-flash-tiered, home lines via deepseek-v4.1-flash. +608 master strings from the same update.

## 2026-09-10 — Full Goes Entire
- **Full is now the whole package**: +77 atlas files (WITH upstream `.json` manifests — the old pack lacked them, likely the stat-bug cause) + the story movie. 25,204 files, ~435 MB. If your training stat numbers look off, say so and atlases come back out.

## 2026-09-10 — Racecourse Card Fix
- **Short track names**: "Sapporo Racecourse" overflowed its card ("Sapporo Racecours"). Cards + live lists now read "Sapporo RC", "Nakayama RC"… Pinned so syncs can't revert. Story prose untouched.

## 2026-09-10 — Hash Mismatch Fix
- **Fixed "File hash mismatch" on update**: `info.json` was hashed as CRLF but stored as LF (Windows text-mode writes). Rewrote LF-only, re-indexed, and hardened all script writes with `newline="\n"`. Full audit: 0 mismatches in 119,549 files across all 5 branches. Just hit Check for Updates again — nothing is broken on your end.

## 2026-09-10 — Renamed to hachimi-tl-gemini-horses
- Repo renamed (`gemini_horses` -> `hachimi-tl-gemini-horses`); all index/meta/docs URLs updated. Expect ONE full re-download after this (new URLs = new repo identity to Hachimi). Old links redirect.

## 2026-09-10 — Plug-and-Play Release Zips
- **v5 zips** (Flagship/Community/Lore/Full-slim) ship a primed `.tl_repo_cache` — manual installs no longer trigger a full re-download. Follow INSTALL.txt in the zip. Built by `package_release.py`, verified zero-diffs.

## 2026-09-10 — Full Slim Flavor
- **New `full-slim` branch**: Flagship text + 214 everyday UI pictures (23,617 files, ~60 MB). Skips race cards, gacha plates & comics. Same `.full_media` allowlist mechanism, same sync.

## 2026-09-10 — Full Flavor (Text + Pictures)
- **New `full` branch**: Flagship text + 1,723 translated UI pictures (25,126 files, ~390 MB). No sprite atlases (stats stay fixed), no movies. Needs modern Hachimi — old 15s-timeout builds can't fetch it.
- Kept fresh by the same UmaTL sync (`.full_media` sentinel); text branches stay lean and untouched.

## 2026-09-10 — Repos Don't Stack
- **One active repo**: Hachimi loads only the selected repo — entries never layer. Docs fixed (they wrongly said otherwise). Use `both_tl_repos.json` to keep ours + UmaTL in the switcher and flip between them.

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
