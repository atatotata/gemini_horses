import UnityPy, sys, json

env = UnityPy.load("C:/TMP/opencode/chara_fetch/dec/UBCZ4MQTEW2PWB2GYJGGILW5YFX36FII")
clip_objects = {}
root = None

for obj in env.objects:
    if obj.type.name == "MonoBehaviour":
        data = obj.read_typetree()
        if "BlockList" in data:
            root = data
        elif "Text" in data or "ChoiceDataList" in data:
            clip_objects[obj.path_id] = data

b3 = root["BlockList"][3]
print("Block 3 keys:", b3.keys())
for k, v in b3.items():
    if isinstance(v, dict) and "ClipList" in v:
        clips = v.get("ClipList", [])
        print(f"  Track {k} has {len(clips)} clips:")
        for c in clips:
            pid = c.get("m_PathID")
            co = clip_objects.get(pid, {})
            if co:
                print(f"    pid={pid}: text={co.get('Text')}, choices={co.get('ChoiceDataList')}")

# Also search ALL clip_objects in the entire bundle for "ラストスパ"
print("\nSearching ALL clip_objects for ラストスパ:")
for pid, co in clip_objects.items():
    t = str(co.get("Text") or "")
    cdl = str(co.get("ChoiceDataList") or "")
    if "ラストスパ" in t or "ラストスパ" in cdl:
        print(f"Found in pid={pid}:")
        print(f"  Name: {co.get('Name')}")
        print(f"  Text: {co.get('Text')}")
        print(f"  Choices: {co.get('ChoiceDataList')}")
