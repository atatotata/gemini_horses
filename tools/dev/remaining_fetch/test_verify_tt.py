#!/usr/bin/env python3
"""Verify: check if read_typetree strings have correct codepoints too."""
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
                
                # Check typetree strings
                tt_text = clip_tree.get("Text", "")
                tt_name = clip_tree.get("Name", "")
                tt_cdl = clip_tree.get("ChoiceDataList", [])
                
                # Write to file for verification
                with open(r"C:\TMP\remaining_fetch\verify_typetree.txt", "w", encoding="utf-8") as f:
                    f.write(f"Name: {tt_name}\n")
                    f.write(f"Text: {tt_text}\n")
                    f.write(f"Choices: {tt_cdl}\n")
                    f.write(f"Name codepoints: {[hex(ord(c)) for c in tt_name[:20]]}\n")
                    f.write(f"Text codepoints: {[hex(ord(c)) for c in tt_text[:20]]}\n")
                    
                    # Check all chars in text
                    bad_chars = [(i, hex(ord(c))) for i, c in enumerate(tt_text) if ord(c) > 127 and not (0x3000 <= ord(c) <= 0x9fff) and not (0x3040 <= ord(c) <= 0x9fff)]
                    f.write(f"Non-JP non-ASCII chars: {bad_chars[:20]}\n")
                
                print("Written verify_typetree.txt")
                break
finally:
    os.unlink(tmp_path)
