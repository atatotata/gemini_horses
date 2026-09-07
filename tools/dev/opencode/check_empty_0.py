import json, glob

for repo, base in [
    ("gemini_horses", r"G:\Games\steamapps\common\UmamusumePrettyDerby_Jpn\gemini_horses\localized_data\assets\story\data"),
    ("hachimi", r"G:\Games\steamapps\common\UmamusumePrettyDerby_Jpn\hachimi\localized_data_1\assets\story\data")
]:
    files = glob.glob(f"{base}/**/*.json", recursive=True)
    empty_0 = []
    for f in files:
        try:
            d = json.load(open(f, encoding="utf-8"))
            tbl = d.get("text_block_list", [])
            if tbl and (not tbl[0] or (not tbl[0].get("text") and not tbl[0].get("name"))):
                empty_0.append(f)
        except:
            pass
    print(f"{repo}: total files = {len(files)}, with empty block[0] = {len(empty_0)}")
