# Changelog

## 2026-09-05 — 14k career stories + fallback hardening

- timeline shift fix: stripped dummy block 0 across 1,483 files (choices now land correctly, Epiphaneia screenshot fixed)
- canonical names: standardized 13 names (Efforia not Euphoria, Curren Chan, Rhein Kraft, etc.) in voice bible, text_data cat6, and 216 stories
- support card career events: +395 missing (gallery_flag=2, Efforia 801146xxx) — 484k-string scan
- horsegirl career events: +14,136 (gallery_flag=1+3, Horsegirls + Main Scenario) via 8-worker extract (14.2s, 483,516 blocks) + dual-engine translate (gemini-3.7-flash-low primary with fallback cascade deepseek-v4-flash/qwen3.8-flash/deepseek-v4-pro/gemini-3.1-pro-low)
- index now 19,698 files (blake3, LF, zip_url/zip_dir)
- tools consolidated under gemini_horses/tools/

## 2026-09-03 — zero to done in one day

- 21:43 — renamed to `Gemini Horses (UmaTL + Gemini mTL + Skill Data)` + made description readable
- 21:16 — `Otattemita` → `atatotata` everywhere (URLs, code, metadata)
- 21:01 / 20:59 — fixed hash mismatches (CRLF → LF), rehashed index — downloads work now on all platforms
- 20:41 — condensed usage instructions
- 20:40 — documented `meta.json` vs `index.json` layering flows
- 20:35 — added `meta.json` so repo shows up in Hachimi first-time setup
- 20:08 — added `zip_url`/`zip_dir` so Android / fresh clones pull the full pack
- 19:54 — added UmaTL attribution
- 19:49 — pointed UmaTL linkback to `hachimi-tl-en`
- 19:43 — bundled 1,765 UmaTL media files (~420 MB) so new users get everything, not just JSON
- 19:29 — highlighted graceful UmaTL overlay (keeps MT where human TL missing)
- 19:22 — tweaked description from "English" to "machine translation"
- 19:17 — streamlined README
- 19:02 — bumped sync to twice weekly (Mon/Thu)
- 18:11 — added UmaTL sync script + GitHub Action + proper BLAKE3 index
- 17:54 — initial commit: 94k strings, 1,160 support stories, 158 voice sets + skill numbers
