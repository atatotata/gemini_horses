#!/usr/bin/env python3
"""Examine existing story JSON format."""
import json

path = r"G:\Games\steamapps\common\UmamusumePrettyDerby_Jpn\gemini_horses\localized_data\assets\story\data\50\1001\storytimeline_501001100.json"
with open(path, "r", encoding="utf-8") as f:
    d = json.load(f)
print("Keys:", list(d.keys()))
print("Title:", d.get("title", "N/A"))
print("no_wrap:", d.get("no_wrap", "N/A"))
if "text_block_list" in d:
    print("text_block_list len:", len(d["text_block_list"]))
    if d["text_block_list"]:
        first = d["text_block_list"][0]
        print("First block keys:", list(first.keys()))
        print("First block:", json.dumps(first, ensure_ascii=False, indent=2)[:1000])
    # Check for choices
    for i, blk in enumerate(d["text_block_list"][:20]):
        if blk.get("choice_data_list"):
            print(f"Block {i} has choices: {blk['choice_data_list']}")
            break
