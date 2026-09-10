# gemini_horses

Whole JP game in English. Works with Hachimi. ~43 MB.

## Install

Drop this in Hachimi's **Translations Meta URL**, pick a flavor, done:
```
https://raw.githubusercontent.com/atatotata/gemini_horses/main/meta.json
```

**Updated and stuff looks weird?** Delete `assets/textures`, `assets/atlas`, `assets/movies`, `assets/an_texture_sets` in `hachimi/localized_data_N` (don't touch `includes_*`), then update. Or just remove + re-add the repo.

**Want the UI pictures too?** Download [`layered_tl_repos.json`](https://raw.githubusercontent.com/atatotata/gemini_horses/main/layered_tl_repos.json), rename to `.tl_repos`, toss it in your `hachimi` folder.

## Flavors

- **Flagship**: Global text + skill numbers + AI gaps. (94.6k lines, ~54k straight from Global, 21,856 stories.)
- **Community**: old fan wording. (94.5k lines, same 21,856 stories, zero Global.)
- **Lore**: no math, just vibes. (2,167 plain-text skills, everything else same as above.)

Thanks: [UmaTL](https://github.com/UmaTL/hachimi-tl-en-sd) · Cygames · us.
