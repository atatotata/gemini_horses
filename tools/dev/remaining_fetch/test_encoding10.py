#!/usr/bin/env python3
"""Debug v10: Decode bytes around CRLF positions as UTF-8."""
import struct, json

DAT_BASE = r"G:\Games\steamapps\common\UmamusumePrettyDerby_Jpn\UmamusumePrettyDerby_Jpn_Data\Persistent"
BUNDLE_BASE_KEY = "532b4631e4a7b9473e7cfb"

gap_list = json.load(open(r"C:\TMP\remaining_fetch\gap_list.json"))
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

# Look at raw bytes around first CRLF
for crlf_pos in [19034, 19335]:
    start = max(0, crlf_pos - 300)
    chunk = decrypted[start:crlf_pos + 100]
    print(f"\n=== Around CRLF at {crlf_pos} (showing from offset {start}) ===")
    # Print hex with ASCII
    for i in range(0, min(400, len(chunk)), 32):
        hex_part = chunk[i:i+32].hex()
        ascii_part = ''.join(chr(b) if 32 <= b < 127 else '.' for b in chunk[i:i+32])
        print(f"  {start+i:#06x}: {hex_part}")
        print(f"         {ascii_part}")
    
    # Try decoding the whole chunk as UTF-8
    # Find the start of the text content
    # Look for length prefix before each CRLF-containing string
    for j in range(max(0, crlf_pos - 200), crlf_pos - 2):
        slen = struct.unpack_from('<I', decrypted, j)[0]
        if 10 < slen < 1000:
            candidate = decrypted[j+4:j+4+slen]
            if candidate[0] >= 0x20 or candidate[0:2] == b'\x0d\x0a':
                try:
                    s = candidate.decode('utf-8')
                    if any(0x3040 <= ord(c) <= 0x9fff for c in s):
                        print(f"  FOUND JP string at {j}: len={slen} => {s[:200]}")
                except:
                    pass
