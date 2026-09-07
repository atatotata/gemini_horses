"""
Scan 198 new 09 files, dedup unique strings, output work queues.
Exclude: 90016001, 90021001, 90032001, 90054007 (already translated+merged).
"""
import os
import json
import re
from pathlib import Path

ROOT_DIR = Path(r"C:/TMP/extra_fetch")
STORY_DIR = ROOT_DIR / "story_json" / "09"
VOICE_BIBLE = Path(r"G:/Games/steamapps/common/UmamusumePrettyDerby_Jpn/gemini_horses/tools/voice_bible/uma_voice_bible.json")
CHECKPOINT_PATH = ROOT_DIR / "extra_checkpoint.json"

EXCLUDE_SIDS = {"90016001", "90021001", "90032001", "90054007"}

def load_voice_bible():
    """Return {jp_name: en_name} mapping from voice bible."""
    with open(VOICE_BIBLE, encoding="utf-8") as f:
        bible = json.load(f)
    mapping = {}
    for key, entry in bible.items():
        if isinstance(entry, dict) and "jp" in entry and "en" in entry:
            mapping[entry["jp"]] = entry["en"]
    return mapping

def load_checkpoint():
    with open(CHECKPOINT_PATH, encoding="utf-8") as f:
        return json.load(f)

def normalize_text(text):
    """Normalize CRLF/whitespace for consistent key lookup."""
    # Convert \r\n to \n for consistent lookup
    text = text.replace("\r\n", "\n").replace("\r", "\n")
    # Strip trailing whitespace per line
    lines = [line.rstrip() for line in text.split("\n")]
    return "\n".join(lines)

def strip_tags(text):
    """Strip HTML/XML tags for display-width measurement."""
    return re.sub(r'<[^>]+>', '', text)

def main():
    bible = load_voice_bible()
    checkpoint = load_checkpoint()
    
    # Collect all 09 files, excluding the 4 already merged
    all_files = []
    for subdir in sorted(os.listdir(STORY_DIR)):
        sub_path = STORY_DIR / subdir
        if not sub_path.is_dir():
            continue
        for fname in sorted(os.listdir(sub_path)):
            if not fname.startswith("storytimeline_") or not fname.endswith(".json"):
                continue
            sid = fname.replace("storytimeline_", "").replace(".json", "")
            if sid in EXCLUDE_SIDS:
                print(f"  SKIP (already merged): {sid}")
                continue
            all_files.append({
                "sid": sid,
                "sub": subdir,
                "path": str(sub_path / fname),
            })
    
    print(f"\nTotal 09 files: 202, Excluded: {len(EXCLUDE_SIDS)}, Remaining: {len(all_files)}")
    
    # Scan all files
    unique_names = {}     # jp_name -> count
    unique_dialogues = {} # jp_text -> count  
    unique_choices = {}   # jp_choice -> count
    
    total_blocks = 0
    total_choices = 0
    
    for finfo in all_files:
        with open(finfo["path"], encoding="utf-8") as f:
            data = json.load(f)
        
        blocks = data.get("text_block_list", [])
        for block in blocks:
            name = block.get("name", "")
            text = block.get("text", "")
            
            if name:
                nn = normalize_text(name)
                unique_names[nn] = unique_names.get(nn, 0) + 1
            
            if text:
                nt = normalize_text(text)
                unique_dialogues[nt] = unique_dialogues.get(nt, 0) + 1
            
            choices = block.get("choice_data_list", [])
            if choices:
                for ch in choices:
                    # choice_data_list items can be strings or dicts
                    if isinstance(ch, str):
                        ct = ch
                    elif isinstance(ch, dict):
                        ct = ch.get("text", "")
                    else:
                        continue
                    if ct:
                        nc = normalize_text(ct)
                        unique_choices[nc] = unique_choices.get(nc, 0) + 1
                        total_choices += 1
            
            total_blocks += 1
    
    print(f"Scanned: {len(all_files)} files, {total_blocks} blocks, {total_choices} choices")
    print(f"Unique names: {len(unique_names)}")
    print(f"Unique dialogues: {len(unique_dialogues)}")
    print(f"Unique choices: {len(unique_choices)}")
    
    # Pre-resolve names: check bible + checkpoint
    pre_resolved = {}
    unresolved_names = {}
    for jp_name, count in unique_names.items():
        if jp_name in checkpoint:
            pre_resolved[jp_name] = checkpoint[jp_name]
        elif jp_name in bible:
            pre_resolved[jp_name] = bible[jp_name]
        else:
            unresolved_names[jp_name] = count
    
    # Pre-resolve dialogues: check checkpoint
    already_resolved_dialogues = {}
    unresolved_dialogues = {}
    for jp_text, count in unique_dialogues.items():
        if jp_text in checkpoint:
            already_resolved_dialogues[jp_text] = checkpoint[jp_text]
        else:
            unresolved_dialogues[jp_text] = count
    
    # Pre-resolve choices: check checkpoint
    already_resolved_choices = {}
    unresolved_choices = {}
    for jp_choice, count in unique_choices.items():
        if jp_choice in checkpoint:
            already_resolved_choices[jp_choice] = checkpoint[jp_choice]
        else:
            unresolved_choices[jp_choice] = count
    
    print(f"\nPre-resolved names (bible/checkpoint): {len(pre_resolved)}")
    print(f"Unresolved names: {len(unresolved_names)}")
    print(f"Already resolved dialogues (checkpoint): {len(already_resolved_dialogues)}")
    print(f"Unresolved dialogues: {len(unresolved_dialogues)}")
    print(f"Already resolved choices (checkpoint): {len(already_resolved_choices)}")
    print(f"Unresolved choices: {len(unresolved_choices)}")
    
    total_unresolved = len(unresolved_names) + len(unresolved_dialogues) + len(unresolved_choices)
    print(f"\nTotal unresolved unique strings: {total_unresolved}")
    estimated_batches = (total_unresolved + 49) // 50
    print(f"Estimated batches (50 per batch): ~{estimated_batches}")
    
    # Save work queues
    unresolved_names_list = list(unresolved_names.keys())
    unresolved_dialogues_list = list(unresolved_dialogues.keys())
    unresolved_choices_list = list(unresolved_choices.keys())
    
    with open(ROOT_DIR / "unresolved_names_09.json", "w", encoding="utf-8") as f:
        json.dump(unresolved_names_list, f, ensure_ascii=False, indent=1)
    with open(ROOT_DIR / "unique_dialogues_09.json", "w", encoding="utf-8") as f:
        json.dump(unresolved_dialogues_list, f, ensure_ascii=False, indent=1)
    with open(ROOT_DIR / "unique_choices_09.json", "w", encoding="utf-8") as f:
        json.dump(unresolved_choices_list, f, ensure_ascii=False, indent=1)
    
    # Save pre-resolved names for checkpoint seeding
    pre_resolved_names = {}
    for jp_name in unique_names:
        if jp_name in pre_resolved:
            pre_resolved_names[jp_name] = pre_resolved[jp_name]
    with open(ROOT_DIR / "pre_resolved_names_09.json", "w", encoding="utf-8") as f:
        json.dump(pre_resolved_names, f, ensure_ascii=False, indent=1)
    
    # Save scan results
    scan_result = {
        "total_files": len(all_files),
        "total_blocks": total_blocks,
        "total_choices": total_choices,
        "unique_names": len(unique_names),
        "unique_dialogues": len(unique_dialogues),
        "unique_choices": len(unique_choices),
        "pre_resolved_names": len(pre_resolved_names),
        "unresolved_names": len(unresolved_names),
        "unresolved_dialogues": len(unresolved_dialogues),
        "unresolved_choices": len(unresolved_choices),
        "total_unresolved": total_unresolved,
        "estimated_batches": estimated_batches,
        "sids": [f["sid"] for f in all_files],
    }
    with open(ROOT_DIR / "scan_09_remaining.json", "w", encoding="utf-8") as f:
        json.dump(scan_result, f, ensure_ascii=False, indent=2)
    
    # Show some unresolved names sample
    if unresolved_names:
        print(f"\nSample unresolved names:")
        for i, (n, c) in enumerate(sorted(unresolved_names.items(), key=lambda x: -x[1])[:20]):
            print(f"  {n} (x{c})")
    
    print(f"\nWork queues saved to {ROOT_DIR}")
    print(f"Scan complete.")

if __name__ == "__main__":
    main()
