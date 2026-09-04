# Gemini Horses - Umamusume English Localization & Skill Data

Comprehensive English translation patch for Umamusume: Pretty Derby (DMM/Steam), compatible with [Hachimi](https://github.com/Hachimi-Hachimi/Hachimi) and Hachimi-Edge.

## Features
- **100% Master Lore Coverage**: Over 94,500 strings covering all skills, item descriptions, character self-introductions, titles, and menus.
- **Numerical Skill Data (SD)**: Skill descriptions feature numerical activation conditions, speeds (m/s), stamina recovery, and duration stats.
- **Complete Voice Lines**: 33,287 voice lines translated for all 158 playable characters and NPCs in `character_system_text_dict.json`.
- **Full Cutscenes**: 2,510 story cutscenes including all 1,160 support-card career training events.
- **Zero Artifacts**: Clean natural formatting with native line breaks.

## Installation via Hachimi

1. Open your game directory:
   `<Game_Directory>/hachimi/.tl_repos`

2. Add this repository to the `repos` array:
   ```json
   {
     "repos": [
       {
         "id": 1,
         "index": "https://raw.githubusercontent.com/Otattemita/gemini_horses/main/index.json"
       }
     ]
   }
   ```
   *(Or keep standard UmaTL as `id: 1` and add this as `id: 2` to layer on top!)*

3. Launch the game. Hachimi will automatically download and update all translations.

## Upstream UmaTL Synchronization

This repository automatically synchronizes with upstream [UmaTL](https://github.com/UmaTL/hachimi-tl-en-sd) to ensure curated human translations always take precedence over machine-translated fallback text.

- **Automated GitHub Action**: Runs weekly to pull changes from UmaTL, overlays them onto dictionaries and story cutscenes, regenerates `index.json`, and commits updates.
- **Local Sync**: You can also run the local synchronization script at any time:
  ```bash
  python sync_umatl.py
  ```
