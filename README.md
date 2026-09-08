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

- **Flagship** (`main`): Official Global text + UmaTL textures + SD numbers + Gemini AI for JP-only gaps.
- **Community** (`community`): Classic community romanizations (pre-Global) + SD numbers + AI gaps.
- **Lore** (`lore`): Same 100% coverage, but vanilla anime skill descriptions (no math/formulas).

## Scope at a Glance

- **21,856 stories**: All main scenarios, 14k+ career events, all support cards, and event archives.
- **94.5k master strings** & **33.2k voice lines** across all 158 horses/NPCs.
- **Full Jikkyo & Concerts**: All 3.6k race commentary lines and 62 Winning Live lyrics.
- **Clean Formatting**: 42-col wrap (no box clipping), fixed choice offsets, canonical JRA names.
- **Auto-Sync**: Bi-weekly GitHub Action pulls latest UmaTL human edits over AI text.

## Credits
[UmaTL SD](https://github.com/UmaTL/hachimi-tl-en-sd) (curated TL, UI textures) · Cygames (Global EN text) · Gemini Horses (AI gap fill & pipeline).
