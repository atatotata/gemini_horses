#!/usr/bin/env python3
"""Verify: write extracted text to file and read back."""
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
                
                raw_data = clip_obj.get_raw_data()
                if raw_data is not None:
                    raw_data = bytes(raw_data)
                    
                    # Find first JP string
                    i = 0
                    while i < len(raw_data) - 4:
                        slen = struct.unpack_from('<I', raw_data, i)[0]
                        if 0 < slen < 5000 and i + 4 + slen <= len(raw_data):
                            candidate = raw_data[i+4:i+4+slen]
                            try:
                                s = candidate.decode('utf-8')
                                has_jp = any(0x3040 <= ord(c) <= 0x9fff for c in s)
                                is_clean = all(c.isprintable() or c in '\r\n\t' for c in s)
                                if has_jp and is_clean:
                                    # Write to file
                                    with open(r"C:\TMP\remaining_fetch\verify_text.txt", "w", encoding="utf-8") as f:
                                        f.write(s)
                                    print(f"Wrote {slen} chars to verify_text.txt")
                                    print(f"Codepoints: {[hex(ord(c)) for c in s[:10]]}")
                                    break
                            except:
                                pass
                        i += 1
                break
finally:
    os.unlink(tmp_path)

# Read back and verify
with open(r"C:\TMP\remaining_fetch\verify_text.txt", "r", encoding="utf-8") as f:
    read_back = f.read()
print(f"\nRead back: {read_back}")
print(f"Read back codepoints: {[hex(ord(c)) for c in read_back[:10]]}")
print(f"Match: {read_back == s}")
