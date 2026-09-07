#!/usr/bin/env python3
"""Verify extracted text is correct UTF-8 by checking code points."""
import io, os, json, struct, tempfile, UnityPy

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
    
    for obj in env.objects:
        if obj.type.name == "MonoBehaviour":
            tree = obj.read_typetree()
            if tree and "BlockList" in tree:
                bl = tree["BlockList"]
                path_map = {}
                for o in env.objects:
                    if o.type.name == "MonoBehaviour":
                        t = o.read_typetree()
                        path_map[o.path_id] = (o, t)
                
                block = bl[1]
                clips = block["TextTrack"].get("ClipList", [])
                pid = clips[0]["m_PathID"]
                clip_obj, clip_tree = path_map[pid]
                
                # Get raw data
                raw_data = clip_obj.get_raw_data()
                if raw_data is not None:
                    raw_data = bytes(raw_data)
                    
                    # Find all length-prefixed UTF-8 strings 
                    i = 0
                    while i < len(raw_data) - 4:
                        slen = struct.unpack_from('<I', raw_data, i)[0]
                        if 0 < slen < 5000 and i + 4 + slen <= len(raw_data):
                            candidate = raw_data[i+4:i+4+slen]
                            try:
                                s = candidate.decode('utf-8')
                                # Check code points
                                codepoints = [hex(ord(c)) for c in s[:20]]
                                has_jp = any(0x3040 <= ord(c) <= 0x9fff for c in s)
                                is_clean = all(c.isprintable() or c in '\r\n\t' for c in s)
                                if has_jp and is_clean:
                                    print(f"JP string at offset {i}: len={slen}")
                                    print(f"  First 20 codepoints: {codepoints}")
                                    print(f"  Text: {s[:200]}")
                                    print(f"  Repr: {repr(s[:200])}")
                                    print()
                            except:
                                pass
                        i += 1
                break
finally:
    os.unlink(tmp_path)
