import sys
from pathlib import Path
import json
import UnityPy

GAME_DIR = Path(r"G:/Games/steamapps/common/UmamusumePrettyDerby_Jpn")
DAT_DIR = GAME_DIR / "UmamusumePrettyDerby_Jpn_Data/Persistent/dat"
sys.path.insert(0, str(GAME_DIR / "gemini_horses/tools/umamusu-utils/scripts"))
from utils import _derive_asset_key

tasks = json.load(open(r"C:\TMP\opencode\career_fetch\tasks.json"))
sid, n, h, e, out_json = tasks[0]

bundle_path = DAT_DIR / h[:2] / h
with open(bundle_path, "rb") as f:
    data = bytearray(f.read())

dec_key = _derive_asset_key(e)
klen = len(dec_key)
for j in range(256, len(data)):
    data[j] ^= dec_key[j % klen]

env = UnityPy.load(bytes(data))

clip_objects = {}
story_data_obj = None

for obj in env.objects:
    if obj.type.name == "MonoBehaviour":
        try:
            tree = obj.read_typetree()
            if "BlockList" in tree:
                story_data_obj = tree
            elif "Text" in tree and "ChoiceDataList" in tree:
                clip_objects[obj.path_id] = tree
        except Exception:
            pass

block_list = story_data_obj.get("BlockList", [])
print("Total blocks:", len(block_list))

extracted_blocks = []
for blk in block_list[1:]:
    tt = blk.get("TextTrack", {})
    clips = tt.get("ClipList", [])
    blk_name = None
    blk_text = ""
    choices = []
    
    for c_ref in clips:
        pid = c_ref.get("m_PathID")
        clip_data = clip_objects.get(pid)
        if clip_data:
            cname = clip_data.get("Name")
            if cname is not None and cname != "":
                blk_name = cname
            ctext = clip_data.get("Text", "")
            if ctext:
                blk_text = ctext if not blk_text else blk_text + "\n" + ctext
            for c_item in clip_data.get("ChoiceDataList", []):
                ct = c_item.get("Text", "")
                if ct:
                    choices.append(ct)
                    
    extracted_blocks.append({
        "name": blk_name,
        "text": blk_text,
        "choice_data_list": choices
    })

print(f"Extracted {len(extracted_blocks)} blocks:")
for i, b in enumerate(extracted_blocks[:5]):
    print(f"Block {i}: name={b['name']}, text={b['text'][:40]}..., choices={b['choice_data_list']}")
