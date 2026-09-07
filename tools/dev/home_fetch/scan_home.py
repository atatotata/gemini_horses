#!/usr/bin/env python3
"""
Step 1: Scan 938 home timeline JSONs, dedupe, pre-resolve names from voice bible.
Output: work queues + scan_home.json
"""
import json, os, re
from pathlib import Path

HOME_SRC = Path(r"C:/TMP/home_fetch/story_json/home/data")
VOICE_BIBLE = Path(r"G:/Games/steamapps/common/UmamusumePrettyDerby_Jpn/gemini_horses/tools/voice_bible/uma_voice_bible.json")
SCAN_OUT = Path(r"C:/TMP/home_fetch/scan_home.json")
PRE_RESOLVED_OUT = Path(r"C:/TMP/home_fetch/home_pre_resolved_names.json")
UNRESOLVED_OUT = Path(r"C:/TMP/home_fetch/home_unresolved_names.json")
DIALOGUES_OUT = Path(r"C:/TMP/home_fetch/home_unique_dialogues.json")

# Known NPC / common label translations
NPC_NAMES = {
    "モノローグ": "Narrator",
    "イベントスタッフ": "Event Staff",
    "インタビュアー": "Interviewer",
    "観客": "Spectator",
    " Reporter オトナシ": "Reporter Otonashi",
    "オトナシ": "Otonashi",
    "報導者オトナシ": "Reporter Otonashi",
    "インタビュア": "Interviewer",
    "園田管理人": "Sonoda Manager",
    "管理人": "Manager",
    "ウマ娘たち": "Umamusume",
    "レポーター": "Reporter",
    "アナウンサー": "Announcer",
    "司会者": "Announcer",
    "先生": "Sensei",
    "トレーナー": "Trainer",
}

def norm_crlf(s: str) -> str:
    return s.replace("\r\n", "\n").replace("\r", "\n")

def build_voice_map():
    """Load voice bible -> {jp_name: en_name}"""
    with open(VOICE_BIBLE, "r", encoding="utf-8") as f:
        bible = json.load(f)
    vmap = {}
    for uid, entry in bible.items():
        jp = entry.get("jp", "")
        en = entry.get("en", "")
        if jp and en:
            vmap[jp] = en
    return vmap

def main():
    print("=== Home Timeline Scan ===")
    
    # Load voice bible
    voice_map = build_voice_map()
    print(f"Voice bible loaded: {len(voice_map)} characters")
    
    # Merge NPC + voice bible for name resolution
    name_resolution = {}
    name_resolution.update(NPC_NAMES)
    name_resolution.update(voice_map)
    
    # Scan all JSON files
    all_files = list(HOME_SRC.rglob("hometimeline_*.json"))
    print(f"Found {len(all_files)} hometimeline JSON files")
    
    # Collect unique strings
    all_names = set()
    all_dialogues = set()
    all_titles = set()
    file_structures = {}  # filename -> [{name_idx, text_idx, title?}, ...]
    
    total_blocks = 0
    for fi, fp in enumerate(all_files):
        with open(fp, "r", encoding="utf-8") as f:
            data = json.load(f)
        
        rel = fp.relative_to(HOME_SRC)
        blocks_info = []
        
        # Title
        title = data.get("title", "")
        if title:
            title = norm_crlf(title)
            all_titles.add(title)
        
        for block in data.get("text_block_list", []):
            name = norm_crlf(block.get("name", ""))
            text = norm_crlf(block.get("text", ""))
            
            if name:
                all_names.add(name)
            if text:
                all_dialogues.add(text)
            
            blocks_info.append({
                "name": name,
                "text": text,
            })
            total_blocks += 1
        
        file_structures[str(rel)] = {
            "title": title,
            "blocks": blocks_info,
        }
    
    print(f"Total blocks: {total_blocks}")
    print(f"Unique names: {len(all_names)}")
    print(f"Unique dialogues: {len(all_dialogues)}")
    print(f"Unique titles: {len(all_titles)}")
    
    # Pre-resolve names from voice bible + NPC
    pre_resolved = {}
    unresolved_names = []
    
    for name in sorted(all_names):
        if not name:
            continue
        if name in name_resolution:
            pre_resolved[name] = name_resolution[name]
        else:
            unresolved_names.append(name)
    
    print(f"\nPre-resolved names: {len(pre_resolved)}")
    for jp, en in sorted(pre_resolved.items())[:20]:
        print(f"  {jp} -> {en}")
    if len(pre_resolved) > 20:
        print(f"  ... and {len(pre_resolved) - 20} more")
    
    print(f"Unresolved names: {len(unresolved_names)}")
    for n in unresolved_names[:20]:
        print(f"  {n}")
    
    # Pre-resolve titles (usually numeric strings like "0", "1" etc. - keep as-is or resolve)
    # Titles in home files are typically "0", "1" etc. - skip translating those
    title_resolved = {}
    title_unresolved = []
    for t in sorted(all_titles):
        if t.isdigit():
            title_resolved[t] = t  # Keep numeric titles as-is
        else:
            title_unresolved.append(t)
    
    # Write outputs
    print(f"\nWriting outputs...")
    
    # Pre-resolved names (voice bible + NPC)
    with open(PRE_RESOLVED_OUT, "w", encoding="utf-8") as f:
        json.dump(pre_resolved, f, ensure_ascii=False, indent=1)
    print(f"  {PRE_RESOLVED_OUT} ({len(pre_resolved)} entries)")
    
    # Unresolved names (need API translation)
    with open(UNRESOLVED_OUT, "w", encoding="utf-8") as f:
        json.dump(unresolved_names, f, ensure_ascii=False, indent=1)
    print(f"  {UNRESOLVED_OUT} ({len(unresolved_names)} entries)")
    
    # Unique dialogues
    dialogues_list = sorted(all_dialogues)
    with open(DIALOGUES_OUT, "w", encoding="utf-8") as f:
        json.dump(dialogues_list, f, ensure_ascii=False, indent=1)
    print(f"  {DIALOGUES_OUT} ({len(dialogues_list)} entries)")
    
    # Full scan manifest
    scan = {
        "total_files": len(all_files),
        "total_blocks": total_blocks,
        "unique_names": len(all_names),
        "unique_dialogues": len(all_dialogues),
        "unique_titles": len(all_titles),
        "pre_resolved_count": len(pre_resolved),
        "unresolved_names_count": len(unresolved_names),
        "title_resolved_count": len(title_resolved),
        "title_unresolved_count": len(title_unresolved),
        "file_structures": file_structures,
    }
    with open(SCAN_OUT, "w", encoding="utf-8") as f:
        json.dump(scan, f, ensure_ascii=False, indent=1)
    print(f"  {SCAN_OUT}")
    
    # Summary
    total_uniques = len(pre_resolved) + len(unresolved_names) + len(dialogues_list)
    print(f"\n=== SUMMARY ===")
    print(f"Files: {len(all_files)}")
    print(f"Blocks: {total_blocks}")
    print(f"Pre-resolved names (voice bible): {len(pre_resolved)}")
    print(f"Unresolved names (need API): {len(unresolved_names)}")
    print(f"Unique dialogues: {len(dialogues_list)}")
    print(f"Total unique strings to translate: {len(unresolved_names) + len(dialogues_list)}")
    print(f"Estimated batches (50/batch): {(len(unresolved_names) + len(dialogues_list)) // 50 + 1}")
    print(f"Done.")

if __name__ == "__main__":
    main()
