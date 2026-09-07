import json
import hashlib
import os
from pathlib import Path

MSG_DICT_GEMINI = Path(r"G:/Games/steamapps/common/UmamusumePrettyDerby_Jpn/gemini_horses/localized_data/race_jikkyo_message_dict.json")
MSG_DICT_HACHIMI = Path(r"G:/Games/steamapps/common/UmamusumePrettyDerby_Jpn/hachimi/localized_data_1/race_jikkyo_message_dict.json")

with open(MSG_DICT_GEMINI, encoding="utf-8") as f:
    msg_dict = json.load(f)

# These 8 IDs have empty message text in master.mdb - add as empty string
empty_ids = ["1269", "2989", "5130", "5131", "5132", "5133", "5137", "5138"]
for eid in empty_ids:
    if eid not in msg_dict:
        msg_dict[eid] = ""
        print(f"Added empty msg[{eid}]")

print(f"Final msg_dict: {len(msg_dict)} keys")

# Write to both repos
def write_dict(path, data):
    tmp = str(path) + ".tmp"
    with open(tmp, "w", encoding="utf-8", newline="\n") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)
    os.replace(tmp, str(path))

write_dict(MSG_DICT_GEMINI, msg_dict)
write_dict(MSG_DICT_HACHIMI, msg_dict)

# Verify identical
def file_hash(p):
    with open(p, "rb") as f:
        return hashlib.md5(f.read()).hexdigest()

gh = file_hash(MSG_DICT_GEMINI)
hh = file_hash(MSG_DICT_HACHIMI)
print(f"msg_dict: gemini={gh}, hachimi={hh}, identical={gh==hh}")
