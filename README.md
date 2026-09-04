# gemini_horses

Full English translation patch and numerical skill data overlay for Umamusume: Pretty Derby (DMM/Steam). Compatible with Hachimi.

## Contents
- **Master Data**: 94,500+ localized UI, skill, and item strings.
- **Skill Data (SD)**: In-line numerical stats, speeds, and triggers.
- **Voice Lines**: 33,287 voice lines across all 158 characters.
- **Stories**: 2,500+ translated timelines, including all support-card events.
- **UmaTL Sync**: Automated biweekly overlay of curated human translations.

## Usage

In `hachimi\.tl_repos`:

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

Hachimi handles downloads and updates on launch.
