#!/usr/bin/env python3
"""Debug encoding v3: manually parse raw bytes to extract text correctly."""
import io
import os
import json
import struct
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
                    raw_data = clip_obj.get_raw_data()
                    print(f"Raw data length: {len(raw_data)}")
                    
                    # Find UTF-8 strings in the raw data
                    # The text seems to be embedded after a length prefix
                    # Let's search for known UTF-8 patterns
                    idx = 0
                    strings_found = []
                    while idx < len(raw_data) - 4:
                        # Look for a 4-byte length prefix followed by UTF-8 data
                        if idx + 4 < len(raw_data):
                            possible_len = struct.unpack_from('<I', raw_data, idx)[0]
                            if 4 < possible_len < 500 and idx + 4 + possible_len <= len(raw_data):
                                candidate = raw_data[idx+4:idx+4+possible_len]
                                try:
                                    decoded = candidate.decode('utf-8')
                                    if any(0x3040 <= ord(c) <= 0x9fff for c in decoded[:5]):
                                        strings_found.append((idx, possible_len, decoded))
                                except:
                                    pass
                        idx += 1
                    
                    for offset, length, s in strings_found:
                        print(f"  Offset={offset} Len={length}: {s[:200]}")
            break

# Also check what encoding the localized file uses
loc_path = r"G:\Games\steamapps\common\UmamusumePrettyDerby_Jpn\gemini_horses\localized_data\assets\story\data\50\1001\storytimeline_501001100.json"
with open(loc_path, 'r', encoding='utf-8') as f:
    loc = json.load(f)
print(f"\nLocalized first block text: {loc['text_block_list'][0]['text'][:200]}")
