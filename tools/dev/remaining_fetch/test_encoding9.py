#!/usr/bin/env python3
"""Debug v9: Check raw decrypted bytes for known Japanese UTF-8 sequences."""
import struct

DAT_BASE = r"G:\Games\steamapps\common\UmamusumePrettyDerby_Jpn\UmamusumePrettyDerby_Jpn_Data\Persistent"
BUNDLE_BASE_KEY = "532b4631e4a7b9473e7cfb"

gap_list_json = r"C:\TMP\remaining_fetch\gap_list.json"
import json
gap_list = json.load(open(gap_list_json))
n, h, e = gap_list[0]

dat_path = f"{DAT_BASE}\\dat\\{h[:2].lower()}\\{h}"
raw = open(dat_path, "rb").read()

key_int = int(e)
final_key = bytes.fromhex(BUNDLE_BASE_KEY)
bundle_key = key_int.to_bytes(8, byteorder="little", signed=True)
fk = bytearray(len(final_key) * 8)
for i, b in enumerate(final_key):
    bo = i << 3
    for j, k in enumerate(bundle_key):
        fk[bo + j] = b ^ k

decrypted = bytearray(raw)
for i in range(256, len(decrypted)):
    decrypted[i] ^= fk[i % len(fk)]
decrypted = bytes(decrypted)

# Search for known patterns
# "今日" in UTF-8 = e4 bb 8a e6 97 a5
target_utf8 = bytes([0xe4, 0xbb, 0x8a, 0xe6, 0x97, 0xa5])
idx = decrypted.find(target_utf8)
print(f"'今日' UTF-8 found at: {idx}")

# Search for "Narrator" in UTF-8
target_ascii = b"Narrator"
idx2 = decrypted.find(target_ascii)
print(f"'Narrator' found at: {idx2}")

# Search for "storytimeline" 
target_st = b"storytimeline"
idx3 = decrypted.find(target_st)
print(f"'storytimeline' found at: {idx3}")

# Let's look at bytes around known offset from encoding2.py (0x60 was the string start in raw)
# But wait - encoding2.py was looking at the raw clip object, not the whole bundle
# Let me search for 0x74000000 pattern (116 bytes length prefix for the first text string)
target_len = struct.pack('<I', 116)
idx4 = decrypted.find(target_len)
print(f"'116' as LE int found at: {idx4}")

# Let me try: scan for 0x0d0a (CRLF) which we know exists in the text
target_crlf = b"\x0d\x0a"
positions = []
start = 0
while True:
    idx = decrypted.find(target_crlf, start)
    if idx < 0:
        break
    positions.append(idx)
    start = idx + 1
print(f"CRLF positions: {positions[:10]}")

# Check if the data around first CRLF has Japanese text
if positions:
    for pos in positions[:3]:
        # Look back 200 bytes
        chunk = decrypted[max(0, pos-200):pos+200]
        # Find any 3-byte UTF-8 sequences (common for Japanese)
        jp_count = 0
        for j in range(len(chunk)-2):
            b0 = chunk[j]
            if 0xe0 <= b0 <= 0xef:  # 3-byte UTF-8 lead
                jp_count += 1
        print(f"  Around CRLF at {pos}: {jp_count} potential UTF-8 3-byte sequences in 400-byte window")
        if jp_count > 0:
            # Try to decode as UTF-8
            try:
                s = chunk.decode('utf-8', errors='replace')
                print(f"  As UTF-8: {s[:200]}")
            except:
                pass
