#!/usr/bin/env python3
"""Deep inspect one lyrics bundle and one storyrace bundle after decryption."""
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
print(f"Loading: {bundle_path}")
raw = open(bundle_path, 'rb').read()
print(f"Raw size: {len(raw)} bytes")
print(f"First 16 bytes: {raw[:16].hex()}")
decrypted = decrypt_bundle(raw, e)
print(f"Decrypted size: {len(decrypted)} bytes")
print(f"Decrypted first 16: {decrypted[:16].hex()}")

env = UnityPy.load(decrypted)
print(f"\nObjects: {len(list(env.objects))}")
for obj in env.objects:
    print(f"\n  --- Object: type={obj.type.name} path_id={obj.path_id} size={obj.byte_size} ---")
    if obj.type.name == "MonoBehaviour":
        try:
            tree = obj.read_typetree()
            if tree and isinstance(tree, dict):
                print(f"  Typetree keys: {list(tree.keys())}")
                for k, v in tree.items():
                    if isinstance(v, str):
                        print(f"    {k}: str = {v[:200]}")
                    elif isinstance(v, list):
                        print(f"    {k}: list[{len(v)}]")
                        for i, item in enumerate(v[:5]):
                            if isinstance(item, dict):
                                print(f"      [{i}]: dict keys={list(item.keys())}")
                                for ik, iv in item.items():
                                    if isinstance(iv, str):
                                        print(f"        {ik}: {iv[:200]}")
                                    elif isinstance(iv, list):
                                        print(f"        {ik}: list[{len(iv)}]")
                                    else:
                                        print(f"        {ik}: {type(iv).__name__} = {iv}")
                            elif isinstance(item, str):
                                print(f"      [{i}]: {item[:200]}")
                            else:
                                print(f"      [{i}]: {type(item).__name__} = {item}")
                    elif isinstance(v, dict):
                        print(f"    {k}: dict keys={list(v.keys())[:10]}")
                    elif v is None:
                        print(f"    {k}: None")
                    else:
                        print(f"    {k}: {type(v).__name__} = {v}")
            else:
                print(f"  Typetree returned: {tree}")
        except Exception as ex:
            print(f"  Error: {ex}")
    elif obj.type.name in ("TextAsset", "AssetBundle"):
        try:
            data = obj.read()
            attrs = [a for a in dir(data) if not a.startswith('_')]
            print(f"  Attrs: {attrs[:20]}")
            if hasattr(data, 'm_Script'):
                script = data.m_Script
                print(f"  m_Script type: {type(script).__name__}, len: {len(script) if script else 0}")
                if script:
                    print(f"  m_Script[:500]: {script[:500]}")
            if hasattr(data, 'name'):
                print(f"  name: {data.name}")
        except Exception as ex:
            print(f"  Error: {ex}")
