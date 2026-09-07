#!/usr/bin/env python3
"""Deep inspect: resolve clip PathIDs to actual MonoBehaviour data."""
import io
import os
import json
import UnityPy

DAT_BASE = r"G:\Games\steamapps\common\UmamusumePrettyDerby_Jpn\UmamusumePrettyDerby_Jpn_Data\Persistent"

BUNDLE_BASE_KEY = "532b4631e4a7b9473e7cfb"

def _create_final_key(key):
    base_key = bytes.fromhex(BUNDLE_BASE_KEY)
    bundle_key = key.to_bytes(8, byteorder="little", signed=True)
    base_len = len(base_key)
    final_key = bytearray(base_len * 8)
    for i, b in enumerate(base_key):
        baseOffset = i << 3
        for j, k in enumerate(bundle_key):
            final_key[baseOffset + j] = b ^ k
    return final_key

gap_list = json.load(open(r"C:\TMP\remaining_fetch\gap_list.json"))
n, h, e = gap_list[0]

dat_path = os.path.join(DAT_BASE, "dat", h[:2].lower(), h)
raw = open(dat_path, "rb").read()

key_int = int(e) if isinstance(e, int) else int(e)
if key_int == 0:
    decrypted = raw
else:
    final_key = _create_final_key(key_int)
    decrypted = bytearray(raw)
    for i in range(256, len(decrypted)):
        decrypted[i] ^= final_key[i % len(final_key)]
    decrypted = bytes(decrypted)

env = UnityPy.load(io.BytesIO(decrypted))

# Build path_id -> object map
path_map = {}
for obj in env.objects:
    path_map[obj.path_id] = obj

# Find timeline
for obj in env.objects:
    if obj.type.name == "MonoBehaviour":
        tree = obj.read_typetree()
        if tree and "BlockList" in tree:
            bl = tree["BlockList"]
            print(f"Title: {tree.get('Title', 'N/A')}")
            print(f"StoryId: {tree.get('StoryId', 'N/A')}")
            print(f"BlockList length: {len(bl)}")
            
            # Skip block 0 (dummy), process blocks 1+
            for bi, block in enumerate(bl):
                if "TextTrack" not in block:
                    continue
                clips = block["TextTrack"].get("ClipList", [])
                for ci, clip in enumerate(clips):
                    pid = clip.get("m_PathID")
                    if pid and pid in path_map:
                        clip_obj = path_map[pid]
                        try:
                            clip_tree = clip_obj.read_typetree()
                            name_val = clip_tree.get("Name", "")
                            text_val = clip_tree.get("Text", "")
                            choice_list = clip_tree.get("ChoiceDataList", [])
                            print(f"\n  Block[{bi}] Clip[{ci}] path_id={pid}")
                            print(f"    Name: {name_val[:80]}")
                            print(f"    Text: {text_val[:80]}")
                            print(f"    ChoiceDataList: {choice_list[:3] if choice_list else '[]'}")
                            print(f"    All keys: {list(clip_tree.keys())}")
                        except Exception as ex:
                            print(f"  Block[{bi}] Clip[{ci}] ERROR: {ex}")
            break
