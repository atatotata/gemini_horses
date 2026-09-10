# gemini_horses

100% English text patch for Umamusume JP (Steam / DMM / Android), built for Hachimi. Every story, career event, voice line, and skill covered — text-only + dialogue font, ~43 MB.

## Install

Paste into Hachimi's **Translations Meta URL** and pick a flavor:
```
https://raw.githubusercontent.com/atatotata/gemini_horses/main/meta.json
```

**Updating from an old version?** This repo is now text-only, and Hachimi never deletes stale files — so once: remove and re-add the repo, *or* delete `assets/textures`, `assets/atlas`, `assets/movies`, `assets/an_texture_sets` in `hachimi/localized_data_N` (keep `includes_*` — that's the dialogue font), then update. (Leftover atlases break stat numbers.)

**Want UI textures?** Layer UmaTL underneath (higher `id` wins):
```json
{ "id": 1, "index": "https://raw.githubusercontent.com/UmaTL/hachimi-tl-en-sd/release/index.json" },
{ "id": 2, "index": "https://raw.githubusercontent.com/atatotata/gemini_horses/main/index.json" }
```

## Flavors

- **Flagship** (`main`): Official Global text + SD numbers + AI gap fill.
- **Community** (`community`): Classic pre-Global romanizations + SD numbers.
- **Lore** (`lore`): Same coverage, vanilla skill text (no formulas).

## Scope

- **21,856 stories** · **94.5k master strings** · **33.2k voice lines** · 3.6k race calls · 62 lyrics.
- 42-col wrap, canonical JRA names, bi-weekly UmaTL sync.

## Credits
[UmaTL SD](https://github.com/UmaTL/hachimi-tl-en-sd) · Cygames (Global EN) · Gemini Horses (AI gap fill).
