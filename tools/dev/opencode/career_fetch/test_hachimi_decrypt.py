import sys, json
from pathlib import Path
import UnityPy

GAME_DIR = Path(r"G:/Games/steamapps/common/UmamusumePrettyDerby_Jpn")
DAT_DIR = GAME_DIR / "UmamusumePrettyDerby_Jpn_Data/Persistent/dat"
sys.path.insert(0, str(GAME_DIR / "gemini_horses/tools/hachimi-tools"))
from decrypt import decrypt_asset_bundle

tasks = json.load(open(r"C:\TMP\opencode\career_fetch\tasks.json"))
sid, n, h, e, out_json = tasks[0]

bundle_path = DAT_DIR / h[:2] / h
with open(bundle_path, "rb") as f:
    data = f.read()

dec_bytes = decrypt_asset_bundle(data, e)
env = UnityPy.load(dec_bytes)

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

print(f"Total extracted blocks: {len(extracted_blocks)}")
for i, b in enumerate(extracted_blocks[:5]):
    print(f"Block {i}: name='{b['name']}', choices={b['choice_data_list']}")
    import sys
    sys.stdout.buffer.write(f"  Text: {b['text'][:30]}\n".encode('utf-8'))
