#!/usr/bin/env python3
"""
Scan 4,280 story JSON files → categorize unique names/dialogues/choices.
Load pre-resolved names from voice bible + home_checkpoint.
Output scan_remaining.json with unresolved names, unique dialogues, unique choices.
"""
import json, os, sys
from pathlib import Path

ROOT_DIR = Path(r"C:/TMP/remaining_fetch")
STORY_SRC = ROOT_DIR / "story_json"
SCAN_OUT = ROOT_DIR / "scan_remaining.json"
VOICE_BIBLE = Path(r"G:/Games/steamapps/common/UmamusumePrettyDerby_Jpn/gemini_horses/tools/voice_bible/uma_voice_bible.json")
HOME_CHECKPOINT = Path(r"C:/TMP/home_fetch/home_checkpoint.json")

def main():
    # Load voice bible → jp->en
    vb = json.load(open(VOICE_BIBLE, "r", encoding="utf-8"))
    bible = {v["jp"]: v["en"] for v in vb.values() if "jp" in v and "en" in v}
    print(f"Voice bible: {len(bible)} entries")

    # Load home checkpoint
    hc = json.load(open(HOME_CHECKPOINT, "r", encoding="utf-8"))
    print(f"Home checkpoint: {len(hc)} entries")

    # Scan all files
    names = set()
    texts = set()
    choices = set()
    total_blocks = 0
    total_choices = 0
    file_count = 0

    for r, ds, fs in os.walk(STORY_SRC):
        for f in fs:
            if not f.endswith(".json"):
                continue
            file_count += 1
            fp = os.path.join(r, f)
            try:
                d = json.load(open(fp, "r", encoding="utf-8"))
                for blk in d.get("text_block_list", []):
                    total_blocks += 1
                    if blk.get("name"):
                        names.add(blk["name"])
                    if blk.get("text"):
                        texts.add(blk["text"])
                    for c in (blk.get("choice_data_list") or []):
                        total_choices += 1
                        choices.add(c)
            except Exception as e:
                print(f"  WARN: {fp}: {e}")

    print(f"\nFiles: {file_count}")
    print(f"Total blocks: {total_blocks}")
    print(f"Unique names: {len(names)}")
    print(f"Unique texts: {len(texts)}")
    print(f"Total choices: {total_choices}")
    print(f"Unique choices: {len(choices)}")

    # Categorize names
    resolved_names = {}  # jp -> en (bible + home_checkpoint)
    unresolved_names = []
    for n in sorted(names):
        if n in bible:
            resolved_names[n] = bible[n]
        elif n in hc:
            resolved_names[n] = hc[n]
        else:
            unresolved_names.append(n)

    print(f"Resolved names (bible+hk): {len(resolved_names)}")
    print(f"Unresolved names: {len(unresolved_names)}")
    print(f"Unique texts to translate: {len(texts)}")
    print(f"Unique choices to translate: {len(choices)}")
    total_to_translate = len(texts) + len(choices)
    print(f"Total unique strings: {total_to_translate}")

    scan = {
        "file_count": file_count,
        "total_blocks": total_blocks,
        "total_choices": total_choices,
        "resolved_names": resolved_names,
        "unresolved_names": unresolved_names,
        "unique_texts": sorted(texts),
        "unique_choices": sorted(choices),
    }

    with open(SCAN_OUT, "w", encoding="utf-8") as f:
        json.dump(scan, f, ensure_ascii=False, indent=1)
    print(f"\nWrote {SCAN_OUT}")

if __name__ == "__main__":
    main()
