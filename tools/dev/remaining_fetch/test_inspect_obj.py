#!/usr/bin/env python3
"""Inspect MonoBehaviour object attributes to find raw data access."""
import io, os, json, tempfile, UnityPy, struct

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

with tempfile.NamedTemporaryFile(delete=False, suffix=".assets") as tmp:
    tmp.write(decrypted)
    tmp_path = tmp.name

try:
    env = UnityPy.load(tmp_path)
    
    path_map = {}
    for obj in env.objects:
        path_map[obj.path_id] = obj
    
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
                            
                            # Print all attributes
                            print(f"\nClip {bi}.{ci}:")
                            for attr in ['byte_offset', 'byte_size', 'path_id', 'type', 'raw_data', 'data_offset', 'data_size']:
                                try:
                                    val = getattr(clip_obj, attr)
                                    print(f"  {attr} = {val}")
                                except:
                                    print(f"  {attr} = <missing>")
                            
                            # Try to read raw data from bundle
                            # The object header in Unity format has specific layout
                            # Try accessing the raw data through the assets file
                            af = clip_obj.assets_file
                            print(f"  assets_file type: {type(af)}")
                            
                            # Try to read from the raw data stream
                            try:
                                raw_data = clip_obj.get_raw_data()
                                print(f"  get_raw_data() = {len(raw_data)} bytes")
                                print(f"  hex[:80]: {raw_data[:80].hex()}")
                            except Exception as ex:
                                print(f"  get_raw_data() failed: {ex}")
                            
                            # Try raw_data attribute directly
                            try:
                                rd = clip_obj.raw_data
                                print(f"  raw_data attr = {rd[:80].hex() if rd else None}")
                            except Exception as ex:
                                print(f"  raw_data attr failed: {ex}")
                break
finally:
    os.unlink(tmp_path)
