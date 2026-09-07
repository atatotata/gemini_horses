#!/usr/bin/env python3
import re, json, unicodedata, pathlib, os, sys, time
from pathlib import Path

TAG_RE = re.compile(r"<[^>]+>")
GEMINI_BASE = Path(r"G:/Games/steamapps/common/UmamusumePrettyDerby_Jpn/gemini_horses/localized_data/assets/story/data")
HACHIMI_BASE = Path(r"G:/Games/steamapps/common/UmamusumePrettyDerby_Jpn/hachimi/localized_data_1/assets/story/data")
LIMIT = 42
TARGETS = ["40","50","80","82","83"]

def char_w(ch):
    eaw = unicodedata.east_asian_width(ch)
    return 2 if eaw in ("W","F") else 1

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
        # if word itself is longer than limit, emit cur and then word as its own line (overflow allowed but rare; could split)
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
    # Preserve paragraph breaks (\n\n) — split on blank line
    # Normalize CRLF
    norm = text.replace("\r\n","\n").replace("\r","\n")
    # Split on double newline (paragraph separator)
    # Keep logic: if contains \n\n, split, else treat as single para
    if "\n\n" in norm:
        paras = re.split(r"\n\s*\n", norm)
        out_paras = []
        for para in paras:
            # collapse single newlines + excessive whitespace to single space
            collapsed = re.sub(r"\s+", " ", para.replace("\n"," ").strip())
            if not collapsed:
                out_paras.append("")
                continue
            wrapped = wrap_paragraph(collapsed, limit)
            out_paras.append(" \n".join(wrapped))
        return "\n\n".join(out_paras)
    else:
        # No blank-line paragraphs — collapse all whitespace/newlines to single space, then wrap
        collapsed = re.sub(r"\s+", " ", norm.replace("\n"," ").strip())
        if not collapsed:
            return ""
        wrapped = wrap_paragraph(collapsed, limit)
        return " \n".join(wrapped)

def process_file(fp):
    raw = fp.read_text(encoding="utf-8")
    data = json.loads(raw)
    changed = False
    wrapped_cnt = 0
    max_cols = 0
    for block in data.get("text_block_list", []):
        # text
        orig = block.get("text","")
        if orig:
            new = wrap_field(orig, LIMIT)
            if new != orig:
                changed = True
            wrapped_cnt += 1 if "\n" in new else 0
            block["text"] = new
            for ln in new.split("\n"):
                c = disp_width(ln.strip())
                if c > max_cols:
                    max_cols = c
        # choices
        choices = block.get("choice_data_list", [])
        if choices:
            new_choices=[]
            for c in choices:
                if c:
                    nc = wrap_field(c, LIMIT)
                    if nc != c:
                        changed = True
                    new_choices.append(nc)
                    for ln in nc.split("\n"):
                        cc = disp_width(ln.strip())
                        if cc > max_cols:
                            max_cols = cc
                else:
                    new_choices.append(c)
            block["choice_data_list"] = new_choices
    data["no_wrap"] = True
    return data, changed, max_cols, wrapped_cnt

def main():
    start=time.time()
    files=[]
    for pref in TARGETS:
        d = GEMINI_BASE/pref
        if d.exists():
            files.extend(list(d.rglob("storytimeline_*.json")))
    print(f"Found {len(files)} career files to re-wrap (limit {LIMIT})")
    total_changed=0
    total_blocks=0
    total_max=0
    wrapped_files=0
    for idx, fp in enumerate(files,1):
        data, changed, max_c, _ = process_file(fp)
        # write to gemini
        out = json.dumps(data, ensure_ascii=False, indent=2)
        # ensure LF
        fp.write_text(out + "\n", encoding="utf-8", newline="\n")
        # sync identical to hachimi
        hfp = HACHIMI_BASE / fp.relative_to(GEMINI_BASE)
        hfp.parent.mkdir(parents=True, exist_ok=True)
        hfp.write_bytes(fp.read_bytes())
        if changed:
            wrapped_files+=1
        total_changed+=1
        if max_c>total_max:
            total_max=max_c
        if idx%4000==0:
            print(f"  {idx}/{len(files)} ({time.time()-start:.1f}s) max {total_max}")
    # also verify UmaTL not touched
    for pref in ["04","09","10","11","00","01","02","08","12","13"]:
        sample = list((GEMINI_BASE/pref).rglob("*.json"))[:1]
        if sample:
            print(f"UmaTL {pref} untouched sample mtime {time.ctime(sample[0].stat().st_mtime)}")
    print(f"Done {len(files)} files in {time.time()-start:.1f}s, wrapped_files {wrapped_files}, max_cols {total_max}")
    # spot check
    import json as js
    for pref, name in [("50","storytimeline_501001100.json"), ("50","storytimeline_501020719.json")]:
        fp = GEMINI_BASE/pref/ name.split("_")[0][:4]  # not accurate
    # find sample files
    for fp in files[:2]:
        j=json.loads(fp.read_text(encoding="utf-8"))
        print(f"Sample {fp.relative_to(GEMINI_BASE)} no_wrap={j.get('no_wrap')}")
        for b in j["text_block_list"][:2]:
            txt=b.get("text","")
            print(repr(txt[:200]))
            for ln in txt.split("\n"):
                print(f"  [{disp_width(ln.strip())} cols] {repr(ln[:100])}")
            break

if __name__=="__main__":
    main()
