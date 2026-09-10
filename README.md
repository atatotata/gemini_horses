# gemini_horses

100% English patch + Skill Data for Umamusume JP (Steam / DMM / Android). Built for Hachimi.

Every story, career event, support card, live commentary line, and skill formula covered. Zero untranslated gaps.

## Install

### New users
Paste into Hachimi's **Translations Meta URL** (First-Time Setup or Repo Settings):
```
https://raw.githubusercontent.com/atatotata/gemini_horses/main/meta.json
```
Pick your flavor and launch. First download is a single ~40 MB zip (~23k text files, a few seconds) — no 500 MB media pack, no per-file rate-limit 403s.

### Existing users (one-time cleanup)
This repo is now **text-only**. Hachimi never deletes stale files on a normal update, so your old textures/atlases stay on disk — and the old atlases keep breaking stat numbers. Do **one** of these once:
1. Easiest: remove this repo in Hachimi settings and re-add it (a repo change wipes the folder and pulls a fresh ~40 MB zip), **or**
2. Delete `assets/textures`, `assets/atlas`, `assets/movies`, `assets/an_texture_sets` plus `includes_android` / `includes_win` inside your `hachimi/localized_data_N` folder, then Check for Updates.

After that, updates go back to small incrementals. (Switching flavors also wipes + re-downloads the ~40 MB zip, since each flavor is a separate repo URL.)

### Want UI textures too? (optional)
This repo ships text only. To get translated UI textures, layer an UmaTL repo **below** this one — higher `id` wins, so keep this repo on top and UmaTL's textures fill the gaps with zero conflicts:
```json
{ "id": 1, "index": "https://raw.githubusercontent.com/UmaTL/hachimi-tl-en-sd/release/index.json" },
{ "id": 2, "index": "https://raw.githubusercontent.com/atatotata/gemini_horses/main/index.json" }
```

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
