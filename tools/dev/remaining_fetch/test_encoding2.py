#!/usr/bin/env python3
"""Debug encoding v2: check raw bytes of text field from object."""
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

# Find timeline
for obj in env.objects:
    if obj.type.name == "MonoBehaviour":
        tree = obj.read_typetree()
        if tree and "BlockList" in tree:
            bl = tree["BlockList"]
            path_map = {}
            for o in env.objects:
                path_map[o.path_id] = o
            
            block = bl[1]
            clips = block["TextTrack"].get("ClipList", [])
            for ci, clip in enumerate(clips):
                pid = clip.get("m_PathID")
                if pid and pid in path_map:
                    clip_obj = path_map[pid]
                    # Read raw data
                    raw_data = clip_obj.get_raw_data()
                    print(f"Raw data length: {len(raw_data)}")
                    print(f"Raw data hex[:200]: {raw_data[:200].hex()}")
                    # The text in UnityPy might be decoded incorrectly
                    # Try reading the raw object and manually parsing
                    clip_tree = clip_obj.read_typetree()
                    text_val = clip_tree.get("Text", "")
                    # Check if Text is a raw string from bytes
                    print(f"Text as bytes: {text_val.encode('latin-1', errors='replace')[:200].hex()}")
                    # Try interpreting as Shift-JIS
                    raw_bytes = text_val.encode('latin-1')
                    print(f"As Shift-JIS: {raw_bytes.decode('shift_jis', errors='replace')[:200]}")
                    # Try encoding the garbled text back to the source encoding
                    raw_bytes2 = text_val.encode('raw_unicode_escape')
                    print(f"raw_unicode_escape: {raw_bytes2[:200]}")
            break
