#!/usr/bin/env python3
"""Debug: read lyrics CSV + storyrace bundle."""
import os, struct, json, UnityPy

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

# === Lyrics CSV test ===
h = "YZDYNUGJ7H7JV2SKT7US4JMIGWRBITMQ"
e = -1361504547809341463
bundle_path = os.path.join(DAT_DIR, h[:2].upper(), h)
raw = open(bundle_path, 'rb').read()
decrypted = decrypt_bundle(raw, e)
env = UnityPy.load(decrypted)
for obj in env.objects:
    if obj.type.name == "TextAsset":
        data = obj.read()
        script_bytes = bytes(data.m_Script) if isinstance(data.m_Script, memoryview) else data.m_Script
        text = script_bytes.decode('utf-8-sig')  # strip BOM
        print("=== LYRICS CSV (m1005) ===")
        print(text[:2000])
        print("=== END ===\n")

        # Parse CSV to JSON format
        lines = text.strip().split('\n')
        result = {}
        for line in lines[1:]:  # skip header "time,lyrics"
            line = line.strip()
            if not line:
                continue
            parts = line.split(',', 1)
            if len(parts) == 2:
                ts, lyric = parts
                ts = ts.strip()
                lyric = lyric.strip()
                if ts:
                    result[ts] = lyric
        print(f"Parsed {len(result)} lyrics entries")
        for k, v in list(result.items())[:5]:
            print(f"  {k}: {v}")

# === Storyrace test ===
print("\n=== STORYRACE ===")
# hash=6N6EIEFKUVCKCFV5..., key=4930585773073268333
h_sr = "6N6EIEFKUVCKCFV5WZX5CDYJ4KX7AECB"
e_sr = 4930585773073268333
bundle_path_sr = os.path.join(DAT_DIR, h_sr[:2].upper(), h_sr)
if os.path.exists(bundle_path_sr):
    raw_sr = open(bundle_path_sr, 'rb').read()
    decrypted_sr = decrypt_bundle(raw_sr, e_sr)
    env_sr = UnityPy.load(decrypted_sr)
    for obj in env_sr.objects:
        print(f"  Object: type={obj.type.name} path_id={obj.path_id}")
        if obj.type.name == "TextAsset":
            data = obj.read()
            script_bytes = bytes(data.m_Script) if isinstance(data.m_Script, memoryview) else data.m_Script
            try:
                text_sr = script_bytes.decode('utf-8-sig')
                print(f"  Name: {data.name}")
                print(f"  Content ({len(text_sr)} chars):")
                print(text_sr[:2000])
            except:
                print(f"  Raw bytes ({len(script_bytes)}): {script_bytes[:200]}")
