#!/usr/bin/env python3
"""Compact verify: 938 new home files only."""
import json, re, unicodedata, time, random
from pathlib import Path

GH_HOME = Path(r"G:/Games/steamapps/common/UmamusumePrettyDerby_Jpn/gemini_horses/localized_data/assets/home/data")
HA_HOME = Path(r"G:/Games/steamapps/common/UmamusumePrettyDerby_Jpn/hachimi/localized_data_1/assets/home/data")
SCAN_SRC = Path(r"C:/TMP/home_fetch/story_json/home/data")

TAG_RE = re.compile(r"<[^>]+>")
def char_w(ch):
    eaw = unicodedata.east_asian_width(ch)
    return 2 if eaw in ("W", "F") else 1
def disp_width(s):
    stripped = TAG_RE.sub("", s)
    return sum(char_w(c) for c in stripped)

def main():
    t0 = time.time()
    src_files = sorted(SCAN_SRC.rglob("hometimeline_*.json"))
    
    identical = 0
    crlf_count = 0
    max_cols = 0
    total_lines = 0
    overflow_multi = 0
    overflow_single = 0
    sample_excerpts = []
    
    for sf in src_files:
        rel = sf.relative_to(SCAN_SRC)
        gh_f = GH_HOME / rel
        ha_f = HA_HOME / rel
        if not gh_f.exists() or not ha_f.exists():
            print(f"MISSING: {rel}")
            continue
        gh_bytes = gh_f.read_bytes()
        ha_bytes = ha_f.read_bytes()
        if gh_bytes != ha_bytes:
            print(f"DIFF: {rel}")
            continue
        identical += 1
        if b"\r\n" in gh_bytes:
            crlf_count += 1
        
        data = json.loads(gh_bytes)
        for block in data.get("text_block_list", []):
            for field in ["name", "text"]:
                txt = block.get(field, "")
                for ln in txt.split("\n"):
                    c = disp_width(ln.strip())
                    total_lines += 1
                    if c > max_cols:
                        max_cols = c
                    if c > 42:
                        words_stripped = TAG_RE.sub("", ln.strip()).split()
                        if len(words_stripped) <= 1:
                            overflow_single += 1
                        else:
                            overflow_multi += 1
    
    # Random excerpt
    sample = random.choice(src_files)
    rel = sample.relative_to(SCAN_SRC)
    with open(GH_HOME / rel, "r", encoding="utf-8") as f:
        data = json.load(f)
    
    elapsed = time.time() - t0
    print(f"=== 938 HOME MERGE RESULTS ===")
    print(f"Source files: {len(src_files)}")
    print(f"Byte-identical GH<->HA: {identical}/{len(src_files)}")
    print(f"CRLF-contaminated: {crlf_count}")
    print(f"Total lines: {total_lines}")
    print(f"Max cols: {max_cols}")
    print(f"Multi-word >42: {overflow_multi}")
    print(f"Single-word >42: {overflow_single}")
    print(f"Overflow rate: {(overflow_multi+overflow_single)/max(total_lines,1)*100:.3f}%")
    print(f"\nExcerpt: {rel}")
    print(f"  title: {data.get('title','N/A')}")
    b0 = data["text_block_list"][0]
    print(f"  name: {b0['name']}")
    for ln in b0["text"].split("\n"):
        print(f"  [{disp_width(ln.strip()):2d}] {ln}")
    print(f"Elapsed: {elapsed:.1f}s")

if __name__ == "__main__":
    main()
