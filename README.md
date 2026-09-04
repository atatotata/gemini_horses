# gemini_horses

Full machine translation patch and numerical skill data overlay for Umamusume: Pretty Derby (DMM/Steam). Compatible with Hachimi.

## Contents
- **Master Data**: 94,500+ localized UI, skill, and item strings.
- **Skill Data (SD)**: In-line numerical stats, speeds, and triggers.
- **Voice Lines**: 33,287 voice lines across all 158 characters.
- **Stories**: 2,500+ translated timelines, including all support-card events.

## Layered UmaTL Synchronization
Whenever upstream [UmaTL](https://github.com/UmaTL/hachimi-tl-en) updates, new human-curated translations automatically and gracefully replace the machine-translated entries here. Everything else remains intact, maintaining 100% full coverage between updates. Synchronized automatically twice a week.

## Usage

**Fresh setup** — Meta URL (not `index.json`):
```
https://raw.githubusercontent.com/Otattemita/gemini_horses/main/meta.json
```

**Gap filler** — in `hachimi\.tl_repos`, add after your main repo (higher `id` wins):
```json
{ "id": 2, "index": "https://raw.githubusercontent.com/Otattemita/gemini_horses/main/index.json" }
```

## Attribution
- **Curated translations, textures, and media**: [UmaTL](https://github.com/UmaTL/hachimi-tl-en) (noccu and contributors). Takes precedence wherever available.
- **Machine-translated gap coverage** (master strings, support-card stories): this project (Gemini MT).
