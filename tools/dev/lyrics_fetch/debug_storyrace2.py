#!/usr/bin/env python3
"""Debug storyrace MonoBehaviour with more detail."""
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

# Get storyrace entry
sr_row = list(conn.cursor().execute("SELECT n, h, e FROM a WHERE n = 'race/storyrace/text/storyrace_020290011'"))[0]
h, e = sr_row[1], sr_row[2]
bundle_path = os.path.join(DAT_DIR, h[:2].upper(), h)
raw = open(bundle_path, 'rb').read()
decrypted = decrypt_bundle(raw, e)

env = UnityPy.load(decrypted)
for obj in env.objects:
    print(f"\n=== Object: type={obj.type.name} path_id={obj.path_id} byte_size={obj.byte_size} ===")
    if obj.type.name == "MonoBehaviour":
        try:
            # Try dump_typetree_structure
            st = obj.dump_typetree_structure()
            print(f"Typetree structure:\n{st}")
        except Exception as ex:
            print(f"dump_typetree_structure error: {ex}")
        try:
            tree = obj.read_typetree()
            if tree:
                print(f"Typetree: {json.dumps(tree, ensure_ascii=False, indent=2)[:3000]}")
            else:
                print("Typetree returned None")
        except Exception as ex:
            print(f"read_typetree error: {ex}")
    elif obj.type.name == "MonoScript":
        try:
            data = obj.read()
            print(f"MonoScript: {data.__dict__}")
        except Exception as ex:
            print(f"Error: {ex}")

# Also dump raw bytes of the MonoBehaviour
for obj in env.objects:
    if obj.type.name == "MonoBehaviour":
        raw_data = obj.get_raw_data()
        print(f"\nMonoBehaviour raw data ({len(raw_data)} bytes):")
        print(raw_data[:500].hex())
        print(raw_data[:500])

conn.close()
