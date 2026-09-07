"""
Extract 09 Story Event bundles — same pipeline as career/seasonal.
Only extracts sids that have local dat bundles.
"""
import os, sys, json, time
from pathlib import Path
from concurrent.futures import ProcessPoolExecutor, as_completed
import multiprocessing

sys.path.insert(0, r'G:\Games\steamapps\common\UmamusumePrettyDerby_Jpn\gemini_horses\tools\umamusu-utils\scripts')
from utils import _derive_decryption_key, DB_KEY, DB_BASE_KEY, dict_factory
import apsw
import UnityPy

GAME_DIR = Path(r"G:/Games/steamapps/common/UmamusumePrettyDerby_Jpn")
DAT_DIR = GAME_DIR / "UmamusumePrettyDerby_Jpn_Data/Persistent/dat"
META_PATH = GAME_DIR / "UmamusumePrettyDerby_Jpn_Data/Persistent/meta"
OUT_BASE = Path(r"C:/TMP/extra_fetch/story_json")

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
    # Load resolve results
    with open(OUT_BASE / "analysis_09.json", "r", encoding="utf-8") as f:
        analysis = json.load(f)

    missing_with_dat = analysis['missing_202_with_dat']
    missing_no_dat = analysis['missing_202_no_dat']

    print(f"Missing 202 breakdown: {len(missing_with_dat)} with dat, {len(missing_no_dat)} without dat")

    # Build tasks for the ones that HAVE dat files
    # Load meta info
    conn = apsw.Connection(str(META_PATH))
    conn.row_trace = dict_factory
    final_key = _derive_decryption_key(DB_KEY, DB_BASE_KEY)
    conn.pragma('cipher', 'chacha20')
    conn.pragma('hexkey', final_key.hex())
    c = conn.cursor()

    meta_09 = {}
    for row in c.execute("SELECT n, h, e FROM a WHERE n LIKE 'story/data/09/%storytimeline_%' AND n NOT LIKE '%resourcelist%'"):
        n = row['n']
        sid_str = n.split('_')[-1]
        try:
            meta_09[int(sid_str)] = row
        except ValueError:
            pass
    conn.close()

    tasks = []
    for sid in missing_with_dat:
        row = meta_09[sid]
        n = row['n']
        h = row['h']
        e = row['e']
        parts = n.split('/')
        prefix = parts[2]
        sub = parts[3]
        out_json = OUT_BASE / prefix / sub / f"storytimeline_{sid}.json"
        tasks.append((sid, n, h, e, str(out_json)))

    print(f"Extraction tasks (with dat): {len(tasks)}")

    # Also build tasks for ALL missing 202 to see which we can't do
    all_missing_tasks = []
    for sid in sorted(set(analysis['missing_202'])):
        if sid in meta_09:
            row = meta_09[sid]
            n = row['n']
            h = row['h']
            e = row['e']
            parts = n.split('/')
            prefix = parts[2]
            sub = parts[3]
            out_json = OUT_BASE / prefix / sub / f"storytimeline_{sid}.json"
            all_missing_tasks.append((sid, n, h, e, str(out_json)))

    # Extract what we can
    if not tasks:
        print("No bundles available locally for extraction!")
        summary = {
            'attempted': 0,
            'success': 0,
            'failed': 0,
            'skipped_exists': 0,
            'no_dat': len(missing_no_dat),
            'total_blocks': 0,
            'total_choices': 0,
            'files': [],
            'failed_list': [],
        }
    else:
        workers = min(os.cpu_count() or 4, 8)
        print(f"Starting extraction with {workers} worker processes...")
        t0 = time.time()

        success = 0
        failed = 0
        total_blocks = 0
        total_choices = 0
        files = []
        failed_list = []

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
                        # Count choices from the file
                        task = [t for t in tasks if t[0] == sid][0]
                        files.append({
                            'sid': sid,
                            'path': task[4],
                            'blocks': res,
                        })
                else:
                    failed += 1
                    failed_list.append({'sid': sid, 'error': str(res)})
                    if failed <= 5:
                        print(f"Failed {sid}: {res}")

                if done % 10 == 0 or done == total:
                    elapsed = time.time() - t0
                    rate = done / elapsed if elapsed > 0 else 0
                    print(f"Progress: {done}/{total} ({done/total*100:.1f}%) | Success: {success}, Fail: {failed} | Rate: {rate:.1f} bundles/s")

        t1 = time.time()
        print(f"\nExtraction completed in {t1-t0:.1f}s!")
        print(f"Success: {success}, Failed: {failed}, Blocks: {total_blocks}")

        # Count choices per file
        for finfo in files:
            try:
                with open(finfo['path'], 'r', encoding='utf-8') as f:
                    fdata = json.load(f)
                choice_count = sum(len(b.get('choice_data_list', [])) for b in fdata.get('text_block_list', []))
                finfo['choices'] = choice_count
                total_choices += choice_count
            except Exception:
                finfo['choices'] = 0

        summary = {
            'attempted': len(tasks),
            'success': success,
            'failed': failed,
            'skipped_exists': 0,
            'no_dat': len(missing_no_dat),
            'total_blocks': total_blocks,
            'total_choices': total_choices,
            'files': files,
            'failed_list': failed_list,
        }

    # Save extraction summary
    with open(OUT_BASE / "extraction_summary_09.json", "w", encoding="utf-8") as f:
        json.dump(summary, f, indent=2, ensure_ascii=False)

    print(f"\nSummary saved to {OUT_BASE / 'extraction_summary_09.json'}")
    print(f"Extracted: {summary['success']} files, {summary['total_blocks']} blocks, {summary['total_choices']} choices")
    print(f"No dat (skipped): {summary['no_dat']}")

if __name__ == "__main__":
    multiprocessing.freeze_support()
    main()
