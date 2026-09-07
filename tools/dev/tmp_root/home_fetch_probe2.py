"""Probe v4: Extract actual hometimeline bundles (non-resourcelist)."""
import json, os, sys
from pathlib import Path
import apsw
import UnityPy

META_KEY = "9c2bab97bcf8c0c4f1a9ea7881a213f6c9ebf9d8d4c6a8e43ce5a259bde7e9fd"
META_URI = f"file:C:/TMP/meta_fresh.bin?hexkey={META_KEY}"
DAT_DIR = Path(r"G:\Games\steamapps\common\UmamusumePrettyDerby_Jpn\UmamusumePrettyDerby_Jpn_Data\Persistent\dat")
BUNDLE_BASE_KEY = bytes.fromhex("532b4631e4a7b9473e7cfb")
GAME_DIR = Path(r"G:\Games\steamapps\common\UmamusumePrettyDerby_Jpn")

conn = apsw.Connection(META_URI, flags=apsw.SQLITE_OPEN_READONLY | apsw.SQLITE_OPEN_URI)
cur = conn.cursor()

# Get non-resourcelist hometimeline entries only
cur.execute("""SELECT n, h, e FROM a WHERE n LIKE 'home/data/%/hometimeline_%' AND n NOT LIKE '%resourcelist%'""")
meta_rows = cur.fetchall()
print(f"Non-resourcelist hometimeline meta rows: {len(meta_rows)}")

# Localized
loc_base = GAME_DIR / "gemini_horses" / "localized_data" / "assets" / "home" / "data"
localized_names = set()
localized_files = {}
for p in loc_base.rglob("hometimeline_*.json"):
    name_stem = p.stem
    localized_names.add(name_stem)
    localized_files[name_stem] = str(p)
print(f"Localized: {len(localized_names)}")

# Missing
meta_entries = []
for n, h, e in meta_rows:
    # n = home/data/00000/01/hometimeline_00000_01_1001001
    # stem = hometimeline_00000_01_1001001
    filename = n.split("/")[-1]
    meta_entries.append({"n": n, "h": h, "e": e, "filename": filename})

meta_names = {e["filename"] for e in meta_entries}
missing_names = sorted(meta_names - localized_names)
print(f"Missing: {len(missing_names)}")
print(f"  First 5: {missing_names[:5]}")

# Build tasks
name_to_meta = {e["filename"]: e for e in meta_entries}
dat_ok = 0
dat_fail = 0
tasks = []
for name in missing_names:
    e = name_to_meta[name]
    h = e["h"]
    dat_path = DAT_DIR / h[:2] / h
    if dat_path.exists():
        dat_ok += 1
        tasks.append(e)
    else:
        dat_fail += 1
print(f"Dat OK: {dat_ok}/{len(missing_names)}, FAIL: {dat_fail}")

# Decrypt+extract first 5
def decrypt_asset_bundle(data: bytes, key: int) -> bytes:
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

print(f"\n{'='*60}")
print("SAMPLE EXTRACT (first 5 non-resourcelist)")
print(f"{'='*60}")

for idx, task in enumerate(tasks[:5]):
    h = task["h"]
    e = task["e"]
    n = task["n"]
    dat_path = DAT_DIR / h[:2] / h
    
    print(f"\n--- [{idx+1}] {n} ---")
    with open(dat_path, "rb") as f:
        raw = f.read()
    print(f"  Raw: {len(raw)} bytes")
    
    dec = decrypt_asset_bundle(raw, e)
    print(f"  Decrypted: {len(dec)} bytes")
    
    env = UnityPy.load(dec)
    
    print(f"  Objects: {len(env.objects)}")
    story_data_obj = None
    clip_objects = {}
    all_mono = []
    
    for obj in env.objects:
        if obj.type.name == "MonoBehaviour":
            try:
                data = obj.read_typetree()
                if isinstance(data, dict):
                    keys = list(data.keys())
                    all_mono.append((obj.path_id, keys))
                    if "BlockList" in data:
                        story_data_obj = data
                    elif "Text" in data and "ChoiceDataList" in data:
                        clip_objects[obj.path_id] = data
            except Exception as ex:
                all_mono.append((obj.path_id, f"ERROR: {ex}"))
    
    for pid, keys in all_mono:
        print(f"    MB path_id={pid}: {keys}")
    
    if story_data_obj:
        block_list = story_data_obj.get("BlockList", [])
        print(f"  FOUND BlockList: {len(block_list)} blocks, {len(clip_objects)} clips")
        
        # Extract blocks[1:]
        for bi, blk in enumerate(block_list[1:4]):  # Show first 3 blocks
            tt = blk.get("TextTrack", {})
            clips = tt.get("ClipList", [])
            print(f"    Block[{bi+1}]: ClipList len={len(clips)}")
            for c_ref in clips[:3]:
                pid = c_ref.get("m_PathID")
                cd = clip_objects.get(pid)
                if cd:
                    name = cd.get("Name", "")
                    text = cd.get("Text", "")[:80]
                    choices = cd.get("ChoiceDataList", [])
                    print(f"      Clip: Name={name}, Text={text!r}, Choices={len(choices)}")
    else:
        print(f"  NO BlockList found")
        # Show first MB full data
        if all_mono:
            pid, keys = all_mono[0]
            for obj in env.objects:
                if obj.type.name == "MonoBehaviour" and obj.path_id == pid:
                    try:
                        data = obj.read_typetree()
                        print(f"  First MB full data keys: {list(data.keys())}")
                        for k, v in data.items():
                            if isinstance(v, list):
                                print(f"    {k}: list[{len(v)}]")
                                if v:
                                    sample = json.dumps(v[0], ensure_ascii=False, default=str)[:200]
                                    print(f"      first: {sample}")
                            else:
                                print(f"    {k}: {type(v).__name__} = {str(v)[:80]}")
                    except Exception as ex:
                        print(f"    Error: {ex}")

# Also check existing localized file for schema reference
print(f"\n{'='*60}")
print("EXISTING LOCALIZED FILE SAMPLE")
print(f"{'='*60}")
if localized_files:
    first_loc = sorted(localized_files.keys())[0]
    fpath = localized_files[first_loc]
    print(f"File: {fpath}")
    with open(fpath, 'r', encoding='utf-8') as f:
        data = json.load(f)
    print(f"Top keys: {list(data.keys())}")
    for k, v in data.items():
        if isinstance(v, list):
            print(f"  {k}: list[{len(v)}]")
            if v:
                print(f"    first item keys: {list(v[0].keys()) if isinstance(v[0], dict) else type(v[0])}")
                sample = json.dumps(v[0], ensure_ascii=False, default=str)[:300]
                print(f"    first item: {sample}")
        else:
            print(f"  {k}: {str(v)[:100]}")

conn.close()
