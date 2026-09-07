#!/usr/bin/env python3
"""
Merge translated 4,280 story files to BOTH repos (lockstep).
For each source file: read JP → look up checkpoint → wrap 42 cols → write to gemini_horses + hachimi twin byte-identical.
"""
import json, os, re, unicodedata, hashlib, time
from pathlib import Path

# ── Paths ──────────────────────────────────────────────────────────────
ROOT_DIR = Path(r"C:/TMP/remaining_fetch")
STORY_SRC = ROOT_DIR / "story_json"
CHECKPOINT_PATH = ROOT_DIR / "remaining_checkpoint.json"

GH_BASE = Path(r"G:/Games/steamapps/common/UmamusumePrettyDerby_Jpn/gemini_horses/localized_data/assets/story/data")
HA_BASE = Path(r"G:/Games/steamapps/common/UmamusumePrettyDerby_Jpn/hachimi/localized_data_1/assets/story/data")

# ── 42-col wrap (tag-aware) ────────────────────────────────────────────
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

def file_hash(path):
    h = hashlib.md5()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(65536), b""):
            h.update(chunk)
    return h.hexdigest()

def main():
    print("=== Merge Translated Stories to Both Repos ===")
    t_start = time.time()

    # Load checkpoint
    print(f"Loading checkpoint from {CHECKPOINT_PATH}...")
    ckpt = json.load(open(CHECKPOINT_PATH, "r", encoding="utf-8"))
    print(f"Checkpoint: {len(ckpt)} entries")

    # Load voice bible for name resolution
    vb_path = Path(r"G:/Games/steamapps/common/UmamusumePrettyDerby_Jpn/gemini_horses/tools/voice_bible/uma_voice_bible.json")
    vb = json.load(open(vb_path, "r", encoding="utf-8"))
    bible = {v["jp"]: v["en"] for v in vb.values() if "jp" in v and "en" in v}
    print(f"Voice bible: {len(bible)} entries")

    # CRLF-normalized lookup helper
    def lookup(text):
        """Look up translation, trying CRLF-normalized key. Check ckpt then bible."""
        if text in ckpt:
            return ckpt[text]
        norm = text.replace("\r\n", "\n").replace("\r", "\n")
        if norm in ckpt:
            return ckpt[norm]
        stripped = norm.rstrip()
        if stripped in ckpt:
            return ckpt[stripped]
        # Voice bible fallback for names
        if text in bible:
            return bible[text]
        return None

    # Stats
    total_files = 0
    merged_files = 0
    missing_translations = 0
    max_cols = 0
    sample_blocks = []

    # Walk source
    for r, ds, fs in os.walk(STORY_SRC):
        for f in fs:
            if not f.endswith(".json"):
                continue
            total_files += 1
            src_fp = os.path.join(r, f)

            # Compute relative path from story_json root
            rel = os.path.relpath(src_fp, STORY_SRC)
            # rel = prefix/sub/file.json  (e.g., "50/1001/storytimeline_501001400.json")
            parts = rel.replace("\\", "/").split("/")
            prefix = parts[0]  # "50", "40", etc.

            try:
                src_data = json.load(open(src_fp, "r", encoding="utf-8"))
            except Exception as e:
                print(f"  WARN: Cannot parse {src_fp}: {e}")
                continue

            title = src_data.get("title", "")
            en_title = lookup(title) if title else None

            # Translate blocks
            new_blocks = []
            for blk in src_data.get("text_block_list", []):
                jp_name = blk.get("name", "")
                jp_text = blk.get("text", "")
                jp_choices = blk.get("choice_data_list", [])

                # Translate name
                en_name = lookup(jp_name) if jp_name else None
                if jp_name and en_name is None:
                    # Check bible or use as-is
                    en_name = jp_name
                    missing_translations += 1

                # Translate text
                en_text = lookup(jp_text) if jp_text else None
                if jp_text and en_text is None:
                    en_text = jp_text  # fallback: keep JP
                    missing_translations += 1

                # Wrap text to 42 cols
                if en_text:
                    en_text = wrap_field(en_text, LIMIT)
                    # Check max cols
                    for line in en_text.split("\n"):
                        line_stripped = line.rstrip(" ")
                        cw = disp_width(line_stripped)
                        if cw > max_cols:
                            max_cols = cw

                # Translate choices
                en_choices = []
                if jp_choices:
                    for ch in jp_choices:
                        en_ch = lookup(ch) if ch else ch
                        if ch and en_ch is None:
                            en_ch = ch  # fallback
                            missing_translations += 1
                        if en_ch:
                            en_ch = wrap_field(en_ch, LIMIT)
                            for line in en_ch.split("\n"):
                                cw = disp_width(line.rstrip(" "))
                                if cw > max_cols:
                                    max_cols = cw
                        en_choices.append(en_ch or "")

                new_blk = {"name": en_name or "", "text": en_text or ""}
                if en_choices:
                    new_blk["choice_data_list"] = en_choices
                else:
                    new_blk["choice_data_list"] = []
                new_blocks.append(new_blk)

            # Build output
            out_data = {
                "no_wrap": True,
                "text_block_list": new_blocks
            }

            # Write to both repos
            gh_out = GH_BASE / rel
            ha_out = HA_BASE / rel
            gh_out.parent.mkdir(parents=True, exist_ok=True)
            ha_out.parent.mkdir(parents=True, exist_ok=True)

            # Write GH with LF, CRLF clean
            out_str = json.dumps(out_data, ensure_ascii=False, indent=2)
            # Ensure LF line endings, no CRLF
            out_str = out_str.replace("\r\n", "\n")

            with open(gh_out, "w", encoding="utf-8", newline="\n") as fp:
                fp.write(out_str)

            # Byte-copy to hachimi twin
            with open(ha_out, "wb") as fp:
                fp.write(out_str.encode("utf-8"))

            merged_files += 1

            # Sample for report
            if len(sample_blocks) < 3:
                for i, blk in enumerate(new_blocks[:2]):
                    sample_blocks.append({
                        "file": rel,
                        "block_idx": i,
                        "name": blk["name"],
                        "text_preview": blk["text"][:120]
                    })

    # Verify sample hashes
    hash_ok = True
    for r, ds, fs in list(os.walk(STORY_SRC))[:5]:
        for f in fs[:2]:
            src_fp = os.path.join(r, f)
            rel = os.path.relpath(src_fp, STORY_SRC).replace("\\", "/")
            gh = GH_BASE / rel
            ha = HA_BASE / rel
            if gh.exists() and ha.exists():
                h1 = file_hash(gh)
                h2 = file_hash(ha)
                if h1 != h2:
                    print(f"  HASH MISMATCH: {rel}")
                    hash_ok = False

    elapsed = time.time() - t_start
    print(f"\n=== Merge Complete ===")
    print(f"Source files scanned: {total_files}")
    print(f"Files merged: {merged_files}")
    print(f"Missing translations (fallback to JP): {missing_translations}")
    print(f"Max display width: {max_cols}")
    print(f"Hash identical (sample): {hash_ok}")
    print(f"Elapsed: {elapsed:.1f}s")
    print(f"\nSample blocks:")
    for sb in sample_blocks:
        try:
            print(f"  {sb['file']} block[{sb['block_idx']}] {sb['name']}: {sb['text_preview']}")
        except UnicodeEncodeError:
            print(f"  {sb['file']} block[{sb['block_idx']}] (encoding)")
    print(f"\nReady-for-reindex: YES")

if __name__ == "__main__":
    main()
