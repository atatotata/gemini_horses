# gemini_horses

Whole JP game in English. Works with Hachimi. ~43 MB.

## Install

Drop this in Hachimi's **Translations Meta URL**, pick a flavor, done:
```
https://raw.githubusercontent.com/atatotata/gemini_horses/main/meta.json
```

**Updated and stuff looks weird?** Delete `assets/textures`, `assets/atlas`, `assets/movies`, `assets/an_texture_sets` in `hachimi/localized_data_N` (don't touch `includes_*`), then update. Or just remove + re-add the repo.

**Want the UI pictures too?** One catch: Hachimi runs a single repo at a time, no stacking. Ours has every line; UmaTL has the translated pictures. Grab [`both_tl_repos.json`](https://raw.githubusercontent.com/atatotata/gemini_horses/main/both_tl_repos.json), rename it to `.tl_repos`, toss it in your `hachimi` folder — then flip between them in the repo menu. Each downloads once, switching after is quick.

## Flavors

- **Flagship**: Global text + skill numbers + AI gaps. (94.6k lines, ~54k straight from Global, 21,856 stories.)
- **Community**: old fan wording. (94.5k lines, same 21,856 stories, zero Global.)
- **Lore**: no math, just vibes. (2,167 plain-text skills, everything else same as above.)
- **Full**: Flagship words + translated UI pictures. (~390 MB, slow — modern Hachimi only.)

Thanks: [UmaTL](https://github.com/UmaTL/hachimi-tl-en-sd) · Cygames · us.
