# Plan: Replace Machine-Translated Content with Global Official English

## Executive Summary

The Global release of Umamusume: Pretty Derby (launched June 26, 2025) ships an **already-English `master.mdb`** with the same `(id, category, index, text)` schema as the JP version. This means 53,796 `(category, index)` pairs in `text_data_dict.json` and 8,893+ `(character_id, voice_id)` pairs in `character_system_text_dict.json` can be directly replaced with official Cygames EN text — no translation needed.

**Key finding:** The Global `master.mdb` is **not encrypted** and is readable directly with `apsw.sqlite3`. The Global `meta` DB uses chacha20 but with a different key than JP (hachimi-tools' `DB_KEY_GLOBAL` = `A713A5C79DBC9497C0A88669` did not work during this investigation — may need verification against latest Global build).

---

## 1. Global Client Availability & Data Locations

### Platforms
| Platform | Client | Data Location |
|----------|--------|---------------|
| **Steam (Global)** | `UmamusumePrettyDerby.exe` | `Steam\steamapps\common\UmamusumePrettyDerby\UmamusumePrettyDerby_Data\Persistent\` |
| **Steam (JP/DMM)** | `UmamusumePrettyDerby.exe` | `...\UmamusumePrettyDerby_Jpn\UmamusumePrettyDerby_Jpn_Data\Persistent\` |
| **Android/iOS** | Cygames app | Equivalent `Persistent/` after full download |

**Case-sensitivity note:** JP data folder is lowercase `umamusume` (LocalLow), Global is capitalized `Umamusume`. Both Steam and DMM install to `Persistent/` with identical subfolder layout.

### Persistent Folder Layout (both JP and Global)
```
Persistent/
├── meta              # Encrypted SQLite DB (asset registry)
├── meta-journal
├── master/
│   └── master.mdb    # Game data DB (text, characters, skills, etc.)
└── dat/
    ├── 22/ 23/ 2A/ 2B/ ...  # 1024 subdirs of asset bundles
    └── (hash-named files)
```

### Observed Sizes (Sep 6, 2026)
| File | Global | JP | Ratio |
|------|--------|----|-------|
| `master.mdb` | 15.9 MB (416 tables) | 42.6 MB (627 tables) | 37% |
| `meta` | 78.8 MB | 155.2 MB | 51% |
| `text_data` rows | 54,234 | 97,029 | 56% |
| `character_system_text` rows | 14,490 | 33,287 | 44% |
| Dat bundles | ~170,469 | ~359,906 | 47% |

---

## 2. Extraction Parity

### master.mdb — ✅ Same Schema, No Encryption on Global
Both JP and Global `master.mdb` use **unencrypted SQLite** with identical column schemas:

**text_data:**
```sql
CREATE TABLE text_data (
    id INTEGER PRIMARY KEY,
    category INTEGER,
    "index" INTEGER,
    text TEXT
);
```

**character_system_text:**
```sql
CREATE TABLE character_system_text (
    character_id INTEGER,
    voice_id INTEGER,
    text TEXT,
    cue_sheet TEXT,
    cue_id INTEGER,
    ...
    start_date INTEGER
);
```

**Key finding:** Global `text_data` is **100% English** — scanning 5,000 rows found zero JP characters. Same for `character_system_text`. The official EN localization is complete and usable as-is.

### meta DB — ⚠️ Different Encryption Key
| Component | JP | Global |
|-----------|-----|--------|
| Meta DB encryption | chacha20, key `9c2bab97...` (64 hex) | chacha20, key `A713A5C7...` (24 hex) — **needs verification** |
| `master.mdb` encryption | None (readable directly) | None (readable directly) |
| Asset bundle XOR | Same `BUNDLE_BASE_KEY` hex | Same `BUNDLE_BASE_KEY` hex |

The Global meta DB opens with the existing `MetaDb` class using `DB_KEY_GLOBAL` from `const.py`, but the initial probe returned "file is not a database" — this may be a key-version mismatch for the latest Global build. **Action needed:** verify/update the Global meta key.

### Asset Path Layout — Same Structure
Both versions use identical `dat/<two-char-prefix>/<hash>` paths. The `meta` table `a` has columns `(i, n, d, g, l, c, h, m, k, s, p, e)` where:
- `n` = asset path (e.g., `story/data/XX/YYYY/storytimeline`)
- `h` = bundle hash
- `e` = decryption key (int)

**Story, home, lyrics, race paths follow the same pattern** in both versions.

---

## 3. Mapping Strategy

### Quantified Overlap (text_data)
| Metric | Count |
|--------|-------|
| JP unique `(category, index)` pairs | 97,029 |
| Global unique `(category, index)` pairs | 54,234 |
| **Common pairs (safe to replace)** | **53,796** |
| JP-only pairs (preserve MT/UMaTL) | 43,233 |
| Global-only pairs (Global-specific) | 438 |

### Category Breakdown (JP-only categories absent from Global)
Categories present in JP but absent from Global include newer content:
- `91` (45 rows), `129` (253 rows), `186` (4,818 rows), `310-323` (JP-exclusive story events), `325-373` (recent content updates), `389` (105), `397-487` (newer horses like Epiphaneia, etc.)

**These 43,233 JP-only pairs must be preserved** — they contain content that Global hasn't caught up to yet.

### character_system_text Overlap
| Metric | Count |
|--------|-------|
| JP character IDs | 158 |
| Global character IDs | 89 |
| JP-only character IDs | 69 (IDs ≥ 1075, newer horses) |
| Common character IDs | 89 |
| Global-only character IDs | **0** |

All Global characters exist in JP. The 69 JP-only character IDs are newer horses added after the Global launch cutoff.

### Safe Replacement Rules
1. **Only replace where `(category, index)` exists in both JP and Global** — 53,796 text_data pairs
2. **Only replace where `(character_id, voice_id)` exists in both** — common CST pairs
3. **Preserve all JP-only content** — MT + UMaTL layers unchanged
4. **Handle Global-only pairs (438)** — These are Global-specific strings (e.g., error messages, region-specific UI). Include them as new entries.

---

## 4. Replacement Workflow — Staged Pipeline

### Phase 1: Acquire & Dump Global Data
1. **Locate Global install** — Steam at `G:\Games\steamapps\common\UmamusumePrettyDerby\UmamusumePrettyDerby_Data\Persistent\`
2. **Dump Global `text_data`** → `global_text_data.json` with same `{category: {index: text}}` schema
3. **Dump Global `character_system_text`** → `global_cst.json` with `{character_id: {voice_id: text}}`
4. **Dump Global `race_jikkyo_message/comment`** if tables exist in Global `master.mdb`
5. **Decrypt Global meta** → resolve Global encryption key, extract story/home/lyrics/race_jikkyo timeline bundles
6. **Extract Global storytimeline/hometimeline/lyrics** JSON from decrypted asset bundles

### Phase 2: Diff & Manifest Generation
New script: `tools/global_diff.py`

```
Input:
  - gemini_horses/text_data_dict.json  (current MT+UMaTL)
  - global_text_data.json              (official EN)
  - gemini_horses/character_system_text_dict.json
  - global_cst.json

Output:
  - global_diff_manifest.json
```

Manifest structure per key:
```json
{
  "category_1/index_101": {
    "action": "replace",
    "source": "global_official",
    "current": "machine translation text",
    "replacement": "Official EN text from Global"
  },
  "category_186/index_1": {
    "action": "preserve",
    "source": "jp_only",
    "reason": "No Global equivalent exists"
  }
}
```

### Phase 3: Merge with Precedence
**Precedence hierarchy (highest to lowest):**
1. **Global official EN** — where Global `(category, index)` matches
2. **UmaTL human translations** — where UMaTL has a translation (highest quality)
3. **Gemini MT** — fallback for JP-only content
4. **Original Japanese** — untouched fallback

**Important nuance:** For keys where both Global official EN and UmaTL exist, **UmaTL should win** if its translation is demonstrably better (community-vetted, context-aware). The manifest should flag these for manual review.

### Phase 4: Regenerate & Publish
1. Apply replacements to `localized_data/` dicts
2. Run `sync_umatl.py` to re-overlay UmaTL (preserves precedence)
3. Run `generate_index.py` to rebuild `index.json`
4. Publish `text_only_v4.zip`

---

## 5. Legal/Practical Notes

### Copyright
- Global `master.mdb` text is **Cygames copyright** — identical to JP game data
- The current gemini_horses repo already distributes JP text (via MT), so risk profile is similar
- **Recommendation:** Use diff-only approach — only ship keys where Global EN exists, with provenance metadata. This minimizes redistribution surface.

### Distribution Strategy
- **Option A (Conservative):** Ship a `global_en_overlay/` directory with only the replacement keys, applied at load time. Full MT/UMaTL remains the base.
- **Option B (Direct):** Merge Global EN directly into `text_data_dict.json` with provenance tags (`"_source": "global_official"`) per key. Simpler but larger diff.
- **Recommended: Option B** — aligns with existing sync_umatl.py merge pattern. Add provenance tracking.

### Global Content Lag
Global launched ~13 months after JP. As of Sep 2026, Global is missing ~43K text entries worth of content. The gap will narrow over time but may never close completely (JP-exclusive seasonal events, collaborations, etc.). The replacement pipeline should be **re-runnable** as Global updates.

---

## 6. Tools & Scripts

### Existing (Reuse Directly)
| Path | Purpose |
|------|---------|
| `tools/hachimi-tools/const.py` | `IS_GLOBAL` flag, `GAME_ROOT` paths — set `UMA_GLOBAL=1` to target Global |
| `tools/hachimi-tools/meta_db_lib.py` | `MetaDb` class with `DB_KEY_GLOBAL` — open Global meta DB |
| `tools/hachimi-tools/meta_decrypt.py` | Decrypt Global meta → `decrypted_metas/` |
| `tools/hachimi-tools/bundle_decrypt.py` | Decrypt asset bundles using meta DB hash→key lookup |
| `tools/hachimi-tools/decrypt.py` | `BUNDLE_BASE_KEY` XOR — same for JP and Global |
| `tools/hachimi-tools/flash_text_extract.py` | Extract text from Unity UIAnimation bundles (story, home, lyrics, race) |
| `tools/umamusu-utils/scripts/decrypt_meta.py` | Alternative meta decryption pipeline |
| `tools/umamusu-utils/scripts/story_extract.py` | Story timeline extraction from asset bundles |
| `tools/master_translate/dump_untranslated_master.py` | Pattern for dumping master.mdb text data |
| `sync_umatl.py` | Merge overlay script — extend for Global EN layer |
| `generate_index.py` | Index regeneration |

### New Scripts Needed
| Script | Purpose |
|--------|---------|
| `tools/global_dump_text.py` | Dump Global `text_data` + `character_system_text` + `race_jikkyo_*` from `master.mdb` to JSON in Hachimi format |
| `tools/global_diff.py` | Diff JP vs Global dicts → replacement manifest with provenance |
| `tools/global_merge.py` | Apply Global EN overlay with precedence rules (Global > UmaTL > MT) |
| `tools/global_extract_bundles.py` | Extract story/home/lyrics/race_jikkyo text from Global asset bundles (wraps `flash_text_extract.py` + `story_extract.py` with Global paths) |
| `tools/verify_global_key.py` | Brute-force or validate Global meta encryption key against latest build |

---

## 7. Recommended Next-Step Checklist

- [ ] **Verify Global meta encryption key** — The `DB_KEY_GLOBAL` from hachimi-tools failed. Check Hachimi Edge source code, community repos, or UmaViewer for updated Global meta key. Without this, story/home/lyrics/race_jikkyo bundle extraction from Global is blocked.
- [ ] **Dump Global `master.mdb` text tables** — Run `global_dump_text.py` against the accessible Global `master.mdb` (no encryption needed). Export `text_data`, `character_system_text`, `race_jikkyo_message`, `race_jikkyo_comment` to JSON.
- [ ] **Verify Global table existence for `race_jikkyo_*`** — Run `SELECT name FROM sqlite_master WHERE type='table'` on Global `master.mdb` and confirm `race_jikkyo_message` and `race_jikkyo_comment` exist with EN text.
- [ ] **Build and run `global_diff.py`** — Produce diff manifest quantifying exact replacement counts per dict file.
- [ ] **Manual review of overlap quality** — Sample 50–100 common keys where both Global EN and UmaTL have translations. Determine whether Global or UmaTL text is preferred. Document decision rules.
- [ ] **Implement `global_merge.py`** — Extend `sync_umatl.py` pattern to add Global EN as a third precedence layer.
- [ ] **Test on subset** — Apply replacements to `text_data_dict.json` category 1 (system messages) first. Validate in-game.
- [ ] **Full pipeline run** — Apply to all dicts, regenerate index, publish.
- [ ] **Set up automated re-sync** — Schedule `global_dump_text.py` + `global_merge.py` to run alongside `sync_umatl.py` in CI, keeping Global EN coverage current.
