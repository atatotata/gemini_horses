#!/usr/bin/env python3
"""Print full 368-byte raw data to find where strings are."""
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
                block = bl[1]
                clips = block["TextTrack"].get("ClipList", [])
                pid = clips[0]["m_PathID"]
                clip_obj = path_map[pid]
                
                raw_data = clip_obj.get_raw_data()
                print(f"Full raw ({len(raw_data)} bytes):")
                for i in range(0, len(raw_data), 16):
                    chunk = raw_data[i:i+16]
                    hex_part = chunk.hex()
                    ascii_part = ''.join(chr(b) if 32 <= b < 127 else '.' for b in chunk)
                    print(f"  {i:#05x}: {hex_part}  {ascii_part}")
                
                # Also check: what does the full decrypted bundle look like around offset 0x4b5b?
                # From encoding10.py, we know there's text at 0x4b5b region
                print(f"\nDecrypted around 0x4a2e (where Japanese was):")
                for i in range(0x4a20, 0x4ab0, 16):
                    chunk = decrypted[i:i+16]
                    hex_part = chunk.hex()
                    ascii_part = ''.join(chr(b) if 32 <= b < 127 else '.' for b in chunk)
                    print(f"  {i:#06x}: {hex_part}  {ascii_part}")
                
                # Search for the e4bb8a pattern in the full decrypted data
                target = bytes([0xe4, 0xbb, 0x8a])
                idx = decrypted.find(target)
                print(f"\n'e4bb8a' found at: {idx}")
                if idx >= 0:
                    # Show context
                    for i in range(max(0, idx-20), min(len(decrypted), idx+50), 16):
                        chunk = decrypted[i:i+16]
                        hex_part = chunk.hex()
                        ascii_part = ''.join(chr(b) if 32 <= b < 127 else '.' for b in chunk)
                        print(f"  {i:#06x}: {hex_part}  {ascii_part}")
                break
finally:
    os.unlink(tmp_path)
