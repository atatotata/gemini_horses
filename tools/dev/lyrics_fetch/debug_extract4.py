#!/usr/bin/env python3
"""Full debug: extract lyrics CSV + storyrace, write to files for inspection."""
import os, struct, json, UnityPy, apsw, sys

sys.stdout.reconfigure(encoding='utf-8')

DAT_DIR = r"G:\Games\steamapps\common\UmamusumePrettyDerby_Jpn\UmamusumePrettyDerby_Jpn_Data\Persistent\dat"
META_DB = r"G:\Games\steamapps\common\UmamusumePrettyDerby_Jpn\UmamusumePrettyDerby_Jpn_Data\Persistent\meta"
AB_KEY = b'\x53\x2B\x46\x31\xE4\xA7\xB9\x47\x3E\x7C\xFB'
DB_BASE_KEY = b'\xF1\x70\xCE\xA4\xDF\xCE\xA3\xE1\xA5\xD8\xC7\x0B\xD1\x00\x00\x00'
DB_KEY = b'\x6D\x5B\x65\x33\x63\x36\x63\x25\x54\x71\x2D\x73\x50\x53\x63\x38\x6D\x34\x37\x7B\x35\x63\x70\x23\x37\x34\x53\x29\x73\x43\x36\x33'

def _derive_decryption_key(key, base_key):
    key = bytearray(key)
    for i in range(len(key)):
        key[i] ^= base_key[i % 13]
    return bytes(key)

def _derive_asset_key(key_long):
    if key_long == 0:
        return None
    key_bytes = struct.pack('<q', key_long)
    base_len = len(AB_KEY)
    final_key = bytearray(base_len * 8)
    for i in range(base_len):
        b = AB_KEY[i]
        base_offset = i * 8
        for j in range(8):
            final_key[base_offset + j] = b ^ key_bytes[j]
    return bytes(final_key)

def decrypt_bundle(raw_data, asset_key_int):
    if asset_key_int == 0:
        return raw_data
    decryption_key = _derive_asset_key(asset_key_int)
    if decryption_key and len(raw_data) > 256:
        data = bytearray(raw_data)
        key_len = len(decryption_key)
        for j in range(256, len(data)):
            data[j] ^= decryption_key[j % key_len]
        return bytes(data)
    return raw_data

# Connect to meta
conn = apsw.Connection(META_DB)
final_key = _derive_decryption_key(DB_KEY, DB_BASE_KEY)
conn.pragma("cipher", "chacha20")
conn.pragma("hexkey", final_key.hex())
next(conn.cursor().execute("PRAGMA quick_check"))

# Get storyrace entry for 020290011
sr_rows = list(conn.cursor().execute("SELECT n, h, e FROM a WHERE n LIKE '%storyrace_020290011%'"))
print(f"Storyrace meta rows for 020290011: {len(sr_rows)}")
for r in sr_rows:
    print(f"  n={r[0]}, h={r[1]}, e={r[2]}")
    h = r[1]
    e = r[2]
    bundle_path = os.path.join(DAT_DIR, h[:2].upper(), h)
    print(f"  Bundle: {bundle_path}")
    print(f"  Exists: {os.path.exists(bundle_path)}")
    if os.path.exists(bundle_path):
        raw = open(bundle_path, 'rb').read()
        decrypted = decrypt_bundle(raw, e)
        env = UnityPy.load(decrypted)
        for obj in env.objects:
            print(f"  Object: type={obj.type.name}")
            if obj.type.name == "TextAsset":
                data = obj.read()
                script_bytes = bytes(data.m_Script) if isinstance(data.m_Script, memoryview) else data.m_Script
                text = script_bytes.decode('utf-8-sig')
                print(f"  Name: {data.name}")
                print(f"  Content ({len(text)} chars):")
                print(text[:3000])
conn.close()

# Also test lyrics m1005 
print("\n=== LYRICS m1005 ===")
conn = apsw.Connection(META_DB)
conn.pragma("cipher", "chacha20")
conn.pragma("hexkey", final_key.hex())
next(conn.cursor().execute("PRAGMA quick_check"))
lyrics_row = list(conn.cursor().execute("SELECT n, h, e FROM a WHERE n LIKE '%m1005_lyrics%'"))[0]
h = lyrics_row[1]
e = lyrics_row[2]
bundle_path = os.path.join(DAT_DIR, h[:2].upper(), h)
raw = open(bundle_path, 'rb').read()
decrypted = decrypt_bundle(raw, e)
env = UnityPy.load(decrypted)
for obj in env.objects:
    if obj.type.name == "TextAsset":
        data = obj.read()
        script_bytes = bytes(data.m_Script) if isinstance(data.m_Script, memoryview) else data.m_Script
        text = script_bytes.decode('utf-8-sig')
        print(f"Content ({len(text)} chars):")
        print(text)
conn.close()
