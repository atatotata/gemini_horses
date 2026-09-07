#!/usr/bin/env python3
"""Verify merged files: no_wrap, CRLF, 42-col, byte-identical."""
import json, os, sys, unicodedata, re, hashlib, time
from pathlib import Path
sys.stdout.reconfigure(encoding="utf-8")

TAG_RE = re.compile(r"<[^>]+>")

def char_w(ch):
    eaw = unicodedata.east_asian_width(ch)
    return 2 if eaw in ("W", "F") else 1

def disp_width(s):
    stripped = TAG_RE.sub("", s)
    return sum(char_w(c) for c in stripped)

def file_hash(path):
    h = hashlib.md5()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(65536), b""):
            h.update(chunk)
    return h.hexdigest()

# Verify all 4,280 files across all prefixes
ROOT_SRC = Path(r"C:/TMP/remaining_fetch/story_json")
GH_BASE = Path(r"G:/Games/steamapps/common/UmamusumePrettyDerby_Jpn/gemini_horses/localized_data/assets/story/data")
HA_BASE = Path(r"G:/Games/steamapps/common/UmamusumePrettyDerby_Jpn/hachimi/localized_data_1/assets/story/data")

max_overall = 0
total_checked = 0
hash_mismatches = 0
nowrap_fails = 0
crlf_fails = 0
samples_printed = 0

for prefix in ["11", "40", "50", "80", "83"]:
    src_dir = ROOT_SRC / prefix
    if not src_dir.exists():
        continue
    for r, ds, fs in os.walk(src_dir):
        for f in fs:
            if not f.endswith(".json"):
                continue
            fp = os.path.join(r, f)
            rel = os.path.relpath(fp, ROOT_SRC).replace("\\", "/")
            gh_path = GH_BASE / rel
            ha_path = HA_BASE / rel
            
            if not gh_path.exists() or not ha_path.exists():
                continue
            
            # Check byte-identical
            gh_bytes = gh_path.read_bytes()
            ha_bytes = ha_path.read_bytes()
            if gh_bytes != ha_bytes:
                hash_mismatches += 1
            
            # Check no CRLF in content
            if b"\r\n" in gh_bytes:
                crlf_fails += 1
            
            # Parse and check
            d = json.loads(gh_bytes.decode("utf-8"))
            if not d.get("no_wrap"):
                nowrap_fails += 1
            
            blocks = d.get("text_block_list", [])
            for b in blocks:
                text = b.get("text", "")
                for line in text.split(" \n"):
                    cw = disp_width(line.rstrip(" "))
                    if cw > max_overall:
                        max_overall = cw
            
            # Print samples
            if samples_printed < 3 and blocks:
                b0 = blocks[0]
                name = b0.get("name", "N/A")
                text = b0.get("text", "")[:120]
                print(f"  {rel}: name={name}, text={text}")
                samples_printed += 1
            
            total_checked += 1

print(f"\n=== Verification Results ===")
print(f"Files checked: {total_checked}")
print(f"Max display width: {max_overall}")
print(f"Hash mismatches GH/HA: {hash_mismatches}")
print(f"no_wrap failures: {nowrap_fails}")
print(f"CRLF in content: {crlf_fails}")
print(f"All pass: {hash_mismatches == 0 and nowrap_fails == 0 and crlf_fails == 0 and max_overall <= 42}")
