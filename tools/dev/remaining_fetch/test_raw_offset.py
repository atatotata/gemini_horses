#!/usr/bin/env python3
"""Test: Find actual raw clip object bytes and manually decode strings."""
import io
import os
import json
import struct
import tempfile
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

key_int = int(e)
final_key = _create_final_key(key_int)
decrypted = bytearray(raw)
for i in range(256, len(decrypted)):
    decrypted[i] ^= final_key[i % len(final_key)]
decrypted = bytes(decrypted)

# Write to temp file
with tempfile.NamedTemporaryFile(delete=False, suffix=".assets") as tmp:
    tmp.write(decrypted)
    tmp_path = tmp.name

try:
    env = UnityPy.load(tmp_path)
    
    path_map = {}
    for obj in env.objects:
        path_map[obj.path_id] = obj
    
    # Find timeline and process
    for obj in env.objects:
        if obj.type.name == "MonoBehaviour":
            tree = obj.read_typetree()
            if tree and "BlockList" in tree:
                bl = tree["BlockList"]
                
                for bi in range(1, min(3, len(bl))):
                    block = bl[bi]
                    clips = block["TextTrack"].get("ClipList", [])
                    for ci, clip in enumerate(clips):
                        pid = clip.get("m_PathID")
                        if pid and pid in path_map:
                            clip_obj = path_map[pid]
                            
                            # Get raw serialized data using reader
                            reader = clip_obj.reader
                            # Save position
                            saved = reader.Position
                            
                            # The object data starts at byte_offset
                            offset = clip_obj.byte_offset
                            size = clip_obj.byte_size
                            
                            reader.Position = offset
                            raw_data = bytes(reader.read_bytes(size))
                            reader.Position = saved
                            
                            print(f"\nClip {bi}.{ci}: offset={offset} size={size}")
                            print(f"Raw hex[:64]: {raw_data[:64].hex()}")
                            
                            # Find strings by scanning for length-prefixed UTF-8
                            for i in range(len(raw_data) - 4):
                                slen = struct.unpack_from('<I', raw_data, i)[0]
                                if 1 < slen < 5000 and i + 4 + slen <= len(raw_data):
                                    candidate = raw_data[i+4:i+4+slen]
                                    try:
                                        s = candidate.decode('utf-8')
                                        has_jp = any(0x3040 <= ord(c) <= 0x9fff for c in s)
                                        is_printable = all(c.isprintable() or c in '\r\n\t' for c in s)
                                        if (has_jp or (is_printable and len(s) > 2)):
                                            print(f"  String at {i}: [{slen}] {repr(s[:200])}")
                                    except:
                                        pass
                break
finally:
    os.unlink(tmp_path)
