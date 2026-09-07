import json, sys

bak_path = r"G:\Games\steamapps\common\UmamusumePrettyDerby_Jpn\hachimi\localized_data_1\text_data_dict.json.bak"
bak_data = json.load(open(bak_path, encoding="utf-8"))
bak_cat6 = bak_data.get("6", {})
print(f"Total in UmaTL bak cat 6: {len(bak_cat6)}")

cur_path = r"G:\Games\steamapps\common\UmamusumePrettyDerby_Jpn\gemini_horses\localized_data\text_data_dict.json"
cur_data = json.load(open(cur_path, encoding="utf-8"))
cur_cat6 = cur_data.get("6", {})

diffs = []
for k in sorted(cur_cat6.keys(), key=lambda x: int(x)):
    c_val = cur_cat6.get(k)
    b_val = bak_cat6.get(k)
    if b_val and c_val != b_val:
        diffs.append((k, c_val, b_val))

print(f"Diffs between current and original UmaTL: {len(diffs)}")
for k, c, b in diffs:
    print(f"ID {k}: current='{c}' vs UmaTL='{b}'")
