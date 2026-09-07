# gemini_horses

Complete English translation patch and skill overlay for Umamusume: Pretty Derby (JP / DMM / Steam / Android). Built for Hachimi.

## Flavors

Pick what fits your playstyle:
- **Flagship (Default)**: Official Global EN + UmaTL curated + Gemini gap-fill + numeric Skill Data.
- **Community Edition**: Pure community naming & translations + numeric Skill Data.
- **Lore Edition**: Pure narrative anime experience — standard story skill descriptions with zero math formulas.

## Quick Install

In Hachimi's First-Time Setup, paste this into the **Translations Meta URL**:
```
https://raw.githubusercontent.com/atatotata/gemini_horses/main/meta.json
```
Pick your preferred flavor from the menu, and you're good to go!

### Use as a Gap Filler
If you already use another translation repo and just want Gemini Horses to fill in missing dialogue/stories, add this to `hachimi\.tl_repos` (higher ID wins):
```json
{ "id": 2, "index": "https://raw.githubusercontent.com/atatotata/gemini_horses/main/index.json" }
```

## What's Inside

- **100% Master Text**: 94,550 UI, skill, item, and character strings across 373 categories.
- **100% Story Cutscenes**: 21,856 stories (main scenario, horsegirl careers, support cards, and event archives).
- **100% Voice Lines**: 33,287 character system lines across all 158 playable horses and NPCs.
- **100% Home Lobby**: 1,441 home screen conversations and idle chats.
- **100% Live Race Commentary**: 3,635 race announcements, fanfares, and color commentary.
- **Concert Lyrics**: 62 Winning Live song lyrics.
- **UI & Graphics**: ~420 MB of translated menus, textures, fonts, and banners.

## How Updates Work

Twice a week, GitHub Actions pulls fresh human-translated text from [UmaTL SD](https://github.com/UmaTL/hachimi-tl-en-sd). Human translations gracefully replace machine-translated lines while keeping 100% gap coverage for everything else.

## Credits

- **Curated Translations & Textures**: [UmaTL SD](https://github.com/UmaTL/hachimi-tl-en-sd) (noccu and contributors).
- **Official English Lines**: Cygames Global localization.
- **Gap Coverage & Machine Translation**: Gemini Horses project.
