# gemini_horses

Full machine translation patch and numerical skill data overlay for Umamusume: Pretty Derby (DMM/Steam). Compatible with Hachimi.

## Contents
- **Master Data**: 94,550 localized UI, skill, character, and item strings across 373 categories.
- **Skill Data (SD)**: In-line numerical stats, speeds, and triggers.
- **Voice Lines**: 33,287 voice lines across all 158 characters (100% full master coverage).
- **Stories**: 21,856 translated story cutscenes (100% coverage across main scenario, character stories, career events, support cards, and seasonal extras).
- **Home Screen**: 1,441 translated home lobby interaction timelines.
- **Live Race Commentary**: 3,635 announcer lines and color commentary (100% jikkyo coverage).
- **Concert Lyrics**: 62 Winning Live song lyrics.

## Layered UmaTL Synchronization
Whenever upstream [UmaTL SD](https://github.com/UmaTL/hachimi-tl-en-sd) updates, new human-curated translations automatically and gracefully replace the machine-translated entries here. Everything else remains intact, maintaining 100% full coverage between updates. Synchronized automatically twice a week.

## Usage

**Fresh setup** — Meta URL (not `index.json`):
```
https://raw.githubusercontent.com/atatotata/gemini_horses/main/meta.json
```

**Gap filler** — in `hachimi\.tl_repos`, add after your main repo (higher `id` wins):
```json
{ "id": 2, "index": "https://raw.githubusercontent.com/atatotata/gemini_horses/main/index.json" }
```

## Attribution
- **Curated translations, textures, and media**: [UmaTL SD](https://github.com/UmaTL/hachimi-tl-en-sd) (noccu and contributors). Takes precedence wherever available.
- **Machine-translated gap coverage** (master strings, career & character stories, home dialogues, race commentary, concert lyrics): this project (Gemini MT).
