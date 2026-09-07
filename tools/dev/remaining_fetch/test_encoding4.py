#!/usr/bin/env python3
"""Debug v4: Extract text directly from raw bytes by finding UTF-8 sequences."""
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

# Print full hex dump to understand structure
print(f"Decrypted total length: {len(decrypted)}")

# Parse the raw bytes looking for Unity string pattern (4-byte LE length + UTF-8 data)
def extract_unity_strings(data):
    """Find length-prefixed UTF-8 strings in binary data."""
    results = []
    i = 0
    while i < len(data) - 4:
        strlen = struct.unpack_from('<I', data, i)[0]
        if 1 < strlen < 10000 and i + 4 + strlen <= len(data):
            candidate = data[i+4:i+4+strlen]
            # Check if it's valid UTF-8 with common Japanese chars
            try:
                s = candidate.decode('utf-8')
                # Check for Japanese characters or ASCII text
                if len(s) > 0 and all(0x20 <= ord(c) < 0x7f or ord(c) > 0x2000 for c in s):
                    results.append((i, strlen, s))
                elif any(0x3040 <= ord(c) <= 0x9fff for c in s):
                    results.append((i, strlen, s))
            except (UnicodeDecodeError, ValueError):
                pass
        i += 1
    return results

# Check raw hex dump of first 30 bytes
print(f"First 100 bytes hex: {decrypted[:100].hex()}")

# Look at the structure right after UnityPy header
# The TextAsset/MonoBehaviour objects are at specific offsets
# Let me try a more targeted approach - find all potential string offsets
strings = extract_unity_strings(decrypted)
for offset, length, s in strings[:20]:
    print(f"  Offset={offset:#x} Len={length}: {repr(s[:200])}")
