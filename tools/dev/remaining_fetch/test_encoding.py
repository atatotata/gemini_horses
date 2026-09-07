#!/usr/bin/env python3
"""Debug encoding: check raw text bytes from clip."""
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

# Find timeline and first actual clip
for obj in env.objects:
    if obj.type.name == "MonoBehaviour":
        tree = obj.read_typetree()
        if tree and "BlockList" in tree:
            bl = tree["BlockList"]
            path_map = {}
            for o in env.objects:
                path_map[o.path_id] = o
            
            # Block 1 (skip 0)
            block = bl[1]
            clips = block["TextTrack"].get("ClipList", [])
            for ci, clip in enumerate(clips):
                pid = clip.get("m_PathID")
                if pid and pid in path_map:
                    clip_obj = path_map[pid]
                    clip_tree = clip_obj.read_typetree()
                    text_val = clip_tree.get("Text", "")
                    name_val = clip_tree.get("Name", "")
                    # Check type
                    print(f"Text type: {type(text_val)}")
                    print(f"Name type: {type(name_val)}")
                    if isinstance(text_val, str):
                        print(f"Text repr: {repr(text_val[:200])}")
                        # Try encoding
                        try:
                            raw_bytes = text_val.encode('utf-8')
                            decoded = raw_bytes.decode('cp932', errors='replace')
                            print(f"As cp932: {decoded[:200]}")
                        except:
                            pass
                    elif isinstance(text_val, bytes):
                        print(f"Text bytes: {text_val[:200]}")
                        print(f"As utf-8: {text_val.decode('utf-8', errors='replace')[:200]}")
                        print(f"As cp932: {text_val.decode('cp932', errors='replace')[:200]}")
                    
                    # Check CharaId
                    print(f"CharaId: {clip_tree.get('CharaId', 'N/A')}")
                    print(f"ChoiceDataList type: {type(clip_tree.get('ChoiceDataList'))}")
                    cdl = clip_tree.get("ChoiceDataList", [])
                    print(f"ChoiceDataList len: {len(cdl)}")
                    for i, cd in enumerate(cdl[:3]):
                        print(f"  Choice {i}: {cd}")
            break
