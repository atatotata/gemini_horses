# gemini_horses

Whole JP game in English. Works with Hachimi. ~43 MB.

## Install

Drop this in Hachimi's **Translations Meta URL**, pick a flavor, done:
```
https://raw.githubusercontent.com/atatotata/gemini_horses/main/meta.json
```

**Updated and stuff looks weird?** Delete `assets/textures`, `assets/atlas`, `assets/movies`, `assets/an_texture_sets` in `hachimi/localized_data_N` (don't touch `includes_*`), then update. Or just remove + re-add the repo.

**Want the UI pictures too?** Pick **Full** (~390 MB, everything) or **Full-slim** (~60 MB, just the daily UI) from the menu. Hachimi runs one repo at a time — to also keep UmaTL around for flipping, grab [`both_tl_repos.json`](https://raw.githubusercontent.com/atatotata/gemini_horses/main/both_tl_repos.json), rename to `.tl_repos`, toss it in `hachimi`.

**Downloads crawling or old Hachimi?** Grab a [v5 zip](https://github.com/atatotata/gemini_horses/releases/tag/text-v5) (cache included, zero re-download) and follow the INSTALL.txt inside.

## Flavors

- **Flagship**: Global text + skill numbers + AI gaps. (94.6k lines, ~54k straight from Global, 21,856 stories.)
- **Community**: old fan wording. (94.5k lines, same 21,856 stories, zero Global.)
- **Lore**: no math, just vibes. (2,167 plain-text skills, everything else same as above. On Hachimi 0.30.0+, the `skill_data_desc` switch brings the numbers back if you miss them.)
- **Full**: Flagship words + translated UI pictures. (~390 MB, slow — modern Hachimi only.)
- **Full-slim**: words + daily UI pictures, none of the bloat. (~60 MB.)

Thanks: [UmaTL](https://github.com/UmaTL/hachimi-tl-en-sd) · Cygames · us.
