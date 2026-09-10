# gemini_horses

Full English patch for the JP game, made for Hachimi. All stories, career events, voices, and skills — ~43 MB, no bloat.

## Getting it running

Paste this into Hachimi's **Translations Meta URL** and pick a flavor:
```
https://raw.githubusercontent.com/atatotata/gemini_horses/main/meta.json
```

**Been here before?** One-time cleanup: Hachimi never deletes old files, so either remove + re-add the repo, or delete `assets/textures`, `assets/atlas`, `assets/movies`, `assets/an_texture_sets` in `hachimi/localized_data_N` (leave `includes_*` alone, that's the font). Old leftovers break stat numbers.

**Want the pretty UI pictures too?** Grab [`layered_tl_repos.json`](https://raw.githubusercontent.com/atatotata/gemini_horses/main/layered_tl_repos.json), rename it to `.tl_repos`, drop it in your `hachimi` folder. (Fresh setups only — it replaces whatever repos you had.)

## Flavors

- **Flagship**: official Global text + skill numbers + AI filling the gaps.
- **Community**: the classic fan wording from before Global.
- **Lore**: same stories, plain skill text with no math.

21,856 stories · 94.5k lines · 33.2k voice clips · race calls · lyrics. Synced with UmaTL twice a week.

Thanks: [UmaTL](https://github.com/UmaTL/hachimi-tl-en-sd) · Cygames · Gemini Horses.
