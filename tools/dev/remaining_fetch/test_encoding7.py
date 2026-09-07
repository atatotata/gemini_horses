#!/usr/bin/env python3
"""Debug v7: Manually extract strings from raw bundle bytes by finding UTF-8 patterns."""
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

# Check all objects' raw data for UTF-8 strings
print("=== Searching for UTF-8 Japanese text in all objects ===")
for obj in env.objects:
    if obj.type.name == "MonoBehaviour":
        tree = obj.read_typetree()
        if tree and "m_Name" in tree:
            mname = tree.get("m_Name", "")
            if "storytimeline" in mname:
                continue  # skip the main timeline object, we already tested it

# Try another approach: UnityPy's string decoder might need adjustment
# Let's look at the actual bytes in the typetree read for a single clip
# by reading the raw serialized data and comparing

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
            pid = clips[0]["m_PathID"]
            clip_obj = path_map[pid]
            
            # Get the raw data from the reader
            reader = clip_obj.reader
            saved_pos = reader.Position
            reader.Position = clip_obj.byte_offset
            raw_data = bytes(reader.read_bytes(clip_obj.byte_size))
            reader.Position = saved_pos
            
            print(f"Clip raw ({len(raw_data)} bytes):")
            print(f"  hex[:120]: {raw_data[:120].hex()}")
            
            # Parse: skip Unity object header (4+4+4+4 = 16 bytes for some, varies)
            # Actually let's just scan for length-prefixed UTF-8 strings
            for i in range(len(raw_data) - 4):
                slen = struct.unpack_from('<I', raw_data, i)[0]
                if 2 < slen < 1000 and i + 4 + slen <= len(raw_data):
                    candidate = raw_data[i+4:i+4+slen]
                    try:
                        s = candidate.decode('utf-8')
                        # Check if it contains Japanese chars or reasonable text
                        has_jp = any(0x3000 <= ord(c) <= 0x9fff for c in s)
                        has_ascii = any(c.isalpha() for c in s)
                        if (has_jp or (has_ascii and len(s) > 3)) and '\x00' not in s:
                            print(f"  Found at offset {i}: [{slen}] {repr(s[:200])}")
                    except:
                        pass
            break
