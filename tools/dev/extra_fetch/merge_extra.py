#!/usr/bin/env python3
"""
Merge translated Extra Stories back into both repos.
- 42-col tag-aware wrap
- atomic write to gemini_horses + byte-copy to hachimi
- no_wrap: true, LF output
"""
import os
import re
import json
import time
import shutil
import hashlib
import unicodedata
from pathlib import Path

# ─── Config ────────────────────────────────────────────────────────────────
DISPLAY_COL_LIMIT = 42

STORY_JSON_DIR = Path(r"C:/TMP/extra_fetch/story_json")
CHECKPOINT_PATH = Path(r"C:/TMP/extra_fetch/extra_checkpoint.json")
PRE_RESOLVED_PATH = Path(r"C:/TMP/extra_fetch/pre_resolved_names.json")

GEMINI_BASE = Path(
    "G:/Games/steamapps/common/UmamusumePrettyDerby_Jpn"
    "/gemini_horses/localized_data/assets/story/data"
)
HACHIMI_BASE = Path(
    "G:/Games/steamapps/common/UmamusumePrettyDerby_Jpn"
    "/hachimi/localized_data_1/assets/story/data"
)

TAG_RE = re.compile(r"<[^>]+>")

# ─── Unicode display-width helpers ─────────────────────────────────────────
def _char_width(ch: str) -> int:
    eaw = unicodedata.east_asian_width(ch)
    if eaw in ("W", "F"):
        return 2
    return 1

def display_width(text: str) -> int:
    stripped = TAG_RE.sub("", text)
    return sum(_char_width(c) for c in stripped)

def wrap_line(line: str, limit: int = DISPLAY_COL_LIMIT) -> str:
    stripped_line = line.rstrip()
    if display_width(stripped_line) <= limit:
        return stripped_line
    tokens = re.findall(r"\S+|\s+", stripped_line)
    wrapped = []
    current = ""
    current_w = 0
    for tok in tokens:
        tok_w = display_width(tok)
        if tok.strip() == "":
            if current_w + tok_w > limit and current:
                wrapped.append(current.rstrip())
                current = ""
                current_w = 0
            else:
                current += tok
                current_w += tok_w
        else:
            if current_w + tok_w > limit and current:
                wrapped.append(current.rstrip())
                current = tok
                current_w = tok_w
            else:
                current += tok
                current_w += tok_w
    if current.strip():
        wrapped.append(current.rstrip())
    return " \n".join(wrapped)

def wrap_text_field(text: str, limit: int = DISPLAY_COL_LIMIT) -> str:
    normalized = text.replace("\r\n", "\n").replace("\r", "\n")
    paragraphs = normalized.split("\n")
    wrapped_parts = [wrap_line(para, limit) for para in paragraphs]
    joined = " \n".join(wrapped_parts)
    # Strip trailing spaces on each display line (they add phantom width)
    lines = joined.split("\n")
    return "\n".join(ln.rstrip() for ln in lines)

def max_line_cols(text: str) -> int:
    lines = text.replace("\\n", "\n").split("\n")
    return max((display_width(ln) for ln in lines), default=0)

def has_cjk(text: str) -> bool:
    if not text:
        return False
    return any(
        '\u3040' <= ch <= '\u30ff' or
        '\u4e00' <= ch <= '\u9fff' or
        '\u3400' <= ch <= '\u4dbf'
        for ch in text
    )

# ─── Main ──────────────────────────────────────────────────────────────────
def main():
    t0 = time.time()
    print("=== Merging Extra Stories ===\n")

    # Load checkpoint
    with open(CHECKPOINT_PATH, "r", encoding="utf-8") as f:
        checkpoint = json.load(f)
    print(f"Loaded checkpoint: {len(checkpoint)} entries")

    # Build file list — ONLY the 26 translated files
    STORY_IDS = [
        # 09: Story Event 09
        "90016001", "90021001", "90032001", "90054007",
        # 10: Seasonal
        "100006001", "100006002", "100006003",
        "100007001", "100007002", "100007003",
        "100008001", "100008002", "100008003",
        "100009001", "100009002", "100009003", "100009004",
        "100010001", "100010002", "100010003",
        "100011001", "100011002", "100011003",
        # 14: Seasonal
        "140001001", "140001002", "140001003",
    ]
    story_files = []
    for root, dirs, files in os.walk(STORY_JSON_DIR):
        for f in files:
            if f.startswith("storytimeline_") and f.endswith(".json"):
                # Extract story ID from filename
                sid = f.replace("storytimeline_", "").replace(".json", "")
                if sid in STORY_IDS:
                    story_files.append(os.path.join(root, f))
    print(f"Found {len(story_files)} translated source files (of {len(STORY_IDS)} target IDs)")

    # Stats
    total_blocks = 0
    total_choices = 0
    wrapped_items = 0
    max_cols = 0
    merged_files = 0
    missing_translations = []

    for src_path in sorted(story_files):
        rel = os.path.relpath(src_path, STORY_JSON_DIR)
        parts = rel.replace("\\", "/").split("/")
        # Extract prefix and sub: e.g. "10/0006/storytimeline_100006001.json" -> prefix="10", sub="0006"
        prefix = parts[0]
        sub = parts[1]
        fname = parts[2]

        with open(src_path, "r", encoding="utf-8") as f:
            src_data = json.load(f)

        out_blocks = []
        for blk in src_data.get("text_block_list", []):
            jp_name = blk.get("name", "")
            jp_text = blk.get("text", "")
            jp_choices = blk.get("choice_data_list", [])

            # Translate name
            if jp_name and jp_name in checkpoint:
                en_name = checkpoint[jp_name]
            elif jp_name:
                en_name = jp_name  # fallback: keep as-is
            else:
                en_name = ""

            # Translate text (normalize CRLF for lookup key)
            jp_text_norm = jp_text.replace("\r\n", "\n").replace("\r", "\n") if jp_text else ""
            if jp_text_norm and jp_text_norm in checkpoint:
                en_text = checkpoint[jp_text_norm]
            elif jp_text and jp_text in checkpoint:
                en_text = checkpoint[jp_text]
            elif jp_text_norm and has_cjk(jp_text_norm):
                missing_translations.append(f"{fname}: text '{jp_text_norm[:40]}...'")
                en_text = jp_text_norm  # fallback
            else:
                en_text = jp_text_norm or jp_text or ""

            # Normalize: LLM may return literal \n (backslash-n) as text — convert to real newlines
            en_text = en_text.replace("\\n", "\n")

            # Normalize CRLF in text before wrap
            en_text = en_text.replace("\r\n", "\n").replace("\r", "\n")

            # Wrap text to 42 cols
            en_text = wrap_text_field(en_text)
            total_blocks += 1

            # Translate choices
            en_choices = []
            for choice in jp_choices:
                if choice and choice in checkpoint:
                    en_c = checkpoint[choice]
                elif choice and has_cjk(choice):
                    missing_translations.append(f"{fname}: choice '{choice}'")
                    en_c = choice
                else:
                    en_c = choice or ""
                en_c = en_c.replace("\\n", "\n")
                en_c = wrap_text_field(en_c)
                en_choices.append(en_c)
                total_choices += 1

            # Measure max cols
            for line in en_text.split("\n"):
                w = display_width(line)
                if w > max_cols:
                    max_cols = w
            for c in en_choices:
                for line in c.split("\n"):
                    w = display_width(line)
                    if w > max_cols:
                        max_cols = w

            blk_out = {"name": en_name, "text": en_text, "choice_data_list": en_choices}
            out_blocks.append(blk_out)

        # Build output
        out_data = {
            "no_wrap": True,
            "text_block_list": out_blocks
        }

        # Write to gemini_horses
        gemini_dir = GEMINI_BASE / prefix / sub
        gemini_dir.mkdir(parents=True, exist_ok=True)
        gemini_path = gemini_dir / fname

        with open(gemini_path, "w", encoding="utf-8", newline="\n") as f:
            json.dump(out_data, f, ensure_ascii=False, indent=2)

        # Byte-copy to hachimi
        hachimi_dir = HACHIMI_BASE / prefix / sub
        hachimi_dir.mkdir(parents=True, exist_ok=True)
        hachimi_path = hachimi_dir / fname
        shutil.copy2(gemini_path, hachimi_path)

        merged_files += 1

    t1 = time.time()

    # Verification: hash check on a sample
    sample_files = [
        ("10", "0006", "storytimeline_100006001.json"),
        ("09", "0016", "storytimeline_90016001.json"),
    ]
    hash_match = True
    for prefix, sub, fname in sample_files:
        g = GEMINI_BASE / prefix / sub / fname
        h = HACHIMI_BASE / prefix / sub / fname
        if g.exists() and h.exists():
            gh = hashlib.md5(g.read_bytes()).hexdigest()
            hh = hashlib.md5(h.read_bytes()).hexdigest()
            if gh != hh:
                hash_match = False
                print(f"  HASH MISMATCH: {prefix}/{sub}/{fname}")

    # CRLF check
    crlf_clean = True
    for prefix, sub, fname in sample_files:
        g = GEMINI_BASE / prefix / sub / fname
        if g.exists():
            raw = g.read_bytes()
            if b"\r\n" in raw or b"\r" in raw:
                crlf_clean = False
                print(f"  CRLF FOUND: {prefix}/{sub}/{fname}")

    # Print sample translations
    print(f"\n{'=' * 60}")
    print("SAMPLE TRANSLATIONS")
    print(f"{'=' * 60}")

    # Sample 1: 100006001 block 0
    sample_path = GEMINI_BASE / "10" / "0006" / "storytimeline_100006001.json"
    if sample_path.exists():
        with open(sample_path, "r", encoding="utf-8") as f:
            sdata = json.load(f)
        b0 = sdata["text_block_list"][0]
        print(f"\n[100006001 Block 0]")
        print(f"  name: {b0['name']}")
        print(f"  text: {b0['text'][:120]}...")

    # Sample 2: 90016001 - look for a choice
    sample2_path = GEMINI_BASE / "09" / "0016" / "storytimeline_90016001.json"
    if sample2_path.exists():
        with open(sample2_path, "r", encoding="utf-8") as f:
            sdata = json.load(f)
        # Find first block with non-empty choices
        for i, blk in enumerate(sdata["text_block_list"]):
            if blk.get("choice_data_list"):
                print(f"\n[90016001 Block {i} with choices]")
                print(f"  name: {blk['name']}")
                print(f"  text: {blk['text'][:100]}...")
                for ci, c in enumerate(blk["choice_data_list"]):
                    print(f"  choice[{ci}]: {c}")
                break
        else:
            # No choices, just show block 0
            b0 = sdata["text_block_list"][0]
            print(f"\n[90016001 Block 0]")
            print(f"  name: {b0['name']}")
            print(f"  text: {b0['text'][:120]}...")

    # Report
    print(f"\n{'=' * 60}")
    print("MERGE REPORT")
    print(f"{'=' * 60}")
    print(f"  Merged files       : {merged_files}")
    print(f"  Total blocks       : {total_blocks}")
    print(f"  Total choices      : {total_choices}")
    print(f"  Max display cols   : {max_cols}")
    print(f"  CRLF clean         : {crlf_clean}")
    print(f"  Gemini=Hachimi     : {'IDENTICAL' if hash_match else 'MISMATCH'}")
    print(f"  Missing trans.     : {len(missing_translations)}")
    if missing_translations:
        for m in missing_translations[:10]:
            print(f"    - {m}")
    print(f"  Elapsed            : {t1-t0:.1f}s")
    print(f"{'=' * 60}")

if __name__ == "__main__":
    import io, sys
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding="utf-8", errors="replace")
    main()
