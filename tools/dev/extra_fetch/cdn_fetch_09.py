#!/usr/bin/env python3
"""
CDN Fetch + Extract Story Event 09 Missing Bundles
=====================================================
Fetch 198 missing Story Event 09 bundles from Akamai CDN,
decrypt them, extract TextTrack dialogue, save JSONs.

Flow:
1. Open meta DB, get all prefix-09 type=1 story_event_story_data IDs
2. Compute missing = all_09_type1 - localized - already_extracted
3. For each missing: query meta for hash h and key e
4. Download from CDN: {platform}/assetbundles/{h[:2]}/{h}
5. Decrypt bundle: BUNDLE_BASE_KEY XOR key, then XOR from byte 256
6. Extract MonoBehaviour BlockList[1:] -> TextTrack -> ClipList -> text
7. Save JSON with {title, text_block_list, no_wrap}
"""
import json
import os
import sys
import time
import io
import struct
import urllib.request
import urllib.error
from pathlib import Path
from concurrent.futures import ThreadPoolExecutor, as_completed
import apsw
import UnityPy

# ============ KEYS ============
DB_KEY = "9c2bab97bcf8c0c4f1a9ea7881a213f6c9ebf9d8d4c6a8e43ce5a259bde7e9fd"
BUNDLE_BASE_KEY = "532b4631e4a7b9473e7cfb"

# ============ PATHS ============
META_PATH = Path(r"G:\Games\steamapps\common\UmamusumePrettyDerby_Jpn\UmamusumePrettyDerby_Jpn_Data\Persistent\meta")
MASTER_PATH = Path(r"G:\Games\steamapps\common\UmamusumePrettyDerby_Jpn\UmamusumePrettyDerby_Jpn_Data\Persistent\master\master.mdb")
LOCALIZED_BASE = Path(r"G:\Games\steamapps\common\UmamusumePrettyDerby_Jpn\gemini_horses\localized_data\assets\story\data")
OUT_BASE = Path(r"C:\TMP\extra_fetch\story_json")
CDN_CACHE = Path(r"C:\TMP\extra_fetch\cdn_09")
MANIFEST_PATH = Path(r"C:\TMP\extra_fetch\cdn_fetch_09.json")

CDN_URL = "https://prd-storage-game-umamusume.akamaized.net/dl/resources/{}/assetbundles/{}/{}"
CDN_URL_FALLBACK = "https://prd-storage-game-umamusume.akamaized.net/generichosts/dl/resources/{}/assetbundles/{}/{}"

# Thread/worker settings
CDN_WORKERS = 8
TIMEOUT = 30

# ============ DECRYPT ============
def create_final_key(key: int) -> bytes:
    """Create final XOR key from base key and bundle key."""
    base_key = bytes.fromhex(BUNDLE_BASE_KEY)
    bundle_key = key.to_bytes(8, byteorder="little", signed=True)
    base_len = len(base_key)
    final_key = bytearray(base_len * 8)
    for i, b in enumerate(base_key):
        baseOffset = i << 3
        for j, k in enumerate(bundle_key):
            final_key[baseOffset + j] = b ^ k
    return bytes(final_key)

def decrypt_asset_bundle(data: bytes, key: int) -> bytes:
    """Decrypt asset bundle bytes from byte 256 onward."""
    if len(data) < 256:
        return data
    final_key = create_final_key(key)
    decrypted = bytearray(data)
    for i in range(256, len(decrypted)):
        decrypted[i] ^= final_key[i % len(final_key)]
    return bytes(decrypted)

# ============ META DB ============
def open_meta_db():
    """Open encrypted meta DB."""
    uri = f"file:{META_PATH}?hexkey={DB_KEY}"
    db = apsw.Connection(uri, flags=apsw.SQLITE_OPEN_READONLY | apsw.SQLITE_OPEN_URI)
    return db

def get_platform(db):
    """Get platform string from meta."""
    try:
        cur = db.cursor()
        row = cur.execute("SELECT n FROM a LIMIT 1").fetchone()
        if row and row[0].startswith("dat/"):
            return row[0][4:6]
    except Exception:
        pass
    return "Windows"

def get_all_09_type1_ids(master_db):
    """Get all story_event_story_data IDs with type=1 that have prefix 09."""
    cur = master_db.cursor()
    # Get schema
    cols = [c[1] for c in cur.execute('PRAGMA table_info("story_event_story_data")').fetchall()]
    # Find story_type_* and story_id_* pairs
    types = [c for c in cols if c.startswith("story_type")]
    ids = set()
    for t in types:
        num = t.split("_")[-1]
        id_col = f"story_id_{num}"
        if id_col in cols:
            rows = cur.execute(
                f'SELECT "{id_col}" FROM "story_event_story_data" WHERE "{t}"=1 AND "{id_col}"!=0'
            ).fetchall()
            for r in rows:
                sid = r[0]
                sid_str = str(sid).zfill(9)
                if sid_str.startswith("09"):
                    ids.add(sid)
    return sorted(ids)

def get_localized_09_ids():
    """Get already localized prefix-09 story IDs."""
    ids = set()
    if LOCALIZED_BASE.exists():
        for p in LOCALIZED_BASE.rglob("storytimeline_*.json"):
            try:
                sid = int(p.stem.split("_")[1])
                if str(sid).zfill(9).startswith("09"):
                    ids.add(sid)
            except (IndexError, ValueError):
                pass
    return ids

def get_already_extracted_09_ids():
    """Get already extracted 09 IDs from OUT_BASE/09/."""
    ids = set()
    dir09 = OUT_BASE / "09"
    if dir09.exists():
        for p in dir09.rglob("storytimeline_*.json"):
            try:
                sid = int(p.stem.split("_")[1])
                ids.add(sid)
            except (IndexError, ValueError):
                pass
    return ids

def query_meta_for_tasks(meta_db, sids):
    """Query meta DB for hash h and key e for each SID."""
    cur = meta_db.cursor()
    tasks = []
    for sid in sids:
        sid_str = str(sid).zfill(9)
        path = f"story/data/{sid_str[:2]}/{sid_str[2:6]}/storytimeline_{sid_str}"
        row = cur.execute("SELECT h, e FROM a WHERE n = ?", (path,)).fetchone()
        if row:
            h, e = row
            sub = sid_str[2:6]
            out_json = OUT_BASE / "09" / sub / f"storytimeline_{sid_str}.json"
            tasks.append({
                "sid": sid,
                "n": path,
                "h": h,
                "e": e,
                "sub": sub,
                "out_json": str(out_json),
            })
        else:
            print(f"  WARNING: SID {sid} not found in meta: {path}")
    return tasks

# ============ CDN FETCH ============
def fetch_one(task):
    """Download one bundle from CDN. Returns (task, data_or_status, bytes)."""
    h = task["h"]
    sid = task["sid"]
    prefix = h[:2]
    url = CDN_URL.format("Windows", prefix, h)
    url_fallback = CDN_URL_FALLBACK.format("Windows", prefix, h)
    
    # Cache path
    cache_path = CDN_CACHE / h
    if cache_path.exists() and cache_path.stat().st_size > 0:
        data = cache_path.read_bytes()
        return (task, data, len(data), "cached")
    
    for attempt_url in [url, url_fallback]:
        try:
            req = urllib.request.Request(attempt_url)
            with urllib.request.urlopen(req, timeout=TIMEOUT) as resp:
                data = resp.read()
                # Cache
                CDN_CACHE.mkdir(parents=True, exist_ok=True)
                cache_path.write_bytes(data)
                return (task, data, len(data), "downloaded")
        except urllib.error.HTTPError as e:
            if e.code == 404:
                return (task, None, 0, f"404")
            continue
        except Exception as e:
            continue
    
    return (task, None, 0, "failed_all")

def fetch_all(tasks):
    """Download all tasks in parallel."""
    results = []
    with ThreadPoolExecutor(max_workers=CDN_WORKERS) as pool:
        futures = {pool.submit(fetch_one, t): t for t in tasks}
        done = 0
        for future in as_completed(futures):
            done += 1
            result = future.result()
            task, data, nbytes, status = result
            if done % 20 == 0 or status.startswith("4"):
                print(f"  [{done}/{len(tasks)}] SID {task['sid']}: {status} ({nbytes} bytes)")
            results.append(result)
    return results

# ============ TEXT EXTRACTION ============
def extract_story_json(dec_data, storyline_basename=None):
    """Extract story text from decrypted bundle."""
    env = UnityPy.load(io.BytesIO(dec_data))
    
    timeline_tree = None
    clip_objects = {}
    
    for obj in env.objects:
        if obj.type.name != 'MonoBehaviour':
            continue
        try:
            tree = obj.read_typetree()
            if not tree or not isinstance(tree, dict):
                continue
            if 'BlockList' in tree:
                if storyline_basename and tree.get('m_Name') == storyline_basename:
                    timeline_tree = tree
                elif not timeline_tree:
                    timeline_tree = tree
            else:
                clip_objects[obj.path_id] = tree
        except Exception:
            pass
    
    if not timeline_tree:
        raise ValueError(f"Could not find MonoBehaviour with BlockList (basename={storyline_basename})")
    
    title = timeline_tree.get('Title') or ''
    text_block_list = []
    
    # Skip first block (dummy 0) per task spec
    blocks = timeline_tree.get('BlockList', [])
    for block in blocks[1:]:
        block_dict = {}
        tt = block.get('TextTrack')
        if tt:
            clips = tt.get('ClipList', [])
            for clip in clips:
                pid = clip.get('m_PathID')
                if pid and pid in clip_objects:
                    c = clip_objects[pid]
                    name = c.get('Name') or ''
                    text = c.get('Text') or ''
                    choices = [ch.get('Text', '') for ch in c.get('ChoiceDataList', []) if ch.get('Text')]
                    
                    if name:
                        block_dict['name'] = name
                    if text:
                        block_dict['text'] = text
                    if choices:
                        block_dict['choice_data_list'] = choices
                    break
        text_block_list.append(block_dict)
    
    return {
        'title': title,
        'text_block_list': text_block_list,
        'no_wrap': True
    }

# ============ MAIN ============
def main():
    t0 = time.time()
    print("=" * 60)
    print("CDN Fetch + Extract Story Event 09 Missing Bundles")
    print("=" * 60)
    
    # 1. Open databases
    print("\n[1] Opening databases...")
    meta_db = open_meta_db()
    platform = get_platform(meta_db)
    print(f"  Platform: {platform}")
    
    master_db = apsw.Connection(str(MASTER_PATH), flags=apsw.SQLITE_OPEN_READONLY)
    
    # 2. Compute missing SIDs
    print("\n[2] Computing missing 09 SIDs...")
    all_09_type1 = get_all_09_type1_ids(master_db)
    print(f"  All prefix-09 type=1 IDs: {len(all_09_type1)}")
    
    localized = get_localized_09_ids()
    print(f"  Already localized: {len(localized)}")
    
    already_extracted = get_already_extracted_09_ids()
    print(f"  Already extracted locally: {len(already_extracted)}")
    
    # Also check 04/10 extraction dirs not to touch
    skip_dirs = set()
    for prefix in ["04", "10"]:
        pdir = OUT_BASE / prefix
        if pdir.exists():
            for f in pdir.rglob("storytimeline_*.json"):
                try:
                    skip_dirs.add(int(f.stem.split("_")[1]))
                except:
                    pass
    
    already = localized | already_extracted | skip_dirs
    missing = sorted(set(all_09_type1) - already)
    print(f"  Missing (to fetch): {len(missing)}")
    
    # Verify count = 198 (or report)
    if len(missing) != 198:
        print(f"  NOTE: Expected 198 missing, got {len(missing)}")
    
    # 3. Query meta for hash/key
    print("\n[3] Querying meta DB for hash+key...")
    tasks = query_meta_for_tasks(meta_db, missing)
    print(f"  Tasks with meta rows: {len(tasks)}")
    
    if len(tasks) != len(missing):
        missing_in_meta = set(missing) - {t["sid"] for t in tasks}
        print(f"  WARNING: {len(missing_in_meta)} SIDs not found in meta: {sorted(missing_in_meta)[:10]}")
    
    meta_db.close()
    master_db.close()
    
    # 4. Download from CDN
    print(f"\n[4] Downloading {len(tasks)} bundles from CDN ({CDN_WORKERS} workers)...")
    CDN_CACHE.mkdir(parents=True, exist_ok=True)
    dl_results = fetch_all(tasks)
    
    # Tally
    downloaded = [(t, d, n) for t, d, n, s in dl_results if d is not None]
    failed_404 = [(t, s) for t, d, n, s in dl_results if s == "404"]
    failed_other = [(t, s) for t, d, n, s in dl_results if d is None and s != "404"]
    print(f"\n  Downloaded: {len(downloaded)}")
    print(f"  404 errors: {len(failed_404)}")
    print(f"  Other failures: {len(failed_other)}")
    
    if failed_404:
        print(f"  404 SIDs: {[t['sid'] for t, _ in failed_404]}")
    if failed_other:
        print(f"  Failed SIDs: {[t['sid'] for t, _ in failed_other]}")
    
    # 5. Decrypt + Extract
    print(f"\n[5] Decrypting + extracting {len(downloaded)} bundles...")
    manifest = []
    total_blocks = 0
    total_choices = 0
    extracted_count = 0
    extract_failed = []
    
    for task, raw_data, nbytes in downloaded:
        sid = task["sid"]
        e = task["e"]
        sid_str = str(sid).zfill(9)
        out_json = Path(task["out_json"])
        
        try:
            dec_data = decrypt_asset_bundle(raw_data, e)
            result = extract_story_json(dec_data, f"storytimeline_{sid_str}")
            
            # Save
            out_json.parent.mkdir(parents=True, exist_ok=True)
            with open(out_json, 'w', encoding='utf-8', newline='\n') as f:
                json.dump(result, f, ensure_ascii=False, indent=2)
            
            bl = result['text_block_list']
            nb = len(bl)
            nc = sum(len(b.get('choice_data_list', [])) for b in bl)
            total_blocks += nb
            total_choices += nc
            extracted_count += 1
            
            manifest.append({
                "sid": sid,
                "path": str(out_json),
                "hash": task["h"],
                "bytes": nbytes,
                "blocks": nb,
                "choices": nc,
                "status": "ok"
            })
        except Exception as ex:
            extract_failed.append({"sid": sid, "error": str(ex)})
            manifest.append({
                "sid": sid,
                "path": str(out_json),
                "hash": task["h"],
                "bytes": nbytes,
                "blocks": 0,
                "choices": 0,
                "status": f"extract_error: {ex}"
            })
    
    # Add 404/failed entries to manifest
    for task, status in failed_404:
        manifest.append({
            "sid": task["sid"],
            "path": task["out_json"],
            "hash": task["h"],
            "bytes": 0,
            "blocks": 0,
            "choices": 0,
            "status": "404_not_found"
        })
    for task, status in failed_other:
        manifest.append({
            "sid": task["sid"],
            "path": task["out_json"],
            "hash": task["h"],
            "bytes": 0,
            "blocks": 0,
            "choices": 0,
            "status": f"download_{status}"
        })
    
    t1 = time.time()
    
    # 6. Report
    print(f"\n{'=' * 60}")
    print(f"EXTRACTION COMPLETE in {t1 - t0:.1f}s")
    print(f"{'=' * 60}")
    print(f"  Total tasks: {len(tasks)}")
    print(f"  Successfully extracted: {extracted_count}")
    print(f"  Extract errors: {len(extract_failed)}")
    print(f"  404 not found: {len(failed_404)}")
    print(f"  Download failures: {len(failed_other)}")
    print(f"  Total blocks: {total_blocks}")
    print(f"  Total choices: {total_choices}")
    
    if extract_failed:
        print(f"\n  Extract errors:")
        for ef in extract_failed:
            print(f"    SID {ef['sid']}: {ef['error']}")
    
    # Count expected total: existing 09 + new 09
    existing_09_count = len(get_already_extracted_09_ids()) + len(already_extracted)
    # Note: already_extracted is included in get_already, but let's just count dir
    dir09 = OUT_BASE / "09"
    final_09_count = len(list(dir09.rglob("storytimeline_*.json"))) if dir09.exists() else 0
    dir10_count = len(list((OUT_BASE / "10").rglob("storytimeline_*.json"))) if (OUT_BASE / "10").exists() else 0
    dir14_count = len(list((OUT_BASE / "14").rglob("storytimeline_*.json"))) if (OUT_BASE / "14").exists() else 0
    seasonal_count = dir10_count + dir14_count
    
    print(f"\n  Final 09 file count: {final_09_count}")
    print(f"  Seasonal (10+14): {seasonal_count}")
    print(f"  Combined 09+seasonal: {final_09_count + seasonal_count}")
    print(f"  Expected combined: 202+22=224 (minus any 404: {len(failed_404)})")
    
    # 7. Write manifest
    manifest.sort(key=lambda x: x["sid"])
    with open(MANIFEST_PATH, 'w', encoding='utf-8') as f:
        json.dump({
            "total": len(manifest),
            "extracted_ok": extracted_count,
            "extract_errors": len(extract_failed),
            "not_found_404": len(failed_404),
            "download_failed": len(failed_other),
            "total_blocks": total_blocks,
            "total_choices": total_choices,
            "seasonal_files": seasonal_count,
            "event_09_files": final_09_count,
            "combined_expected": final_09_count + seasonal_count,
            "tasks": manifest
        }, f, indent=2, ensure_ascii=False)
    print(f"\n  Manifest written: {MANIFEST_PATH}")
    print("=" * 60)

if __name__ == "__main__":
    main()
