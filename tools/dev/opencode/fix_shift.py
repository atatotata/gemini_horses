import json, glob, os

repos = [
    ("gemini_horses", r"G:\Games\steamapps\common\UmamusumePrettyDerby_Jpn\gemini_horses\localized_data\assets\story\data"),
    ("hachimi", r"G:\Games\steamapps\common\UmamusumePrettyDerby_Jpn\hachimi\localized_data_1\assets\story\data")
]

for name, base_path in repos:
    print(f"--- Processing {name} ---")
    files = glob.glob(f"{base_path}/**/*.json", recursive=True)
    modified_count = 0
    skipped_count = 0
    
    for f in files:
        try:
            with open(f, "r", encoding="utf-8") as jf:
                data = json.load(jf)
                
            tbl = data.get("text_block_list", [])
            if tbl:
                first = tbl[0]
                # If first block is empty (no name, no text)
                if not first or (not first.get("name") and not first.get("text")):
                    data["text_block_list"] = tbl[1:]
                    with open(f, "w", encoding="utf-8", newline="\n") as jf:
                        json.dump(data, jf, ensure_ascii=False, indent=2)
                    modified_count += 1
                else:
                    skipped_count += 1
        except Exception as e:
            print(f"Error processing {f}: {e}")
            
    print(f"{name}: Modified {modified_count} files, Skipped {skipped_count} files (already non-empty first block)")
