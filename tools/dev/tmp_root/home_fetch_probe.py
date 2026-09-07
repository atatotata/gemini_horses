"""Probe v2: Fix ID parsing, find localized files, inspect home bundle structure."""
import json, os, sys
from pathlib import Path
import apsw
import UnityPy

META_KEY = "9c2bab97bcf8c0c4f1a9ea7881a213f6c9ebf9d8d4c6a8e43ce5a259bde7e9fd"
META_URI = f"file:C:/TMP/meta_fresh.bin?hexkey={META_KEY}"
DAT_DIR = Path(r"G:\Games\steamapps\common\UmamusumePrettyDerby_Jpn\UmamusumePrettyDerby_Jpn_Data\Persistent\dat")
BUNDLE_BASE_KEY = bytes.fromhex("532b4631e4a7b9473e7cfb")
GAME_DIR = Path(r"G:\Games\steamapps\common\UmamusumePrettyDerby_Jpn")

# === 1. Meta DB ===
print("="*60)
print("[1] META DB: home/data hometimeline entries")
print("="*60)
conn = apsw.Connection(META_URI, flags=apsw.SQLITE_OPEN_READONLY | apsw.SQLITE_OPEN_URI)
cur = conn.cursor()
cur.execute("""SELECT n, h, e FROM a WHERE n LIKE 'home/data/%/hometimeline_%'""")
meta_rows = cur.fetchall()
print(f"Meta home timeline rows: {len(meta_rows)}")

# Parse all rows
meta_entries = []
for n, h, e in meta_rows:
    parts = n.split("/")
    # home/data/{group}/{sub}/hometimeline_{group}_{sub}_{id}
    filename = parts[-1]  # hometimeline_00000_01_1001001
    stem = filename  # no extension in meta n
    # The unique ID is the filename itself (minus .json ext if present)
    # But for task matching we need the full name stem
    meta_entries.append({"n": n, "h": h, "e": e, "filename": stem, "parts": parts})

print(f"\nFirst 5 entries:")
for e in meta_entries[:5]:
    print(f"  n={e['n']}")
    print(f"    h={e['h'][:20]}... e={e['e']} filename={e['filename']}")

# Check filename patterns
suffixes = set()
for e in meta_entries:
    fn = e["filename"]
    # hometimeline_XXXXXXXXX where X can be alphanumeric
    suffix = fn.replace("hometimeline_", "")
    suffixes.add(suffix)
print(f"\nUnique suffixes: {len(suffixes)}")
# Show some examples
for s in sorted(suffixes)[:10]:
    print(f"  {s}")

# === 2. Find localized files ===
print("\n" + "="*60)
print("[2] FIND LOCALIZED HOME FILES")
print("="*60)

localized_files = {}
localized_names = set()

# Search broadly
for search_root in [
    GAME_DIR / "gemini_horses" / "localized_data" / "assets" / "home",
    GAME_DIR / "hachimi_horses" / "localized_data" / "assets" / "home",
]:
    if search_root.exists():
        for p in search_root.rglob("hometimeline_*.json"):
            name_stem = p.stem  # hometimeline_xxx
            localized_names.add(name_stem)
            localized_files[name_stem] = str(p)
        print(f"  {search_root}: {len(list(search_root.rglob('hometimeline_*.json')))} files")
    else:
        print(f"  NOT FOUND: {search_root}")

# Also check hachimi/gemini repos at other locations
for alt in [
    Path(r"C:\TMP\gemini_horses"),
    Path(r"C:\TMP\hachimi_horses"),
    GAME_DIR / "gemini_horses",
    GAME_DIR / "hachimi_horses",
]:
    if alt.exists():
        for p in alt.rglob("hometimeline_*.json"):
            name_stem = p.stem
            localized_names.add(name_stem)
            localized_files[name_stem] = str(p)
        cnt = len(list(alt.rglob("hometimeline_*.json")))
        if cnt > 0:
            print(f"  {alt}: {cnt} files")

print(f"\nLocalized total: {len(localized_names)}")
for name in sorted(localized_names)[:5]:
    print(f"  {name}: {localized_files[name]}")

# === 3. Compute missing ===
print("\n" + "="*60)
print("[3] MISSING = meta - localized")
print("="*60)
meta_names = {e["filename"] for e in meta_entries}
missing_names = sorted(meta_names - localized_names)
print(f"Meta: {len(meta_names)}")
print(f"Localized: {len(localized_names)}")
print(f"Missing: {len(missing_names)}")
if missing_names:
    print(f"  First 5: {missing_names[:5]}")
    print(f"  Last 5: {missing_names[-5:]}")

# === 4. Build task list with dat probe ===
print("\n" + "="*60)
print("[4] BUILD TASKS + DAT PROBE")
print("="*60)
name_to_meta = {e["filename"]: e for e in meta_entries}

dat_ok = 0
dat_fail = 0
tasks = []
for name in missing_names:
    e = name_to_meta[name]
    h = e["h"]
    dat_path = DAT_DIR / h[:2] / h
    exists = dat_path.exists()
    if exists:
        dat_ok += 1
        tasks.append(e)
    else:
        dat_fail += 1

print(f"Dat OK: {dat_ok}/{len(missing_names)}")
print(f"Dat FAIL: {dat_fail}/{len(missing_names)}")

# === 5. Sample extract on first bundle ===
print("\n" + "="*60)
print("[5] SAMPLE EXTRACT (first 3 bundles)")
print("="*60)

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

for idx, task in enumerate(tasks[:3]):
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
    for obj in env.objects:
        print(f"    type={obj.type.name} path_id={obj.path_id}")
        if obj.type.name == "MonoBehaviour":
            try:
                data = obj.read_typetree()
                if isinstance(data, dict):
                    keys = list(data.keys())
                    print(f"      keys({len(keys)}): {keys}")
                    # Check for any list fields
                    for k, v in data.items():
                        if isinstance(v, list):
                            print(f"        list '{k}' len={len(v)}")
                            if len(v) > 0 and isinstance(v[0], dict):
                                print(f"          first item keys: {list(v[0].keys())[:10]}")
                                # Print first item (truncated)
                                fv = json.dumps(v[0], ensure_ascii=False, default=str)[:200]
                                print(f"          first item: {fv}")
                elif isinstance(data, bytes):
                    print(f"      (bytes data, len={len(data)})")
                else:
                    print(f"      type={type(data).__name__}")
            except Exception as ex:
                print(f"      typetree error: {ex}")
