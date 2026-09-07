# Changelog

## 2026-09-06 — story gaps 4,280 + lyrics 25 + storyrace 1

- story gaps 4,280 (50:3,603, 40:356, 11:228, 80:89, 83:4) via local dat 100% decrypt (17,565 blocks, 13,768 uniques) dual-engine fallback, 42-cols tag-aware ` \n`, both repos identical, UmaTL 04/09 untouched
- lyrics 25 + storyrace 1 (62→62, 34→34) via XOR e + UnityPy/TextAsset CSV, 617 strings, merged both repos
- index now ~25,166 files (blake3, LF, zip_url/zip_dir)

## 2026-09-06 — race jikkyo 1200 + home 938

- race jikkyo: +1,200 (`race_jikkyo_message` 2,171→3,251, `race_jikkyo_comment` 264→384) via 5-worker batch fallback, both repos identical
- home timelines: +938 (`hometimeline` 503→1,441, 9,851 blocks) via local dat extract + 6-worker translate (9,960 strings), wrapped 42 cols tag-aware ` \n`, `no_wrap:true`, both repos identical
- full download audit: `meta` 365,808 unchanged, `dat` 359,906 (+33k, 0 CDN needed), `master.mdb` 44.6MB unchanged, JP columns still only 4
- index now 20,860 files (blake3, LF, zip_url/zip_dir)

## 2026-09-06 — Extra Stories 224 + career wrap fix

- career overflow: re-wrapped 15,893 files (40/50/80/82/83) to 42 cols tag-aware ` \n`, collapsed `     \n` artifacts (max 76→42, p90 41), both repos identical, UmaTL 04/09/10 untouched
- Extra Stories: +224 (Seasonal 19+3 + Story Event 202) via apsw chacha20 meta decrypt (365,808 rows) + Akamai CDN `Windows/assetbundles` (198 CDN + 4 local + 22 seasonal), UmaTL 09:255→457, 10:24→43, 14:0→3
- translate: dual-engine fallback (gemini-3.7-flash-low → deepseek-v4-flash/qwen3.8-flash/deepseek-v4-pro/gemini-3.1-pro-low), 11,357 strings (9,871 new 09), wrapped 42 cols, `no_wrap:true`, CRLF clean
- index now 19,922 files (blake3, LF, zip_url/zip_dir) — Extra Stories now 100% in `Extra Stories` hub (55/55, 11/11, 3/3, 4/4)

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
