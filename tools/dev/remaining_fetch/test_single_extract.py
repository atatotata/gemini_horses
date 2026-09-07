#!/usr/bin/env python3
"""Test UnityPy extraction of a single story bundle from dat."""
import io
import os
import json
import UnityPy

DAT_BASE = r"G:\Games\steamapps\common\UmamusumePrettyDerby_Jpn\UmamusumePrettyDerby_Jpn_Data\Persistent"

# Pick a known hash from the gap list
gap_list = json.load(open(r"C:\TMP\remaining_fetch\gap_list.json"))
# Take first entry
n, h, e = gap_list[0]
print(f"Testing: {n}")
print(f"Hash: {h}")
print(f"Key (e): {e}")

# Read from dat
dat_path = os.path.join(DAT_BASE, "dat", h[:2].lower(), h)
print(f"DAT path: {dat_path}")
print(f"Exists: {os.path.exists(dat_path)}")

raw = open(dat_path, "rb").read()
print(f"Raw size: {len(raw)}")

# Decrypt
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

key_int = int(e, 16) if isinstance(e, str) else e
if key_int == 0:
    decrypted = raw
else:
    final_key = _create_final_key(key_int)
    decrypted = bytearray(raw)
    for i in range(256, len(decrypted)):
        decrypted[i] ^= final_key[i % len(final_key)]
    decrypted = bytes(decrypted)
print(f"Decrypted size: {len(decrypted)}")

# Load with UnityPy
env = UnityPy.load(io.BytesIO(decrypted))

# Find MonoBehaviours
mono_behaviours = []
for obj in env.objects:
    if obj.type.name == "MonoBehaviour":
        try:
            tree = obj.read_typetree()
            name = tree.get("m_Name", "N/A")
            mono_behaviours.append((name, tree))
        except Exception as ex:
            mono_behaviours.append((f"ERR: {ex}", None))

print(f"\nMonoBehaviours found: {len(mono_behaviours)}")
for name, tree in mono_behaviours:
    if tree:
        keys = list(tree.keys())
        print(f"  Name={name}, keys={keys[:10]}")
    else:
        print(f"  Name={name}")

# Find the timeline object
storyline_basename = os.path.splitext(os.path.basename(n))[0]
print(f"\nLooking for: {storyline_basename}")
for name, tree in mono_behaviours:
    if tree and storyline_basename in str(name):
        print(f"  FOUND: {name}")
        if "BlockList" in tree:
            bl = tree["BlockList"]
            print(f"  BlockList length: {len(bl)}")
            for bi, block in enumerate(bl[:3]):
                tracks = list(block.keys())
                print(f"    Block {bi}: tracks={tracks}")
                if "TextTrack" in block:
                    tt = block["TextTrack"]
                    clips = tt.get("ClipList", [])
                    print(f"    TextTrack clips: {len(clips)}")
                    for ci, clip in enumerate(clips[:2]):
                        print(f"      Clip {ci}: {list(clip.keys())[:10]}")
        break
