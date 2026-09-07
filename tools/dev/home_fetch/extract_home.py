#!/usr/bin/env python3
"""
Home Timeline Bundle Extraction (Local Dat)
============================================
Extract 938 missing home timeline bundles from local dat files.
Same pipeline as career/extra but for home bundles.

Flow:
1. Open meta DB, get all non-resourcelist home/data/hometimeline entries (1441)
2. Subtract localized (503) -> 938 missing
3. For each: read dat/{h[:2]}/{h}, decrypt with BUNDLE_BASE_KEY XOR e
4. Extract BlockList[1:] -> TextTrack -> ClipList -> Name/Text/ChoiceDataList
5. Save JSON with {text_block_list, no_wrap}
"""
import json
import os
import sys
import time
from pathlib import Path
from concurrent.futures import ThreadPoolExecutor, as_completed
import apsw
import UnityPy

# ============ KEYS ============
META_KEY = "9c2bab97bcf8c0c4f1a9ea7881a213f6c9ebf9d8d4c6a8e43ce5a259bde7e9fd"
META_URI = f"file:C:/TMP/meta_fresh.bin?hexkey={META_KEY}"
BUNDLE_BASE_KEY = bytes.fromhex("532b4631e4a7b9473e7cfb")

# ============ PATHS ============
DAT_DIR = Path(r"G:\Games\steamapps\common\UmamusumePrettyDerby_Jpn\UmamusumePrettyDerby_Jpn_Data\Persistent\dat")
GAME_DIR = Path(r"G:\Games\steamapps\common\UmamusumePrettyDerby_Jpn")
LOCALIZED_BASE = GAME_DIR / "gemini_horses" / "localized_data" / "assets" / "home" / "data"
OUT_DIR = Path(r"C:\TMP\home_fetch\story_json\home")
MANIFEST_PATH = Path(r"C:\TMP\home_fetch\extraction_summary.json")

WORKERS = 8

# ============ DECRYPT ============
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

# ============ EXTRACT ============
def extract_home_timeline(dec_data: bytes, basename: str):
    """Extract home timeline text from decrypted bundle."""
    env = UnityPy.load(dec_data)

    story_data_obj = None
    clip_objects = {}

    for obj in env.objects:
        if obj.type.name == "MonoBehaviour":
            try:
                data = obj.read_typetree()
                if isinstance(data, dict):
                    if "BlockList" in data:
                        story_data_obj = data
                    elif "Text" in data and "ChoiceDataList" in data:
                        clip_objects[obj.path_id] = data
            except Exception:
                pass

    if not story_data_obj:
        raise ValueError(f"No BlockList found in {basename}")

    block_list = story_data_obj.get("BlockList", [])
    title = story_data_obj.get("Title", "")

    extracted_blocks = []
    for blk in block_list[1:]:  # Skip dummy block 0
        tt = blk.get("TextTrack", {})
        clips = tt.get("ClipList", [])
        blk_name = ""
        blk_text = ""
        choices = []

        for c_ref in clips:
            pid = c_ref.get("m_PathID")
            clip_data = clip_objects.get(pid)
            if clip_data:
                cname = clip_data.get("Name", "")
                if cname is not None and cname != "":
                    blk_name = cname
                ctext = clip_data.get("Text", "")
                if ctext:
                    blk_text = ctext if not blk_text else blk_text + "\n" + ctext
                for c_item in clip_data.get("ChoiceDataList", []):
                    ct = c_item.get("Text", "")
                    if ct:
                        choices.append(ct)

        block_dict = {}
        if blk_name:
            block_dict["name"] = blk_name
        if blk_text:
            block_dict["text"] = blk_text
        if choices:
            block_dict["choice_data_list"] = choices
        extracted_blocks.append(block_dict)

    result = {"text_block_list": extracted_blocks, "no_wrap": True}
    if title:
        result["title"] = title
    return result

# ============ WORKER ============
def extract_worker(task):
    """Worker: decrypt + extract one bundle."""
    filename = task["filename"]
    h = task["h"]
    e = task["e"]
    out_json = task["out_json"]

    if os.path.exists(out_json):
        return (filename, True, "exists", 0, 0)

    dat_path = DAT_DIR / h[:2] / h
    if not dat_path.exists():
        return (filename, False, "missing_dat", 0, 0)

    try:
        with open(dat_path, "rb") as f:
            raw_data = f.read()

        dec_data = decrypt_asset_bundle(raw_data, e)
        result = extract_home_timeline(dec_data, filename)

        # Save
        os.makedirs(os.path.dirname(out_json), exist_ok=True)
        with open(out_json, "w", encoding="utf-8", newline="\n") as f:
            json.dump(result, f, ensure_ascii=False, indent=2)

        nb = len(result["text_block_list"])
        nc = sum(len(b.get("choice_data_list", [])) for b in result["text_block_list"])
        return (filename, True, "ok", nb, nc)
    except Exception as ex:
        return (filename, False, str(ex), 0, 0)

# ============ MAIN ============
def main():
    t0 = time.time()
    print("=" * 60)
    print("Home Timeline Bundle Extraction (Local Dat)")
    print("=" * 60)

    # 1. Open meta
    print("\n[1] Opening meta DB...")
    conn = apsw.Connection(META_URI, flags=apsw.SQLITE_OPEN_READONLY | apsw.SQLITE_OPEN_URI)
    cur = conn.cursor()

    cur.execute("""SELECT n, h, e FROM a WHERE n LIKE 'home/data/%/hometimeline_%' AND n NOT LIKE '%resourcelist%'""")
    meta_rows = cur.fetchall()
    print(f"  Non-resourcelist hometimeline entries: {len(meta_rows)}")

    meta_entries = []
    for n, h, e in meta_rows:
        filename = n.split("/")[-1]
        meta_entries.append({"n": n, "h": h, "e": e, "filename": filename})
    conn.close()

    # 2. Localized
    print("\n[2] Checking localized files...")
    localized_names = set()
    if LOCALIZED_BASE.exists():
        for p in LOCALIZED_BASE.rglob("hometimeline_*.json"):
            localized_names.add(p.stem)
    print(f"  Already localized: {len(localized_names)}")

    # 3. Missing
    meta_names = {e["filename"] for e in meta_entries}
    missing_names = sorted(meta_names - localized_names)
    print(f"  Missing (to extract): {len(missing_names)}")

    # 4. Build tasks
    print("\n[3] Building tasks + dat probe...")
    name_to_meta = {e["filename"]: e for e in meta_entries}
    tasks = []
    dat_fail = 0
    for name in missing_names:
        e = name_to_meta[name]
        dat_path = DAT_DIR / e["h"][:2] / e["h"]
        # Build output path: mirror the meta path structure
        # n = home/data/00000/01/hometimeline_00000_01_1001001
        parts = e["n"].split("/")
        # parts: ['home', 'data', '00000', '01', 'hometimeline_...']
        rel_path = "/".join(parts[1:])  # data/00000/01/hometimeline_...
        out_json = str(OUT_DIR / (rel_path + ".json"))
        e["out_json"] = out_json

        if dat_path.exists():
            tasks.append(e)
        else:
            dat_fail += 1

    print(f"  Tasks with local dat: {len(tasks)}")
    print(f"  Dat missing: {dat_fail}")

    if dat_fail > 0:
        print(f"  WARNING: {dat_fail} bundles have no local dat file!")

    # 5. Extract
    print(f"\n[4] Extracting {len(tasks)} bundles ({WORKERS} workers)...")
    success = 0
    failed = 0
    total_blocks = 0
    total_choices = 0
    extract_errors = []

    with ThreadPoolExecutor(max_workers=WORKERS) as executor:
        futures = {executor.submit(extract_worker, task): task for task in tasks}
        done = 0
        total = len(futures)
        for fut in as_completed(futures):
            done += 1
            filename, ok, status, nb, nc = fut.result()
            if ok:
                success += 1
                total_blocks += nb
                total_choices += nc
            else:
                failed += 1
                extract_errors.append({"filename": filename, "error": status})
                if failed <= 10:
                    print(f"  FAIL {filename}: {status}")
            if done % 100 == 0 or done == total:
                elapsed = time.time() - t0
                rate = done / elapsed if elapsed > 0 else 0
                print(f"  Progress: {done}/{total} ({done/total*100:.1f}%) | OK: {success} Fail: {failed} | {rate:.1f} bundles/s | Blocks: {total_blocks}")

    t1 = time.time()

    # 6. Report
    print(f"\n{'='*60}")
    print(f"EXTRACTION COMPLETE in {t1-t0:.1f}s")
    print(f"{'='*60}")
    print(f"  Meta hexkey: {META_KEY}")
    print(f"  Meta total (non-RL): {len(meta_rows)}")
    print(f"  Already localized: {len(localized_names)}")
    print(f"  Extracted new: {success}")
    print(f"  Failed: {failed}")
    print(f"  Total blocks: {total_blocks}")
    print(f"  Total choices: {total_choices}")

    # Count actual output files
    out_count = len(list(OUT_DIR.rglob("hometimeline_*.json")))
    print(f"  Output file count: {out_count}")

    if extract_errors:
        print(f"\n  Extract errors ({len(extract_errors)}):")
        for ee in extract_errors[:20]:
            print(f"    {ee['filename']}: {ee['error']}")

    # 7. Write manifest
    manifest = {
        "meta_hexkey": META_KEY,
        "meta_total_non_rl": len(meta_rows),
        "already_localized": len(localized_names),
        "extracted_new": success,
        "failed": failed,
        "dat_missing": dat_fail,
        "total_blocks": total_blocks,
        "total_choices": total_choices,
        "output_file_count": out_count,
        "elapsed_seconds": round(t1 - t0, 2),
        "extract_errors": extract_errors,
        "tasks": [{"filename": t["filename"], "n": t["n"], "out_json": t["out_json"]} for t in tasks]
    }
    with open(MANIFEST_PATH, "w", encoding="utf-8") as f:
        json.dump(manifest, f, indent=2, ensure_ascii=False)
    print(f"\n  Manifest: {MANIFEST_PATH}")
    print("=" * 60)

if __name__ == "__main__":
    main()
