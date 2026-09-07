#!/usr/bin/env python3
import re, json, unicodedata, pathlib, os, sys
from pathlib import Path

TAG_RE = re.compile(r"<[^>]+>")
GEMINI_BASE = Path(r"G:/Games/steamapps/common/UmamusumePrettyDerby_Jpn/gemini_horses/localized_data/assets/story/data")
HACHIMI_BASE = Path(r"G:/Games/steamapps/common/UmamusumePrettyDerby_Jpn/hachimi/localized_data_1/assets/story/data")
LIMIT = 42

def char_w(ch):
    eaw = unicodedata.east_asian_width(ch)
    return 2 if eaw in ("W","F") else 1

def disp_width(s):
    stripped = TAG_RE.sub("", s)
    return sum(char_w(c) for c in stripped)

def wrap_paragraph(para, limit):
    para = para.strip()
    if not para:
        return [""]
    words = para.split()
    if not words:
        return [""]
    lines = []
    cur = words[0]
    cur_w = disp_width(cur)
    # handle initial word too long
    if cur_w > limit:
        # split long word crudely by chars
        # fallback: emit as is (overflow) - rare
        pass
    for w in words[1:]:
        w_w = disp_width(w)
        if w_w > limit:
            # long word: flush cur, then split w
            lines.append(cur)
            # split w into chunks
            chunk = ""
            chunk_w = 0
            for ch in w:
                # naive: tags inside w complicate; treat tag as zero and keep together
                # for now treat char by char
                cw = disp_width(ch) if not ch.startswith("<") else 0
                # Actually w may contain tags without spaces, splitting char by char would break tags
                # So for long w containing tags, just emit as single line (overflow) to avoid breaking tags
                if "<" in w and ">" in w:
                    chunk = w
                    break
                if chunk_w + cw > limit:
                    lines.append(chunk)
                    chunk = ch
                    chunk_w = cw
                else:
                    chunk += ch
                    chunk_w += cw
            cur = chunk
            cur_w = disp_width(cur)
            continue
        sep_w = 1  # space
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
    # Normalize CRLF and trim trailing spaces around existing newlines
    # Split on \n to preserve original paragraph breaks
    # First, normalize: replace \r, then split
    paras = text.replace("\r\n","\n").replace("\r","\n").split("\n")
    out_lines = []
    for para in paras:
        # para may be "" for blank line
        if para.strip() == "":
            out_lines.append("")
            continue
        # para may have leading/trailing spaces; strip then wrap
        # But if para already has wraps, we re-wrap it anyway to enforce limit
        wrapped = wrap_paragraph(para, limit)
        out_lines.extend(wrapped)
    # Now join out_lines with " \n" (space before newline) between every visual line
    # But preserve blank lines: if out_lines contains "" we need to keep them as empty line
    # Join logic: for each i, if out_lines[i]=="" -> produce "" (blank line), else produce line
    # Join with "\n" normally, but ensure space before \n for non-last lines
    # Standard: join with " \n" — but blank lines would become " \n \n"? We need to handle.
    # Simpler: build result by iterating and adding " \n" between non-last lines, with space
    # For blank lines, they are "" — we should not add leading space
    result_parts = []
    for i, ln in enumerate(out_lines):
        if i < len(out_lines)-1:
            # not last: add space before newline if ln not empty
            if ln == "":
                result_parts.append("\n")
            else:
                result_parts.append(ln + " \n")
        else:
            result_parts.append(ln)
    # The above produces array where each part includes newline; join without extra sep
    # But we built with newlines already inside parts, so concat
    result = "".join(result_parts)
    # The above loop double counts: better just " \n".join filtering blanks?
    # Reimplement clean: join with " \n" but handle blanks
    # Let's do simple join with " \n" then fix double spaces around blank lines
    # Actually easiest: " \n".join(out_lines) where out_lines may contain ""
    # Example out_lines = ["A","B","","C"] -> "A \nB \n \nC" -> blank line becomes " \n \n" which is " \n" + "" + " \n" => extra spaces
    # So we need blank-aware join:
    # We'll just use "\n".join and then replace every "\n" with " \n" except where line empty
    # Simpler: reconstruct final by iterating
    final = ""
    for idx, ln in enumerate(out_lines):
        if idx > 0:
            # separator before this line
            prev = out_lines[idx-1]
            # decide separator: if ln=="" or prev=="" -> just "\n"
            if ln == "" or prev == "":
                final += "\n"
            else:
                final += " \n"
        final += ln
    return final

def process_file(fp):
    data = json.loads(fp.read_text(encoding="utf-8"))
    changed = False
    total_wrapped = 0
    for block in data.get("text_block_list", []):
        for key in ("text",):
            orig = block.get(key, "")
            if orig:
                new = wrap_field(orig, LIMIT)
                if new != orig:
                    changed = True
                    total_wrapped += 1
                block[key] = new
        # choices
        choices = block.get("choice_data_list", [])
        if choices:
            new_choices = []
            for c in choices:
                if c:
                    nc = wrap_field(c, LIMIT)
                    if nc != c:
                        changed = True
                        total_wrapped += 1
                    new_choices.append(nc)
                else:
                    new_choices.append(c)
            block["choice_data_list"] = new_choices
    data["no_wrap"] = True
    return data, changed, total_wrapped

# Test on sample
if __name__ == "__main__":
    import sys
    # quick test
    sample = "Starting today, our challenge in the Twinkle Series with Special Week finally begins!"
    print("sample raw len", len(sample), "width", disp_width(sample))
    print("wrapped:", repr(wrap_field(sample)))
    print("lines:", wrap_field(sample).split("\n"))
    for l in wrap_field(sample).split("\n"):
        print(f"  [{disp_width(l.strip())} cols] {repr(l)}")
    # test with tags
    s2 = "After <chrname>'s public training session, a message from <support> arrived on my smartphone. The Dubai miss must have been so relieved and the distance was quite long."
    print("\n--- tags sample ---")
    print(repr(wrap_field(s2)))
    for l in wrap_field(s2).split("\n"):
        print(f"  [{disp_width(l.strip())}] {l}")
    # test with existing broken sample
    broken = "Starting today, our challenge in the     \nTwinkle Series     \nwith Special Week finally begins!"
    print("\n--- broken input rewrap ---")
    print(repr(wrap_field(broken)))
