import json, glob, os, re

canonical_fixes = {
    "1026": ("ミホノブルボン", "Mihono Bourbon", ["Miho no Bourbon"]),
    "1038": ("カレンチャン", "Curren Chan", ["Karen Chan", "Karen-chan"]),
    "1048": ("トーセンジョーダン", "Tosen Jordan", ["Toosen Jordan"]),
    "1056": ("マチカネフクキタル", "Matikanefukukitaru", ["Machikane Fukukitaru", "Machikanefukukitaru"]),
    "1062": ("マチカネタンホイザ", "Matikanetannhauser", ["Machikane Tannhauser", "Machikanetannhauser"]),
    "1103": ("ロイスアンドロイス", "Royce and Royce", ["Lois and Loyce", "Royce & Royce"]),
    "1109": ("ラインクラフト", "Rhein Kraft", ["Line Craft"]),
    "1112": ("デアリングハート", "Daring Heart", ["Dearing Heart"]),
    "1124": ("バブルガムフェロー", "Bubble Gum Fellow", ["Bubblegum Fellow"]),
    "1127": ("フェノーメノ", "Fenomeno", ["Phenomeno"]),
    "1146": ("エフフォーリア", "Efforia", ["Euphoria"]),
    "2002": ("ビターグラッセ", "Bitter Glasse", ["Bitter Glace"]),
    "2006": ("リガントーナ", "Rigauntona", ["Rigantona"]),
    "9050": ("保科健子", "Takeshi Hoshina", ["Keiko Hoshina"])
}

# 1. Update uma_voice_bible.json
vb_path = r"G:\Games\steamapps\common\UmamusumePrettyDerby_Jpn\gemini_horses\tools\voice_bible\uma_voice_bible.json"
with open(vb_path, "r", encoding="utf-8") as f:
    vb = json.load(f)

for cid, (jp, canonical, _) in canonical_fixes.items():
    if cid in vb:
        vb[cid]["en"] = canonical
        vb[cid]["jp"] = jp

with open(vb_path, "w", encoding="utf-8", newline="\n") as f:
    json.dump(vb, f, ensure_ascii=False, indent=2)
print("Updated uma_voice_bible.json successfully.")

# 2. Update text_data_dict.json in both repos
td_paths = [
    r"G:\Games\steamapps\common\UmamusumePrettyDerby_Jpn\gemini_horses\localized_data\text_data_dict.json",
    r"G:\Games\steamapps\common\UmamusumePrettyDerby_Jpn\hachimi\localized_data_1\text_data_dict.json"
]

for tdp in td_paths:
    with open(tdp, "r", encoding="utf-8") as f:
        td = json.load(f)
    if "6" in td:
        for cid, (jp, canonical, _) in canonical_fixes.items():
            td["6"][cid] = canonical
    with open(tdp, "w", encoding="utf-8", newline="\n") as f:
        json.dump(td, f, ensure_ascii=False, indent=2)
    print(f"Updated text_data_dict.json at {tdp}")

# 3. Replace wrong names in story files across both repos
story_dirs = [
    r"G:\Games\steamapps\common\UmamusumePrettyDerby_Jpn\gemini_horses\localized_data\assets\story\data",
    r"G:\Games\steamapps\common\UmamusumePrettyDerby_Jpn\hachimi\localized_data_1\assets\story\data"
]

# Replacement pairs: (old_word, new_word)
# We only replace whole words or exact speaker names
replacements = []
for cid, (jp, canonical, old_variants) in canonical_fixes.items():
    for ov in old_variants:
        replacements.append((ov, canonical))

print(f"Replacements to apply: {replacements}")

for sdir in story_dirs:
    mod_files = 0
    total_replaces = 0
    files = glob.glob(f"{sdir}/**/*.json", recursive=True)
    for f in files:
        try:
            with open(f, "r", encoding="utf-8") as jf:
                data = json.load(jf)
            
            file_changed = False
            for b in data.get("text_block_list", []):
                # check speaker name
                name = b.get("name")
                if name:
                    for old_v, canon in replacements:
                        if name == old_v:
                            b["name"] = canon
                            file_changed = True
                            total_replaces += 1
                        elif old_v in name:
                            # e.g. "Euphoria's Trainer" -> "Efforia's Trainer"
                            b["name"] = re.sub(r'\b' + re.escape(old_v) + r'\b', canon, name)
                            if b["name"] != name:
                                file_changed = True
                                total_replaces += 1
                                
                # check dialogue text
                text = b.get("text")
                if text:
                    for old_v, canon in replacements:
                        if old_v in text:
                            # regex word boundary
                            new_text = re.sub(r'\b' + re.escape(old_v) + r'\b', canon, text)
                            if new_text != text:
                                b["text"] = new_text
                                file_changed = True
                                total_replaces += 1
                                
                # check choice_data_list
                choices = b.get("choice_data_list")
                if choices:
                    new_choices = []
                    for ch in choices:
                        ch_text = ch
                        for old_v, canon in replacements:
                            if old_v in ch_text:
                                ch_text = re.sub(r'\b' + re.escape(old_v) + r'\b', canon, ch_text)
                                file_changed = True
                                total_replaces += 1
                        new_choices.append(ch_text)
                    b["choice_data_list"] = new_choices
                    
            if file_changed:
                with open(f, "w", encoding="utf-8", newline="\n") as jf:
                    json.dump(data, jf, ensure_ascii=False, indent=2)
                mod_files += 1
        except Exception as e:
            print(f"Error in {f}: {e}")
            
    print(f"{sdir}: Modified {mod_files} files with {total_replaces} replacements.")
