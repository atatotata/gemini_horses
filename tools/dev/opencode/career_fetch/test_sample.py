import sys, json
from pathlib import Path
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

extracted_blocks = []
for blk in block_list[1:]:
    tt = blk.get("TextTrack", {})
    clips = tt.get("ClipList", [])
    blk_name = ""
    blk_text = ""
    blk_choices = []
    
    for cinfo in clips:
        pid = cinfo.get("m_PathID")
        cobj = clip_objects.get(pid)
        if cobj:
            blk_name = cobj.get("Name", "")
            blk_text = cobj.get("Text", "")
            blk_choices = [ch.get("Text", "") for ch in cobj.get("ChoiceDataList", [])]
            
    extracted_blocks.append({
        "name": blk_name,
        "text": blk_text,
        "choice_data_list": blk_choices
    })

test_out = r"C:\TMP\opencode\career_fetch\sample_400001022.json"
with open(test_out, "w", encoding="utf-8", newline="\n") as f:
    json.dump({"no_wrap": True, "text_block_list": extracted_blocks}, f, ensure_ascii=False, indent=2)

print("Wrote successfully!")

# Read back and print raw hex or chars
with open(test_out, "r", encoding="utf-8") as f:
    loaded = json.load(f)
for i, b in enumerate(loaded["text_block_list"][:5]):
    print(f"Block {i}: name='{b['name']}', text_len={len(b['text'])}, choices={b['choice_data_list']}")
    # Print first 20 characters as repr
    print("  Repr:", repr(b['text'][:30]))
