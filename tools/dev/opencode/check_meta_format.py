#!/usr/bin/env python3
"""Check Global meta file format."""
import os

# Read first 256 bytes of Global meta
global_meta = r"G:\Games\steamapps\common\UmamusumePrettyDerby\UmamusumePrettyDerby_Data\Persistent\meta"
with open(global_meta, "rb") as f:
    data = f.read(256)

print(f"Global meta size: {os.path.getsize(global_meta)} bytes")
print(f"First 32 bytes (hex): {data[:32].hex()}")
print(f"First 32 bytes (repr): {repr(data[:32])}")

# Check if it looks like a SQLite database
if data[:16] == b"SQLite format 3\x00":
    print("=> Looks like unencrypted SQLite!")
elif b"SQLCipher" in data[:64]:
    print("=> Looks like SQLCipher encrypted SQLite!")
else:
    print("=> Unknown format (likely encrypted with chacha20 or other scheme)")

# Check JP meta for comparison
jp_meta = r"G:\Games\steamapps\common\UmamusumePrettyDerby_Jpn\UmamusumePrettyDerby_Jpn_Data\Persistent\meta"
# Need to copy since JP game is running and may lock it
import shutil
temp = r"C:\TMP\opencode\jp_meta_copy"
shutil.copy2(jp_meta, temp)
with open(temp, "rb") as f:
    jp_data = f.read(256)

print(f"\nJP meta size: {os.path.getsize(temp)} bytes")
print(f"First 32 bytes (hex): {jp_data[:32].hex()}")
print(f"First 32 bytes (repr): {repr(jp_data[:32])}")

if jp_data[:16] == b"SQLite format 3\x00":
    print("=> Looks like unencrypted SQLite!")
else:
    print("=> Encrypted (SQLCipher)")

os.remove(temp)
