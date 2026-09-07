#!/usr/bin/env python3
"""Debug v6: Check obj.raw_data attribute and try reading raw bytes from reader."""
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
            
            # Check raw_data vs get_raw_data
            print(f"raw_data attr: {clip_obj.raw_data[:100].hex() if clip_obj.raw_data else 'None'}")
            print(f"raw_data len: {len(clip_obj.raw_data) if clip_obj.raw_data else 0}")
            
            # Check reader
            reader = clip_obj.reader
            print(f"Reader position: {reader.Position}")
            print(f"Reader byte_size: {clip_obj.byte_size}")
            
            # Read full raw from original position
            reader.Position = 0
            full_raw = reader.read_bytes(clip_obj.byte_size)
            print(f"Full raw ({len(full_raw)} bytes): {full_raw[:80].hex()}")
            
            # Now search in this full raw for UTF-8 strings
            # The text "今日から" in UTF-8 is: e4 bb 8a e6 97 a5 e3 81 8b e3 82 89
            target = b'\xe4\xbb\x8a\xe6\x97\xa5'
            idx = full_raw.find(target)
            if idx >= 0:
                # Found Japanese text - extract string
                # Go back to find length prefix (4 bytes LE)
                if idx >= 4:
                    strlen = struct.unpack_from('<I', full_raw, idx-4)[0]
                    print(f"Found string at offset {idx}, prefix length={strlen}")
                    s = full_raw[idx:idx+strlen].decode('utf-8', errors='replace')
                    print(f"Decoded string: {s[:300]}")
            
            # Also search in entire decrypted bundle for the same
            target2 = b'\xe4\xbb\x8a\xe6\x97\xa5'
            idx2 = decrypted.find(target2)
            if idx2 >= 0:
                if idx2 >= 4:
                    strlen2 = struct.unpack_from('<I', decrypted, idx2-4)[0]
                    s2 = decrypted[idx2:idx2+strlen2].decode('utf-8', errors='replace')
                    print(f"\nFound in bundle at offset {idx2:#x}, length prefix={strlen2}")
                    print(f"String: {s2[:300]}")
            break
