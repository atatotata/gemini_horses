#!/usr/bin/env python3
"""Verify 938 home files: GH <-> HA byte-identical, no CRLF, max cols."""
import json, os, re, unicodedata, time, random, sys
from pathlib import Path

GH_HOME = Path(r"G:/Games/steamapps/common/UmamusumePrettyDerby_Jpn/gemini_horses/localized_data/assets/home/data")
HA_HOME = Path(r"G:/Games/steamapps/common/UmamusumePrettyDerby_Jpn/hachimi/localized_data_1/assets/home/data")

TAG_RE = re.compile(r"<[^>]+>")

def char_w(ch):
    eaw = unicodedata.east_asian_width(ch)
    return 2 if eaw in ("W", "F") else 1

def disp_width(s):
    stripped = TAG_RE.sub("", s)
    return sum(char_w(c) for c in stripped)

def main():
    print("=== Home Verification ===", flush=True)
    t0 = time.time()

    gh_files = sorted(GH_HOME.rglob("hometimeline_*.json"))
    ha_files = sorted(HA_HOME.rglob("hometimeline_*.json"))
    print(f"GH home files: {len(gh_files)}", flush=True)
    print(f"HA home files: {len(ha_files)}", flush=True)

    identical = 0
    different = 0
    crlf_count = 0
    max_cols = 0
    total_blocks = 0
    overflow_count = 0
    single_word_overflow = 0
    overflow_samples = []
    missing_in_ha = 0
    missing_in_gh = 0

    gh_set = {f.relative_to(GH_HOME) for f in gh_files}
    ha_set = {f.relative_to(HA_HOME) for f in ha_files}

    for rel in sorted(gh_set - ha_set):
        missing_in_ha += 1
    for rel in sorted(ha_set - gh_set):
        missing_in_gh += 1

    for fi, gh_fp in enumerate(gh_files):
        ha_fp = HA_HOME / gh_fp.relative_to(GH_HOME)
        if not ha_fp.exists():
            different += 1
            continue
        gh_bytes = gh_fp.read_bytes()
        ha_bytes = ha_fp.read_bytes()
        if gh_bytes == ha_bytes:
            identical += 1
        else:
            different += 1

        if b"\r\n" in gh_bytes:
            crlf_count += 1

        data = json.loads(gh_bytes)
        for block in data.get("text_block_list", []):
            total_blocks += 1
            for field in ["name", "text"]:
                txt = block.get(field, "")
                for ln in txt.split("\n"):
                    c = disp_width(ln.strip())
                    if c > max_cols:
                        max_cols = c
                    if c > 42:
                        overflow_count += 1
                        words_stripped = TAG_RE.sub("", ln.strip()).split()
                        if len(words_stripped) <= 1:
                            single_word_overflow += 1
                        elif len(overflow_samples) < 5:
                            try:
                                overflow_samples.append(f"[{c}] {ln.strip()[:50]}")
                            except:
                                overflow_samples.append(f"[{c}] (encoding error)")

        if (fi + 1) % 300 == 0:
            print(f"  Checked {fi+1}/{len(gh_files)}...", flush=True)

    elapsed = time.time() - t0

    print(f"\n=== VERIFICATION RESULTS ===", flush=True)
    print(f"GH files: {len(gh_files)}", flush=True)
    print(f"HA files: {len(ha_files)}", flush=True)
    print(f"Missing GH->HA: {missing_in_ha}", flush=True)
    print(f"Missing HA->GH: {missing_in_gh}", flush=True)
    print(f"Byte-identical GH<->HA: {identical}/{len(gh_files)}", flush=True)
    print(f"Different: {different}", flush=True)
    print(f"CRLF-contaminated: {crlf_count}", flush=True)
    print(f"Total blocks: {total_blocks}", flush=True)
    print(f"Max cols (tag-stripped): {max_cols}", flush=True)
    print(f"Lines >42 cols: {overflow_count} ({overflow_count/max(total_blocks*2,1)*100:.2f}%)", flush=True)
    print(f"Single-word overflow >42: {single_word_overflow}", flush=True)
    print(f"Multi-word overflow >42: {overflow_count - single_word_overflow}", flush=True)

    if overflow_samples:
        print(f"\nOverflow samples:", flush=True)
        for s in overflow_samples:
            print(f"  {s}", flush=True)

    # Random excerpt
    print(f"\n=== Random Excerpt ===", flush=True)
    sample = random.choice(gh_files)
    with open(sample, "r", encoding="utf-8") as f:
        data = json.load(f)
    print(f"File: {sample.relative_to(GH_HOME)}", flush=True)
    try:
        print(f"  Title: {data.get('title', 'N/A')}", flush=True)
    except:
        print(f"  Title: (encoding error)", flush=True)
    blocks = data.get("text_block_list", [])
    if blocks:
        b = blocks[0]
        try:
            print(f"  Block[0] name: {b.get('name', '')}", flush=True)
            for ln in b.get("text", "").split("\n"):
                c = disp_width(ln.strip())
                print(f"    [{c:2d} cols] {ln}", flush=True)
        except:
            print(f"  (encoding error in sample)", flush=True)

    print(f"\nElapsed: {elapsed:.1f}s", flush=True)

    # Override for 938 check (only count NEW home files)
    print(f"\n=== 938 Home File Check ===", flush=True)
    scan_src = Path(r"C:/TMP/home_fetch/story_json/home/data")
    src_files = sorted(scan_src.rglob("hometimeline_*.json"))
    merged_gh = 0
    merged_ha = 0
    identical_938 = 0
    for sf in src_files:
        rel = sf.relative_to(scan_src)
        gh_f = GH_HOME / rel
        ha_f = HA_HOME / rel
        if gh_f.exists():
            merged_gh += 1
        if ha_f.exists():
            merged_ha += 1
        if gh_f.exists() and ha_f.exists() and gh_f.read_bytes() == ha_f.read_bytes():
            identical_938 += 1
    print(f"Source files: {len(src_files)}", flush=True)
    print(f"Merged to GH: {merged_gh}", flush=True)
    print(f"Merged to HA: {merged_ha}", flush=True)
    print(f"Byte-identical 938 GH<->HA: {identical_938}/{len(src_files)}", flush=True)

if __name__ == "__main__":
    main()
