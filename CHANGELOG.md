# Changelog

All on 2026-09-03 — repo went from zero to done in one day.

### Latest
- **b2c01ea** — renamed to `Gemini Horses (UmaTL + Gemini mTL + Skill Data)` + made description actually readable
- **a551f97** — `Otattemita` → `atatotata` everywhere (code, URLs, metadata)
- **0c65109 / 9ee7e16** — fixed hash mismatches (CRLF vs LF). Enforced LF, rehashed index. Downloads work now on all platforms.

### Android & fresh installs
- **4ddd7c0** — added `zip_url`/`zip_dir` so Android/fresh clones pull the full pack
- **6605c23** — added `meta.json` so repo shows up in Hachimi's first-time setup

### Content
- **890ed7c** — bundled 1,765 UmaTL media files (~420 MB textures + movie) so new users get everything, not just JSON

### Sync & docs
- **d3f8de8** — upstream UmaTL sync script + auto GitHub Action (twice weekly, Mon/Thu) + proper BLAKE3 index
- **cd0a548** — bumped sync to twice a week
- **0d00fdd / ab0838e / b6df3be / a8fed63 / 9245687 / a031b41 / 36345c1** — docs churn: readme, usage, `meta.json` vs `index.json` explanation, and UmaTL attribution

### Initial
- **c759723** — first commit. Full MT coverage: 94k strings, 1,160 support stories, 158 voice sets + skill numbers.
