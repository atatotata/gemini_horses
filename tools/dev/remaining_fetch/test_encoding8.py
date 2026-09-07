#!/usr/bin/env python3
"""Debug v8: Parse the raw clip object bytes directly to extract Name/Text strings."""
import io
import os
import json
import struct
import re
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

# Find ALL length-prefixed UTF-8 strings in the entire decrypted bundle
print("=== All UTF-8 strings in decrypted bundle ===")
all_strings = []
for i in range(len(decrypted) - 4):
    slen = struct.unpack_from('<I', decrypted, i)[0]
    if 1 < slen < 5000 and i + 4 + slen <= len(decrypted):
        candidate = decrypted[i+4:i+4+slen]
        try:
            s = candidate.decode('utf-8')
            # Check for Japanese chars
            has_jp = any(0x3000 <= ord(c) <= 0x9fff for c in s)
            is_printable = all(c.isprintable() or c in '\r\n\t' for c in s)
            if has_jp and is_printable and len(s) > 2:
                all_strings.append((i, slen, s))
        except:
            pass

for offset, length, s in all_strings:
    print(f"  Offset={offset:#x} Len={length}: {s[:150]}")

print(f"\nTotal strings found: {len(all_strings)}")
