#!/usr/bin/env python3
"""Final approach: bypass read_typetree and extract text directly from raw clip bytes."""
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

key_int = int(e)
final_key = _create_final_key(key_int)
decrypted = bytearray(raw)
for i in range(256, len(decrypted)):
    decrypted[i] ^= final_key[i % len(final_key)]
decrypted = bytes(decrypted)

env = UnityPy.load(io.BytesIO(decrypted))

# Get all MonoBehaviour objects with path_id
all_objects = {}
for obj in env.objects:
    all_objects[obj.path_id] = obj

# Find the timeline
for obj in env.objects:
    if obj.type.name == "MonoBehaviour":
        tree = obj.read_typetree()
        if tree and "BlockList" in tree:
            bl = tree["BlockList"]
            print(f"Found timeline: {tree.get('m_Name')}")
            print(f"BlockList length: {len(bl)}")
            
            # Process blocks 1+
            for bi in range(1, len(bl)):
                block = bl[bi]
                if "TextTrack" not in block:
                    continue
                clips = block["TextTrack"].get("ClipList", [])
                for ci, clip in enumerate(clips):
                    pid = clip.get("m_PathID")
                    if not pid or pid not in all_objects:
                        continue
                    clip_obj = all_objects[pid]
                    
                    # Read the full raw bytes for this object
                    # Get raw data using the reader  
                    raw_data = clip_obj.get_raw_data()
                    if raw_data is None:
                        # Fallback: read from bundle directly
                        continue
                    raw_data = bytes(raw_data)
                    
                    # Extract strings from raw data
                    # Find Name and Text strings (length-prefixed UTF-8)
                    strings = []
                    for i in range(len(raw_data) - 4):
                        slen = struct.unpack_from('<I', raw_data, i)[0]
                        if 0 < slen < 5000 and i + 4 + slen <= len(raw_data):
                            candidate = raw_data[i+4:i+4+slen]
                            try:
                                s = candidate.decode('utf-8')
                                # Check if it's a reasonable string
                                if len(s) > 0 and all(c.isprintable() or c in '\r\n\t' for c in s):
                                    # Skip obvious non-text (like "2022.3.62f1")
                                    if not all(c in '0123456789.' for c in s.replace('f', '')):
                                        strings.append(s)
                            except:
                                pass
                    
                    # Name should be first, Text should be the longer one
                    # Also look for CRLF which is typical of Text field
                    name_val = ""
                    text_val = ""
                    for s in strings:
                        if '\r\n' in s or '\n' in s:
                            text_val = s
                        elif len(s) < 50 and not name_val:
                            name_val = s
                    
                    # Get CharaId from typetree
                    clip_tree = clip_obj.read_typetree()
                    chara_id = clip_tree.get("CharaId", 0)
                    
                    # Get ChoiceDataList
                    cdl = clip_tree.get("ChoiceDataList", [])
                    choice_texts = []
                    for cd in cdl:
                        if isinstance(cd, dict):
                            choice_texts.append(cd.get("Text", ""))
                        elif isinstance(cd, str):
                            choice_texts.append(cd)
                    
                    print(f"  Block[{bi}] Clip[{ci}] pid={pid}")
                    print(f"    Strings found: {len(strings)}")
                    for s in strings:
                        print(f"      [{len(s)}] {s[:100]}")
                    print(f"    CharaId: {chara_id}")
                    print(f"    Choices: {choice_texts}")
                    
                    if bi > 2:
                        break
                if bi > 2:
                    break
            break
