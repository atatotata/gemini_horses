#!/usr/bin/env python3
"""Deep inspect TextAsset contents - read m_Script as bytes."""
import os, sys, struct, json, UnityPy

DAT_DIR = r"G:\Games\steamapps\common\UmamusumePrettyDerby_Jpn\UmamusumePrettyDerby_Jpn_Data\Persistent\dat"
AB_KEY = b'\x53\x2B\x46\x31\xE4\xA7\xB9\x47\x3E\x7C\xFB'

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

# Lyrics: m1005, hash=YZDYNUGJ7H7JV2SKT7US4JMIGWRBITMQ, key=-1361504547809341463
h = "YZDYNUGJ7H7JV2SKT7US4JMIGWRBITMQ"
e = -1361504547809341463
bundle_path = os.path.join(DAT_DIR, h[:2].upper(), h)
raw = open(bundle_path, 'rb').read()
decrypted = decrypt_bundle(raw, e)

env = UnityPy.load(decrypted)
for obj in env.objects:
    if obj.type.name == "TextAsset":
        data = obj.read()
        # m_Script is memoryview - convert to bytes
        script_mv = data.m_Script
        if isinstance(script_mv, memoryview):
            script_bytes = bytes(script_mv)
        elif isinstance(script_mv, bytes):
            script_bytes = script_mv
        else:
            script_bytes = script_mv
        
        print(f"Script bytes length: {len(script_bytes)}")
        print(f"Script hex first 100: {script_bytes[:100].hex()}")
        print(f"Script raw first 500: {script_bytes[:500]}")
        
        # Try decoding as UTF-8
        try:
            text = script_bytes.decode('utf-8')
            print(f"\nDecoded as UTF-8 ({len(text)} chars):")
            print(text[:1000])
            # Try as JSON
            try:
                parsed = json.loads(text)
                print(f"\nParsed JSON type: {type(parsed)}")
                if isinstance(parsed, dict):
                    print(f"JSON keys: {list(parsed.keys())[:20]}")
                    for k, v in list(parsed.items())[:5]:
                        print(f"  {k}: {repr(v)[:200]}")
                elif isinstance(parsed, list):
                    print(f"JSON list len: {len(parsed)}")
                    for item in parsed[:5]:
                        print(f"  {repr(item)[:200]}")
            except json.JSONDecodeError as je:
                print(f"\nNot JSON: {je}")
        except UnicodeDecodeError:
            print("Not UTF-8, trying Shift-JIS...")
            try:
                text = script_bytes.decode('shift-jis')
                print(f"Shift-JIS decoded: {text[:500]}")
            except:
                print("Not Shift-JIS either")
