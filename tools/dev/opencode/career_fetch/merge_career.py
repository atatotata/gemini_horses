import os
import sys
import json
import time
from pathlib import Path
from concurrent.futures import ProcessPoolExecutor

ROOT_DIR = Path(r"C:/TMP/opencode/career_fetch")
STORY_JSON_DIR = ROOT_DIR / "story_json"
CHECKPOINT_PATH = ROOT_DIR / "career_checkpoint.json"

GAME_DIR = Path(r"G:/Games/steamapps/common/UmamusumePrettyDerby_Jpn")
GEMINI_DATA_DIR = GAME_DIR / "gemini_horses/localized_data/assets/story/data"
HACHIMI_DATA_DIR = GAME_DIR / "hachimi/localized_data_1/assets/story/data"

def sanitize_text(text: str) -> str:
    if not text:
        return text
    # Normalize double-escaped newlines
    text = text.replace(r"\n", "\n").replace(r"\r", "")
    return text

def process_file(task):
    # task: (rel_path, checkpoint_map)
    rel_path, checkpoint = task
    src_file = STORY_JSON_DIR / rel_path
    gemini_file = GEMINI_DATA_DIR / rel_path
    hachimi_file = HACHIMI_DATA_DIR / rel_path
    
    try:
        with open(src_file, "r", encoding="utf-8") as f:
            data = json.load(f)
            
        blocks = data.get("text_block_list", [])
        modified = 0
        
        for blk in blocks:
            n = blk.get("name")
            if n and n in checkpoint:
                blk["name"] = checkpoint[n]
                modified += 1
                
            t = blk.get("text", "")
            if t and t in checkpoint:
                blk["text"] = sanitize_text(checkpoint[t])
                modified += 1
                
            choices = blk.get("choice_data_list", [])
            new_choices = []
            for c in choices:
                if c in checkpoint:
                    new_choices.append(sanitize_text(checkpoint[c]))
                    modified += 1
                else:
                    new_choices.append(c)
            blk["choice_data_list"] = new_choices
            
        out_payload = {
            "no_wrap": True,
            "text_block_list": blocks
        }
        
        # Write to gemini_horses
        gemini_file.parent.mkdir(parents=True, exist_ok=True)
        with open(gemini_file, "w", encoding="utf-8", newline="\n") as f:
            json.dump(out_payload, f, ensure_ascii=False, indent=2)
            f.write("\n")
            
        # Write to hachimi
        hachimi_file.parent.mkdir(parents=True, exist_ok=True)
        with open(hachimi_file, "w", encoding="utf-8", newline="\n") as f:
            json.dump(out_payload, f, ensure_ascii=False, indent=2)
            f.write("\n")
            
        return True, modified
    except Exception as ex:
        return False, str(ex)

def main():
    t0 = time.time()
    print("Loading checkpoint...")
    with open(CHECKPOINT_PATH, "r", encoding="utf-8") as f:
        checkpoint = json.load(f)
    print(f"Loaded {len(checkpoint)} translations from checkpoint.")
    
    # Collect files
    file_list = []
    for root, dirs, files in os.walk(STORY_JSON_DIR):
        for f in files:
            if f.startswith("storytimeline_") and f.endswith(".json"):
                full_path = Path(root) / f
                rel = full_path.relative_to(STORY_JSON_DIR)
                file_list.append(rel)
                
    print(f"Total files to merge: {len(file_list)}")
    
    tasks = [(rel, checkpoint) for rel in file_list]
    
    workers = min(os.cpu_count() or 4, 8)
    print(f"Writing to gemini_horses & hachimi using {workers} processes...")
    
    success = 0
    total_mod = 0
    
    # Process sequentially or via chunked pool to avoid huge IPC
    for i, task in enumerate(tasks):
        ok, mod = process_file(task)
        if ok:
            success += 1
            total_mod += mod
        if (i + 1) % 2000 == 0 or (i + 1) == len(tasks):
            print(f"Merged {i+1}/{len(tasks)} files | Items updated: {total_mod}")
            
    t1 = time.time()
    print(f"\nMerge complete in {t1-t0:.1f}s!")
    print(f"Successfully merged {success} files across both repos.")

if __name__ == "__main__":
    main()
