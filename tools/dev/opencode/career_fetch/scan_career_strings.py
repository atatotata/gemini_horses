import os
import sys
import json
import time
from pathlib import Path

GAME_DIR = Path(r"G:/Games/steamapps/common/UmamusumePrettyDerby_Jpn")
BIBLE_PATH = GAME_DIR / "gemini_horses/tools/voice_bible/uma_voice_bible.json"
STORY_JSON_DIR = Path(r"C:/TMP/opencode/career_fetch/story_json")
OUT_DIR = Path(r"C:/TMP/opencode/career_fetch")

def has_cjk(text: str) -> bool:
    if not text:
        return False
    return any(
        '\u3040' <= ch <= '\u30ff' or  # Hiragana, Katakana
        '\u4e00' <= ch <= '\u9fff' or  # CJK Unified Ideographs
        '\u3400' <= ch <= '\u4dbf'     # CJK Extension A
        for ch in text
    )

def main():
    t0 = time.time()
    print("Loading voice bible...")
    with open(BIBLE_PATH, "r", encoding="utf-8") as f:
        voice_bible = json.load(f)
        
    # Build JP -> EN lookup for all characters in voice bible
    name_lookup = {}
    for cid, info in voice_bible.items():
        name_lookup[info["jp"]] = info["en"]
        
    # Common generic names in Umamusume
    common_names = {
        "モノローグ": "Narrator",
        "ナレーション": "Narrator",
        "トレーナー": "Trainer",
        "実況": "Commentary",
        "解説": "Analysis",
        "観客": "Spectator",
        "観客A": "Spectator A",
        "観客B": "Spectator B",
        "観客たち": "Spectators",
        "ファン": "Fan",
        "記者": "Reporter",
        "記者たち": "Reporters",
        "記者A": "Reporter A",
        "記者B": "Reporter B",
        "クラスメイト": "Classmate",
        "クラスメイトA": "Classmate A",
        "クラスメイトB": "Classmate B",
        "ウマ娘": "Umamusume",
        "ウマ娘A": "Umamusume A",
        "ウマ娘B": "Umamusume B",
        "アナウンス": "Announcement",
        "理事長": "Chairwoman",
        "秋川理事長": "Chairwoman Akikawa",
        "駿川たづな": "Tazuna Hayakawa",
        "桐生院葵": "Aoi Kiryuin",
        "樫本理子": "Riko Kashimoto",
        "安心沢刺々美": "Sasami Anshinzawa",
        "乙名史記者": "Reporter Otonashi",
        "女性": "Woman",
        "男性": "Man",
        "店員": "Clerk",
        "店主": "Shopkeeper",
        "子供": "Child",
        "少年": "Boy",
        "少女": "Girl",
        "<username>": "<username>"
    }
    name_lookup.update(common_names)
    
    print("Scanning all 14,138 story files...")
    
    total_files = 0
    total_blocks = 0
    name_hits = 0
    unresolved_names = set()
    unique_choices = set()
    unique_dialogues = set()
    
    for root, dirs, files in os.walk(STORY_JSON_DIR):
        for f in files:
            if f.startswith("storytimeline_") and f.endswith(".json"):
                total_files += 1
                fpath = os.path.join(root, f)
                try:
                    with open(fpath, "r", encoding="utf-8") as jf:
                        data = json.load(jf)
                    blocks = data.get("text_block_list", [])
                    total_blocks += len(blocks)
                    for blk in blocks:
                        n = blk.get("name")
                        if n:
                            if n in name_lookup:
                                name_hits += 1
                            elif has_cjk(n):
                                unresolved_names.add(n)
                        t = blk.get("text", "")
                        if t and has_cjk(t):
                            unique_dialogues.add(t)
                        for c in blk.get("choice_data_list", []):
                            if c and has_cjk(c):
                                unique_choices.add(c)
                except Exception as ex:
                    print(f"Error reading {f}: {ex}")
                    
    t1 = time.time()
    print(f"\nScan completed in {t1-t0:.1f}s!")
    print(f"Total files: {total_files}")
    print(f"Total dialogue blocks: {total_blocks}")
    print(f"Pre-resolved speaker names: {name_hits}")
    print(f"Unresolved speaker names needing translation: {len(unresolved_names)}")
    print(f"Unique player choices: {len(unique_choices)}")
    print(f"Unique dialogue texts: {len(unique_dialogues)}")
    print(f"Total unique strings needing translation: {len(unresolved_names) + len(unique_choices) + len(unique_dialogues)}")
    
    # Save work queues
    stats = {
        "total_files": total_files,
        "total_blocks": total_blocks,
        "pre_resolved_names_count": len(name_lookup),
        "unresolved_names_count": len(unresolved_names),
        "unique_choices_count": len(unique_choices),
        "unique_dialogues_count": len(unique_dialogues),
        "total_unique_items": len(unresolved_names) + len(unique_choices) + len(unique_dialogues)
    }
    with open(OUT_DIR / "scan_stats.json", "w", encoding="utf-8") as f:
        json.dump(stats, f, indent=2)
        
    with open(OUT_DIR / "pre_resolved_names.json", "w", encoding="utf-8") as f:
        json.dump(name_lookup, f, ensure_ascii=False, indent=2)
        
    with open(OUT_DIR / "unresolved_names.json", "w", encoding="utf-8") as f:
        json.dump(sorted(list(unresolved_names)), f, ensure_ascii=False, indent=2)
        
    with open(OUT_DIR / "unique_choices.json", "w", encoding="utf-8") as f:
        json.dump(sorted(list(unique_choices)), f, ensure_ascii=False, indent=2)
        
    with open(OUT_DIR / "unique_dialogues.json", "w", encoding="utf-8") as f:
        json.dump(sorted(list(unique_dialogues)), f, ensure_ascii=False, indent=2)
        
    print(f"Saved work queues to {OUT_DIR}")

if __name__ == "__main__":
    main()
