"""Probe text encoding from decrypted bundle."""
import json, sys
from pathlib import Path
import apsw
import UnityPy

META_KEY = "9c2bab97bcf8c0c4f1a9ea7881a213f6c9ebf9d8d4c6a8e43ce5a259bde7e9fd"
META_URI = f"file:C:/TMP/meta_fresh.bin?hexkey={META_KEY}"
DAT_DIR = Path(r"G:\Games\steamapps\common\UmamusumePrettyDerby_Jpn\UmamusumePrettyDerby_Jpn_Data\Persistent\dat")
BUNDLE_BASE_KEY = bytes.fromhex("532b4631e4a7b9473e7cfb")

def decrypt_asset_bundle(data, key):
    if len(data) < 256:
        return data
    bundle_key = key.to_bytes(8, byteorder="little", signed=True)
    base_len = len(BUNDLE_BASE_KEY)
    final_key = bytearray(base_len * 8)
    for i, b in enumerate(BUNDLE_BASE_KEY):
        baseOffset = i << 3
        for j, k in enumerate(bundle_key):
            final_key[baseOffset + j] = b ^ k
    decrypted_data = bytearray(data)
    klen = len(final_key)
    for i in range(256, len(decrypted_data)):
        decrypted_data[i] ^= final_key[i % klen]
    return bytes(decrypted_data)

conn = apsw.Connection(META_URI, flags=apsw.SQLITE_OPEN_READONLY | apsw.SQLITE_OPEN_URI)
cur = conn.cursor()
cur.execute("""SELECT n, h, e FROM a WHERE n = 'home/data/00000/01/hometimeline_00000_01_1001001'""")
row = cur.fetchone()
n, h, e = row
conn.close()

dat_path = DAT_DIR / h[:2] / h
with open(dat_path, "rb") as f:
    raw = f.read()
dec = decrypt_asset_bundle(raw, e)
env = UnityPy.load(dec)

for obj in env.objects:
    if obj.type.name == "MonoBehaviour":
        try:
            data = obj.read_typetree()
            if isinstance(data, dict) and "Text" in data and "ChoiceDataList" in data:
                text = data.get("Text", "")
                name = data.get("Name", "")
                print(f"Name: {name!r}")
                print(f"Name type: {type(name)}")
                print(f"Name bytes: {name.encode('utf-8') if isinstance(name, str) else name!r}")
                print(f"Text: {text!r}")
                print(f"Text type: {type(text)}")
                print(f"Text len: {len(text)}")
                # Print each char
                for i, c in enumerate(text[:50]):
                    print(f"  [{i}] U+{ord(c):04X} = {c!r}")
                break
        except Exception as ex:
            pass
