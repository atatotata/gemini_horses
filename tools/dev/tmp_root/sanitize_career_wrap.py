#!/usr/bin/env python3
"""
Strict sanitizer for career overflow — UmaTL excluded, both repos in lockstep.

Wraps long EN text lines to 42 display columns using space-prefixed "\\n".
Tags are preserved in output but excluded from width calculations.
Processes only career prefixes: 50, 40, 80, 82, 83.
Skips UmaTL-curated prefixes: 00,01,02,04,08,09,10,11,12,13.
Keeps both gemini and hachimi repos bit-identical.
"""

import os
import re
import json
import hashlib
import unicodedata
import textwrap
import time
import sys
from collections import defaultdict
from concurrent.futures import ProcessPoolExecutor, as_completed
from pathlib import Path

# ─── Configuration ───────────────────────────────────────────────────────────
DISPLAY_COL_LIMIT = 42
TARGET_PREFIXES = ["40", "50", "80", "82", "83"]

GEMINI_BASE = Path(
    "G:/Games/steamapps/common/UmamusumePrettyDerby_Jpn"
    "/gemini_horses/localized_data/assets/story/data"
)
HACHIMI_BASE = Path(
    "G:/Games/steamapps/common/UmamusumePrettyDerby_Jpn"
    "/hachimi/localized_data_1/assets/story/data"
)

# Tag pattern: match any <...> tag (opening, closing, self-closing, with attrs)
TAG_RE = re.compile(r"<[^>]+>")


# ─── Unicode display-width helpers (no wcwidth dependency) ──────────────────
def _char_width(ch: str) -> int:
    """Return display column width for a single character."""
    eaw = unicodedata.east_asian_width(ch)
    if eaw in ("W", "F"):
        return 2
    return 1


def display_width(text: str) -> int:
    """Calculate the visual column width of *text*, counting tags as zero width."""
    # Strip tags for width calculation
    stripped = TAG_RE.sub("", text)
    return sum(_char_width(c) for c in stripped)


def strip_tags(text: str) -> str:
    """Remove markup tags — used only for display-width measurement."""
    return TAG_RE.sub("", text)


# ─── Word-wrapper ────────────────────────────────────────────────────────────
def wrap_line(line: str, limit: int = DISPLAY_COL_LIMIT) -> str:
    """
    Word-wrap a single paragraph (no internal ``\\n``) to *limit* display cols.

    Returns the wrapped text with ``" \\n"`` (space+LF) between sublines.
    Tags are preserved in the output but excluded from width measurement.
    """
    # Fast path: already fits
    if display_width(line) <= limit:
        return line

    # Tokenize: split on whitespace boundaries, preserving tags as part of tokens.
    # Strategy: walk character-by-character, building tokens that include
    # leading whitespace, then the word (including any embedded tags).
    tokens = re.findall(r"\S+|\s+", line)

    # Build wrapped result
    wrapped: list[str] = []
    current = ""
    current_w = 0

    for tok in tokens:
        tok_w = display_width(tok)
        if tok.strip() == "":
            # Whitespace token — potential break point
            if current_w + tok_w > limit and current:
                wrapped.append(current.rstrip())
                current = ""
                current_w = 0
                # Skip consuming the whitespace (it becomes leading space on next line)
            else:
                current += tok
                current_w += tok_w
        else:
            # Word token
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
    """
    Word-wrap a full text/choice field.

    1. Normalize ``\\r\\n`` → ``\\n``.
    2. Split on ``\\n`` into paragraphs.
    3. Wrap each paragraph independently to *limit* display cols.
    4. Rejoin paragraphs with ``" \\n"`` (space+LF).
    """
    # Normalize CRLF → LF
    normalized = text.replace("\r\n", "\n")
    # Split into paragraphs (preserving paragraph breaks)
    paragraphs = normalized.split("\n")

    wrapped_parts: list[str] = []
    for para in paragraphs:
        wrapped_parts.append(wrap_line(para, limit))

    return " \n".join(wrapped_parts)


# ─── File processing ─────────────────────────────────────────────────────────
def _max_line_cols(text: str) -> int:
    """Return the max display column width among all lines in *text*."""
    # The text field may have embedded \\n — measure each display line.
    lines = text.replace("\\n", "\n").split("\n")
    return max((display_width(ln) for ln in lines), default=0)


def process_file(filepath: Path) -> dict:
    """
    Process a single career JSON file.

    Returns a stats dict for aggregation.
    """
    raw = filepath.read_text(encoding="utf-8")

    # CRLF sanity check
    has_crlf = "\r\n" in raw or "\r" in raw

    data = json.loads(raw)

    # Make a mutable copy for comparison
    orig_no_wrap = data.get("no_wrap", False)
    data["no_wrap"] = True  # Ensure stays true

    stats = {
        "file": str(filepath),
        "blocks": 0,
        "choices": 0,
        "items_wrapped": 0,
        "lines_before": 0,
        "lines_after": 0,
        "max_cols_after": 0,
        "has_crlf": has_crlf,
        "changed": False,
    }

    for block in data.get("text_block_list", []):
        stats["blocks"] += 1

        # Process block text
        orig_text = block.get("text", "")
        # Count original display lines
        stats["lines_before"] += len(orig_text.replace("\r\n", "\n").split("\n"))
        new_text = wrap_text_field(orig_text, DISPLAY_COL_LIMIT)
        new_lines = new_text.split("\n")
        stats["lines_after"] += len(new_lines)
        # Track max display cols
        for ln in new_lines:
            w = display_width(ln.lstrip())  # lstrip to account for leading space before \n
            if w > stats["max_cols_after"]:
                stats["max_cols_after"] = w
        # Check if wrapping occurred
        if new_text != orig_text:
            stats["items_wrapped"] += 1
            stats["changed"] = True
        block["text"] = new_text

        # Process choice strings
        choices = block.get("choice_data_list", [])
        for i, choice in enumerate(choices):
            stats["choices"] += 1
            stats["lines_before"] += len(choice.replace("\r\n", "\n").split("\n"))
            new_choice = wrap_text_field(choice, DISPLAY_COL_LIMIT)
            new_clines = new_choice.split("\n")
            stats["lines_after"] += len(new_clines)
            for ln in new_clines:
                w = display_width(ln.lstrip())
                if w > stats["max_cols_after"]:
                    stats["max_cols_after"] = w
            if new_choice != choice:
                stats["items_wrapped"] += 1
                stats["changed"] = True
            choices[i] = new_choice

    # Write output
    out = json.dumps(data, ensure_ascii=False, indent=2) + "\n"
    # Ensure LF only (no CRLF)
    out = out.replace("\r\n", "\n")
    filepath.write_text(out, encoding="utf-8", newline="")

    return stats


# ─── Twin sync ───────────────────────────────────────────────────────────────
def collect_files(base: Path, prefixes: list[str]) -> list[Path]:
    """Walk base directory and return all JSON files under target prefixes."""
    files = []
    for pfx in prefixes:
        pfx_dir = base / pfx
        if not pfx_dir.is_dir():
            continue
        for root, dirs, fnames in os.walk(pfx_dir):
            for fn in fnames:
                if fn.endswith(".json"):
                    files.append(Path(root) / fn)
    return files


def main():
    t0 = time.time()

    print("=" * 72)
    print("CAREER WRAP SANITIZER — UmaTL excluded, repos in lockstep")
    print("=" * 72)
    print(f"  Gemini base : {GEMINI_BASE}")
    print(f"  Hachimi base: {HACHIMI_BASE}")
    print(f"  Prefixes    : {TARGET_PREFIXES}")
    print(f"  Col limit   : {DISPLAY_COL_LIMIT}")
    print()

    # Collect files from gemini (canonical)
    gemini_files = collect_files(GEMINI_BASE, TARGET_PREFIXES)
    print(f"  Gemini career files: {len(gemini_files)}")

    # ─── Phase 1: Process all gemini files ───────────────────────────────
    total_files = 0
    total_blocks = 0
    total_choices = 0
    total_items_wrapped = 0
    total_lines_before = 0
    total_lines_after = 0
    global_max_cols = 0
    files_with_wraps = 0
    crlf_clean = True

    for fp in gemini_files:
        stats = process_file(fp)
        total_files += 1
        total_blocks += stats["blocks"]
        total_choices += stats["choices"]
        total_items_wrapped += stats["items_wrapped"]
        total_lines_before += stats["lines_before"]
        total_lines_after += stats["lines_after"]
        if stats["max_cols_after"] > global_max_cols:
            global_max_cols = stats["max_cols_after"]
        if stats["changed"]:
            files_with_wraps += 1
        if stats["has_crlf"]:
            crlf_clean = False

        if total_files % 2000 == 0:
            elapsed = time.time() - t0
            print(f"  ... processed {total_files}/{len(gemini_files)} files ({elapsed:.1f}s)")

    elapsed1 = time.time() - t0
    print(f"\n  Phase 1 done: {total_files} files in {elapsed1:.1f}s")
    print(f"  Blocks: {total_blocks}, Choices: {total_choices}")
    print(f"  Items wrapped: {total_items_wrapped}")
    print(f"  Files with wraps: {files_with_wraps}")
    print(f"  Lines before: {total_lines_before}, after: {total_lines_after}")
    print(f"  Max display cols after: {global_max_cols}")
    print(f"  CRLF clean: {crlf_clean}")

    # ─── Phase 2: Copy gemini → hachimi for identical bytes ──────────────
    print(f"\n  Phase 2: Syncing gemini → hachimi ...")
    sync_count = 0
    sync_errors = 0
    for gfp in gemini_files:
        rel = gfp.relative_to(GEMINI_BASE)
        hfp = HACHIMI_BASE / rel
        try:
            data = gfp.read_bytes()
            hfp.write_bytes(data)
            sync_count += 1
        except Exception as e:
            print(f"  SYNC ERROR: {rel}: {e}")
            sync_errors += 1

    elapsed2 = time.time() - t0
    print(f"  Synced: {sync_count}, errors: {sync_errors} ({elapsed2:.1f}s)")

    # ─── Phase 3: Spot-check hashes ──────────────────────────────────────
    print(f"\n  Phase 3: Spot-check hashes (gemini vs hachimi) ...")
    spot_samples = [
        "50/1001/storytimeline_501001100.json",
        "50/1020/storytimeline_501020719.json",
        "82/0001/storytimeline_820001001.json",
    ]
    hash_match = True
    for s in spot_samples:
        gp = GEMINI_BASE / s
        hp = HACHIMI_BASE / s
        hg = hashlib.sha256(gp.read_bytes()).hexdigest()
        hh = hashlib.sha256(hp.read_bytes()).hexdigest()
        match = "IDENTICAL" if hg == hh else "DIFFERENT"
        if hg != hh:
            hash_match = False
        print(f"    {s}: {match}")

    # ─── Phase 4: Detailed spot-checks ───────────────────────────────────
    print(f"\n  Phase 4: Detailed spot-checks ...")
    spot_checks = [
        "50/1001/storytimeline_501001100.json",
        "50/1020/storytimeline_501020719.json",
        "82/0001/storytimeline_820001001.json",
    ]
    for s in spot_checks:
        gp = GEMINI_BASE / s
        data = json.loads(gp.read_text(encoding="utf-8"))
        print(f"\n  --- {s} ---")
        print(f"  no_wrap: {data.get('no_wrap')}")
        blocks = data.get("text_block_list", [])
        print(f"  blocks: {len(blocks)}")
        wrapped_count = 0
        for block in blocks:
            t = block.get("text", "")
            if "\n" in t:
                wrapped_count += 1
            # Show first wrapped excerpt
            if wrapped_count <= 2 and " \n" in t:
                excerpt = t[:200]
                print(f"  wrapped excerpt: {excerpt!r}")
            # Check line cols
            for ln in t.split("\n"):
                w = display_width(ln.lstrip())
                if w > DISPLAY_COL_LIMIT:
                    print(f"  OVERFLOW: {w} cols: {ln[:80]!r}")
            for c in block.get("choice_data_list", []):
                for ln in c.split("\n"):
                    w = display_width(ln.lstrip())
                    if w > DISPLAY_COL_LIMIT:
                        print(f"  CHOICE OVERFLOW: {w} cols: {c[:80]!r}")

    # ─── Summary ─────────────────────────────────────────────────────────
    elapsed_total = time.time() - t0
    print(f"\n{'=' * 72}")
    print(f"SUMMARY")
    print(f"{'=' * 72}")
    print(f"  Files processed      : {total_files}")
    print(f"  Blocks               : {total_blocks}")
    print(f"  Choice strings       : {total_choices}")
    print(f"  Items wrapped        : {total_items_wrapped}")
    print(f"  Files with wraps     : {files_with_wraps}")
    print(f"  Lines before         : {total_lines_before}")
    print(f"  Lines after          : {total_lines_after}")
    print(f"  Max display cols     : {global_max_cols}")
    print(f"  CRLF clean           : {crlf_clean}")
    print(f"  Gemini ↔ Hachimi     : {'IDENTICAL' if hash_match else 'MISMATCH'}")
    print(f"  Total elapsed        : {elapsed_total:.1f}s")
    print(f"{'=' * 72}")
    print(f"READY for reindex lane to consume.")
    print(f"{'=' * 72}")


if __name__ == "__main__":
    import io
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding="utf-8", errors="replace")
    main()
