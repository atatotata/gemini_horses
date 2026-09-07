#!/usr/bin/env python3
"""
Step 3: Merge translated 938 home files to BOTH repos lockstep.
For each source JSON: map name/text/title via checkpoint, wrap 42 cols, output to GH+HA.
"""
import json, os, re, unicodedata, time, hashlib
from pathlib import Path

# ── Paths ──────────────────────────────────────────────────────────────
ROOT_DIR = Path(r"C:/TMP/home_fetch")
HOME_SRC = ROOT_DIR / "story_json" / "home" / "data"
CHECKPOINT_PATH = ROOT_DIR / "home_checkpoint.json"
GH_HOME = Path(r"G:/Games/steamapps/common/UmamusumePrettyDerby_Jpn/gemini_horses/localized_data/assets/home/data")
HA_HOME = Path(r"G:/Games/steamapps/common/UmamusumePrettyDerby_Jpn/hachimi/localized_data_1/assets/home/data")
SCAN_PATH = ROOT_DIR / "scan_home.json"

# ── 42-col tag-aware wrap (same as sanitize_fix_final.py) ─────────────
TAG_RE = re.compile(r"<[^>]+>")
LIMIT = 42

def char_w(ch):
    eaw = unicodedata.east_asian_width(ch)
    return 2 if eaw in ("W", "F") else 1

def disp_width(s):
    stripped = TAG_RE.sub("", s)
    return sum(char_w(c) for c in stripped)

def wrap_paragraph(para, limit):
    para = para.strip()
    if not para:
        return []
    words = para.split()
    if not words:
        return []
    lines = []
    cur = words[0]
    cur_w = disp_width(cur)
    for w in words[1:]:
        w_w = disp_width(w)
        if w_w > limit:
            lines.append(cur)
            cur = w
            cur_w = w_w
            continue
        sep_w = 1
        if cur_w + sep_w + w_w <= limit:
            cur += " " + w
            cur_w += sep_w + w_w
        else:
            lines.append(cur)
            cur = w
            cur_w = w_w
    lines.append(cur)
    return lines

def wrap_field(text, limit=LIMIT):
    if not text:
        return text
    norm = text.replace("\r\n", "\n").replace("\r", "\n")
    if "\n\n" in norm:
        paras = re.split(r"\n\s*\n", norm)
        out_paras = []
        for para in paras:
            collapsed = re.sub(r"\s+", " ", para.replace("\n", " ").strip())
            if not collapsed:
                out_paras.append("")
                continue
            wrapped = wrap_paragraph(collapsed, limit)
            out_paras.append(" \n".join(wrapped))
        return "\n\n".join(out_paras)
    else:
        collapsed = re.sub(r"\s+", " ", norm.replace("\n", " ").strip())
        if not collapsed:
            return ""
        wrapped = wrap_paragraph(collapsed, limit)
        return " \n".join(wrapped)

def norm_crlf(s):
    return s.replace("\r\n", "\n").replace("\r", "\n")

def key_lookup(checkpoint, jp_text):
    """Lookup with CRLF-normalized key."""
    jp_norm = norm_crlf(jp_text).strip()
    # Direct match
    if jp_norm in checkpoint:
        return checkpoint[jp_norm]
    # Try original
    if jp_text in checkpoint:
        return checkpoint[jp_text]
    return None

def main():
    print("=== Home Timeline Merge (Both Repos Lockstep) ===")
    t_start = time.time()

    # Load checkpoint
    with open(CHECKPOINT_PATH, "r", encoding="utf-8") as f:
        checkpoint = json.load(f)
    print(f"Checkpoint loaded: {len(checkpoint)} entries")

    # Load scan for file structures
    with open(SCAN_PATH, "r", encoding="utf-8") as f:
        scan = json.load(f)
    file_structures = scan["file_structures"]
    print(f"File structures: {len(file_structures)} files")

    # Process each file
    ok_count = 0
    fail_count = 0
    missing_count = 0
    max_cols = 0
    errors = []

    for rel_path, structure in file_structures.items():
        title = structure.get("title", "")
        blocks = structure.get("blocks", [])

        # Translate title
        en_title = key_lookup(checkpoint, title) if title and not title.isdigit() else title

        # Build translated blocks
        en_blocks = []
        for block in blocks:
            jp_name = block.get("name", "")
            jp_text = block.get("text", "")

            en_name = key_lookup(checkpoint, jp_name) if jp_name else jp_name
            en_text = key_lookup(checkpoint, jp_text) if jp_text else jp_text

            if en_name is None:
                en_name = jp_name  # fallback: keep original
            if en_text is None:
                en_text = jp_text  # fallback: keep original

            # Wrap text to 42 cols
            en_text = wrap_field(en_text, LIMIT)
            # Name wrapping (usually short, but wrap anyway)
            en_name = wrap_field(en_name, LIMIT)

            en_blocks.append({
                "name": en_name,
                "text": en_text,
            })

            # Track max cols
            for ln in en_text.split("\n"):
                c = disp_width(ln.strip())
                if c > max_cols:
                    max_cols = c

        # Build output JSON
        out_data = {
            "text_block_list": en_blocks,
            "no_wrap": True,
        }
        if en_title is not None:
            out_data["title"] = en_title

        # Write to GH
        gh_out = GH_HOME / rel_path
        gh_out.parent.mkdir(parents=True, exist_ok=True)
        content = json.dumps(out_data, ensure_ascii=False, indent=2) + "\n"
        gh_out.write_text(content, encoding="utf-8", newline="\n")

        # Byte-copy to HA
        ha_out = HA_HOME / rel_path
        ha_out.parent.mkdir(parents=True, exist_ok=True)
        ha_out.write_bytes(gh_out.read_bytes())

        ok_count += 1

        if ok_count % 100 == 0:
            print(f"  Progress: {ok_count}/{len(file_structures)} ({time.time()-t_start:.1f}s)")

    elapsed = time.time() - t_start

    # ── Verify byte-identical GH ↔ HA ──
    print("\n=== Verifying GH <-> HA byte-identical ===")
    identical_count = 0
    diff_count = 0

    gh_files = list(GH_HOME.rglob("*.json"))
    for gh_fp in gh_files:
        ha_fp = HA_HOME / gh_fp.relative_to(GH_HOME)
        if not ha_fp.exists():
            print(f"  MISSING in HA: {ha_fp}")
            diff_count += 1
            continue
        gh_bytes = gh_fp.read_bytes()
        ha_bytes = ha_fp.read_bytes()
        if gh_bytes == ha_bytes:
            identical_count += 1
        else:
            print(f"  DIFF: {gh_fp.relative_to(GH_HOME)}")
            diff_count += 1

    # Check no CRLF in output
    crlf_count = 0
    for gh_fp in gh_files:
        raw = gh_fp.read_bytes()
        if b"\r\n" in raw:
            crlf_count += 1

    # ── Summary ──
    print(f"\n=== MERGE COMPLETE ===")
    print(f"Files merged: {ok_count}/{len(file_structures)}")
    print(f"Max cols (tag-stripped): {max_cols}")
    print(f"GH <-> HA identical: {identical_count}/{len(gh_files)}")
    print(f"GH <-> HA different: {diff_count}")
    print(f"CRLF-contaminated files: {crlf_count}")
    print(f"Elapsed: {elapsed:.1f}s")

    # ── Random excerpt ──
    print("\n=== Random Excerpt ===")
    if gh_files:
        import random
        sample = random.choice(gh_files)
        with open(sample, "r", encoding="utf-8") as f:
            data = json.load(f)
        print(f"File: {sample.relative_to(GH_HOME)}")
        print(f"  Title: {data.get('title', 'N/A')}")
        blocks = data.get("text_block_list", [])
        if blocks:
            b = blocks[0]
            print(f"  Block[0] name: {b.get('name', '')}")
            for ln in b.get("text", "").split("\n"):
                print(f"    [{disp_width(ln.strip()):2d} cols] {ln}")

if __name__ == "__main__":
    main()
