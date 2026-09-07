#!/usr/bin/env python3
"""Test: Use temp file for UnityPy loading (like story_extract.py does)."""
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

# Write to temp file and load from there (like story_extract.py)
with tempfile.NamedTemporaryFile(delete=False, suffix=".assets") as tmp:
    tmp.write(decrypted)
    tmp_path = tmp.name

try:
    env = UnityPy.load(tmp_path)
    
    path_map = {}
    all_mono = {}
    for obj in env.objects:
        path_map[obj.path_id] = obj
        if obj.type.name == "MonoBehaviour":
            tree = obj.read_typetree()
            all_mono[obj.path_id] = tree
    
    # Find timeline
    for obj in env.objects:
        if obj.type.name == "MonoBehaviour":
            tree = all_mono.get(obj.path_id)
            if tree and "BlockList" in tree:
                bl = tree["BlockList"]
                print(f"Timeline: {tree.get('m_Name')}")
                print(f"Title: {tree.get('Title', 'N/A')}")
                print(f"BlockList: {len(bl)} blocks")
                
                for bi in range(1, min(3, len(bl))):
                    block = bl[bi]
                    clips = block["TextTrack"].get("ClipList", [])
                    for ci, clip in enumerate(clips):
                        pid = clip.get("m_PathID")
                        if pid and pid in all_mono:
                            ct = all_mono[pid]
                            name_val = ct.get("Name", "")
                            text_val = ct.get("Text", "")
                            cdl = ct.get("ChoiceDataList", [])
                            print(f"  Block[{bi}] Clip[{ci}]: Name={repr(name_val[:50])}, Text={repr(text_val[:80])}, Choices={len(cdl)}")
                            if cdl:
                                for choice in cdl[:3]:
                                    if isinstance(choice, dict):
                                        print(f"    Choice: {choice.get('Text', '')}")
                                    else:
                                        print(f"    Choice: {choice}")
                break
finally:
    os.unlink(tmp_path)
