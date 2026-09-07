import json, glob, sys

# Let's check 041141007 vs other files
f1 = r"G:\Games\steamapps\common\UmamusumePrettyDerby_Jpn\hachimi\localized_data_1\assets\story\data\04\1141\storytimeline_041141007.json"
d1 = json.load(open(f1, encoding="utf-8"))
print("041141007 blocks:", len(d1["text_block_list"]))
for i in range(min(6, len(d1["text_block_list"]))):
    print(f"  041141007[{i}]:", d1["text_block_list"][i])

f0 = r"G:\Games\steamapps\common\UmamusumePrettyDerby_Jpn\hachimi\localized_data_1\assets\story\data\04\1001\storytimeline_041001001.json"
d0 = json.load(open(f0, encoding="utf-8"))
print("041001001 blocks:", len(d0["text_block_list"]))
for i in range(min(6, len(d0["text_block_list"]))):
    print(f"  041001001[{i}]:", d0["text_block_list"][i])
