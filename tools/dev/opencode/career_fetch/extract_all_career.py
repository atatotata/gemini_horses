import os
import sys
import json
import time
import sqlite3
from pathlib import Path
from concurrent.futures import ProcessPoolExecutor, as_completed
import multiprocessing
import UnityPy

GAME_DIR = Path(r"G:/Games/steamapps/common/UmamusumePrettyDerby_Jpn")
DAT_DIR = GAME_DIR / "UmamusumePrettyDerby_Jpn_Data/Persistent/dat"
META_PATH = GAME_DIR / "UmamusumePrettyDerby_Jpn_Data/Persistent/meta"
MASTER_PATH = GAME_DIR / "UmamusumePrettyDerby_Jpn_Data/Persistent/master/master.mdb"
GEMINI_DIR = GAME_DIR / "gemini_horses/localized_data/assets/story/data"
OUT_DIR = Path(r"C:/TMP/opencode/career_fetch")
STORY_JSON_DIR = OUT_DIR / "story_json"

sys.path.insert(0, str(GAME_DIR / "gemini_horses/tools/umamusu-utils/scripts"))
from utils import _derive_decryption_key, DB_KEY, DB_BASE_KEY, dict_factory
import apsw

BUNDLE_BASE_KEY = bytes.fromhex("532b4631e4a7b9473e7cfb")

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

def extract_worker(task):
    # task: (sid, asset_name, h, e, out_json_path)
    sid, asset_name, h, e, out_json_path = task
    
    if os.path.exists(out_json_path):
        return sid, True, "exists"
        
    dat_path = DAT_DIR / h[:2] / h
    if not dat_path.exists():
        return sid, False, "missing_dat"
        
    try:
        with open(dat_path, "rb") as f:
            raw_data = f.read()
            
        dec_bytes = decrypt_asset_bundle(raw_data, e)
        env = UnityPy.load(dec_bytes)
        
        story_data_obj = None
        clip_objects = {}
        
        for obj in env.objects:
            if obj.type.name == "MonoBehaviour":
                try:
                    data = obj.read_typetree()
                    if "BlockList" in data:
                        story_data_obj = data
                    elif "Text" in data and "ChoiceDataList" in data:
                        clip_objects[obj.path_id] = data
                except Exception:
                    pass
                    
        if not story_data_obj:
            return sid, False, "no_story_data"
            
        block_list = story_data_obj.get("BlockList", [])
        
        # Skip dummy block 0!
        extracted_blocks = []
        for blk in block_list[1:]:
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
                            
            extracted_blocks.append({
                "name": blk_name,
                "text": blk_text,
                "choice_data_list": choices
            })
            
        os.makedirs(os.path.dirname(out_json_path), exist_ok=True)
        with open(out_json_path, "w", encoding="utf-8", newline="\n") as f:
            json.dump({
                "no_wrap": True,
                "text_block_list": extracted_blocks
            }, f, ensure_ascii=False, indent=2)
            f.write("\n")
            
        return sid, True, len(extracted_blocks)
    except Exception as ex:
        return sid, False, str(ex)

def main():
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    STORY_JSON_DIR.mkdir(parents=True, exist_ok=True)
    
    tasks_file = OUT_DIR / "tasks.json"
    if tasks_file.exists():
        print(f"Loading cached tasks from {tasks_file}...")
        with open(tasks_file, "r", encoding="utf-8") as f:
            tasks = json.load(f)
    else:
        print("1. Querying master.mdb for career events (gallery_flag 1 & 3)...")
        mconn = sqlite3.connect(str(MASTER_PATH))
        mc = mconn.cursor()
        mc.execute("SELECT story_id, gallery_flag FROM single_mode_story_data WHERE gallery_flag IN (1, 3)")
        rows = mc.fetchall()
        mconn.close()
        
        print(f"Total single_mode_story_data career rows: {len(rows)}")
        
        existing = set()
        for root, dirs, files in os.walk(GEMINI_DIR):
            for f in files:
                if f.startswith("storytimeline_") and f.endswith(".json"):
                    sid = f.replace("storytimeline_", "").replace(".json", "")
                    existing.add(int(sid))
                    
        missing_ids = [sid for sid, flag in rows if sid not in existing]
        print(f"Already translated in gemini_horses: {len(rows) - len(missing_ids)}")
        print(f"Missing career events to extract: {len(missing_ids)}")
        
        print("2. Resolving missing IDs in meta DB...")
        conn = apsw.Connection(str(META_PATH))
        conn.row_trace = dict_factory
        final_key = _derive_decryption_key(DB_KEY, DB_BASE_KEY)
        conn.pragma('cipher', 'chacha20')
        conn.pragma('hexkey', final_key.hex())
        c = conn.cursor()
        
        tasks = []
        missing_meta = []
        
        print("Querying table a for storytimeline paths...")
        meta_map = {}
        for row in c.execute("SELECT n, h, e FROM a WHERE n LIKE 'story/data/%'"):
            n = row['n']
            sid_str = n.split('_')[-1]
            try:
                meta_map[int(sid_str)] = row
            except ValueError:
                pass
                
        conn.close()
        print(f"Indexed {len(meta_map)} story timelines from meta.")
        
        for sid in missing_ids:
            if sid in meta_map:
                row = meta_map[sid]
                n = row['n']
                h = row['h']
                e = row['e']
                parts = n.split('/')
                prefix = parts[2]
                sub = parts[3]
                out_json = STORY_JSON_DIR / prefix / sub / f"storytimeline_{sid}.json"
                tasks.append((sid, n, h, e, str(out_json)))
            else:
                missing_meta.append(sid)
                
        print(f"Resolved tasks: {len(tasks)} / {len(missing_ids)}")
        with open(tasks_file, "w", encoding="utf-8") as f:
            json.dump(tasks, f, indent=2)

    # Multiprocess extract
    workers = min(os.cpu_count() or 4, 8)
    print(f"Starting extraction with {workers} worker processes...")
    t0 = time.time()
    
    success = 0
    failed = 0
    total_blocks = 0
    
    with ProcessPoolExecutor(max_workers=workers) as executor:
        futures = {executor.submit(extract_worker, task): task[0] for task in tasks}
        done = 0
        total = len(futures)
        for fut in as_completed(futures):
            done += 1
            sid, ok, res = fut.result()
            if ok:
                success += 1
                if isinstance(res, int):
                    total_blocks += res
            else:
                failed += 1
                if failed <= 5:
                    print(f"Failed {sid}: {res}")
            if done % 1000 == 0 or done == total:
                elapsed = time.time() - t0
                rate = done / elapsed if elapsed > 0 else 0
                print(f"Progress: {done}/{total} ({done/total*100:.1f}%) | Success: {success}, Fail: {failed} | Rate: {rate:.1f} bundles/s | Blocks: {total_blocks}")
                
    t1 = time.time()
    print(f"\nExtraction completed in {t1-t0:.1f}s!")
    print(f"Total success: {success}, Failed: {failed}, Total blocks: {total_blocks}")

if __name__ == "__main__":
    multiprocessing.freeze_support()
    main()
