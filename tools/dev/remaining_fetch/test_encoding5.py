#!/usr/bin/env python3
"""Debug v5: Try obj.read() vs obj.read_typetree() and also try TextAsset approach."""
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

# Try reading the clip objects as raw/typed 
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
            
            # Try read_typetree with different approach
            tree2 = clip_obj.read_typetree()
            # Check m_Script for raw bytes
            print(f"Keys from read_typetree: {list(tree2.keys())}")
            
            # Try obj.read()
            try:
                obj_read = clip_obj.read()
                print(f"obj.read() type: {type(obj_read)}")
                print(f"obj.read() attrs: {[a for a in dir(obj_read) if not a.startswith('_')][:20]}")
                if hasattr(obj_read, 'Name'):
                    print(f"Name: {obj_read.Name}")
                if hasattr(obj_read, 'Text'):
                    print(f"Text: {obj_read.Text}")
            except Exception as ex:
                print(f"obj.read() failed: {ex}")
            
            # Try direct raw parsing
            raw_data = clip_obj.get_raw_data()
            print(f"\nRaw data ({len(raw_data)} bytes):")
            print(f"  hex[:80]: {raw_data[:80].hex()}")
            # The data starts with m_GameObject, m_Enabled, m_Script, m_Name, then custom fields
            # Try to find where Name and Text strings start
            # Search for 'Narrator' or JP equivalent in raw bytes
            for encoding in ['utf-8', 'shift_jis', 'cp932']:
                try:
                    enc_name = "Narrator".encode(encoding)
                    idx = raw_data.find(enc_name)
                    if idx >= 0:
                        print(f"  Found 'Narrator' at offset {idx} with {encoding}")
                except:
                    pass
                try:
                    # Check for the start of the text (CJK chars)
                    for pattern_bytes in [b'\xe6\x97\xa5', b'\xe4\xbb\x8a']:
                        idx = raw_data.find(pattern_bytes)
                        if idx >= 0:
                            # Extract string from here
                            end = raw_data.find(b'\x00', idx)
                            if end < 0 or end - idx > 500:
                                end = idx + 200
                            s = raw_data[idx:min(end, idx+200)]
                            print(f"  CJK at offset {idx}: {s.decode('utf-8', errors='replace')[:200]}")
                            break
                except:
                    pass
            break
