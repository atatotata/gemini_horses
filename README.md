# gemini_horses

100% English patch + Skill Data for Umamusume JP (Steam / DMM / Android). Built for Hachimi.

Every story, career event, support card, live commentary line, and skill formula covered. Zero untranslated gaps.

## Install

Paste into Hachimi's **Translations Meta URL** (First-Time Setup or Repo Settings):
```
https://raw.githubusercontent.com/atatotata/gemini_horses/main/meta.json
```
Pick your flavor and launch.

### Layering (Gap Filler)
Already running another repo? Put this as `id: 2` in `hachimi\.tl_repos` to fill missing stories and unreleased JP content:
```json
{ "id": 2, "index": "https://raw.githubusercontent.com/atatotata/gemini_horses/main/index.json" }
```

## Flavors

- **Flagship** (`main`): Official Global text + UmaTL SD numbers + Gemini AI for JP-only gaps (text-only, no textures — fixes stat numbers, ~38 MB fast install).
- **Community** (`community`): Classic community romanizations (pre-Global) + SD numbers + AI gaps (text-only).
- **Lore** (`lore`): Same 100% text coverage, but vanilla anime skill descriptions (no math/formulas), text-only.

## Scope at a Glance

- **21,856 stories**: All main scenarios, 14k+ career events, all support cards, and event archives.
- **94.5k master strings** & **33.2k voice lines** across all 158 horses/NPCs.
- **Full Jikkyo & Concerts**: All 3.6k race commentary lines and 62 Winning Live lyrics.
- **Clean Formatting**: 42-col wrap (no box clipping), fixed choice offsets, canonical JRA names.
- **Text-only / Fast**: 23,401 JSON, ~38 MB download (no atlases/textures/movies — fixes stat-number sprites, fits Hachimi timeout). Pair with UmaTL repo below if you want UI textures.
- **Auto-Sync**: Bi-weekly GitHub Action pulls latest UmaTL human edits over AI text.

## Credits
[UmaTL SD](https://github.com/UmaTL/hachimi-tl-en-sd) (SD numbers, curated TL) · Cygames (Global EN text) · Gemini Horses (AI gap fill & pipeline).
