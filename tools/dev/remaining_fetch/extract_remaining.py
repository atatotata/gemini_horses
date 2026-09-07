#!/usr/bin/env python3
"""
Extract remaining story gaps (50/40/11/80/83) from local Persistent/dat.
- Read meta DB for gap list
- Decrypt dat bundles
- Extract story JSON via UnityPy read_typetree()
- Save to C:\TMP\remaining_fetch\story_json/
Uses ProcessPool for parallelism.
"""
import io, os, json, struct, tempfile, sys, time
import multiprocessing as mp
from pathlib import Path

DAT_BASE = r"G:\Games\steamapps\common\UmamusumePrettyDerby_Jpn\UmamusumePrettyDerby_Jpn_Data\Persistent"
BUNDLE_BASE_KEY = "532b4631e4a7b9473e7cfb"
DB_URI = r"file:C:\TMP\meta_fresh.bin?hexkey=9c2bab97bcf8c0c4f1a9ea7881a213f6c9ebf9d8d4c6a8e43ce5a259bde7e9fd"
LOCALIZED_BASE = r"G:\Games\steamapps\common\UmamusumePrettyDerby_Jpn\gemini_horses\localized_data\assets\story\data"
OUTPUT_BASE = r"C:\TMP\remaining_fetch\story_json"
PREFIXES = ["50", "40", "11", "80", "83"]
NUM_WORKERS = 8


def _create_final_key(key):
    base_key = bytes.fromhex(BUNDLE_BASE_KEY)
    bundle_key = key.to_bytes(8, byteorder="little", signed=True)
    base_len = len(base_key)
    final_key = bytearray(base_len * 8)
    for i, b in enumerate(base_key):
        baseOffset = i << 3
        for j, k in enumerate(bundle_key):
            final_key[baseOffset + j] = b ^ k
    return final_key


def decrypt_and_load(raw, key_int):
    """Decrypt bundle data and load via UnityPy."""
    import UnityPy
    if key_int != 0:
        final_key = _create_final_key(key_int)
        decrypted = bytearray(raw)
        for i in range(256, len(decrypted)):
            decrypted[i] ^= final_key[i % len(final_key)]
        decrypted = bytes(decrypted)
    else:
        decrypted = raw
    
    with tempfile.NamedTemporaryFile(delete=False, suffix=".assets") as tmp:
        tmp.write(decrypted)
        tmp_path = tmp.name
    try:
        env = UnityPy.load(tmp_path)
    finally:
        os.unlink(tmp_path)
    return env


def extract_single(entry):
    """Extract a single story file from dat. Returns (n, success, error_msg)."""
    import UnityPy
    
    n, h, e = entry
    
    # Parse meta name to get output path components
    # n = "story/data/50/1001/storytimeline_501001400"
    parts = n.split("/")
    prefix = parts[2]    # "50"
    sub = parts[3]       # "1001"
    filename = parts[4]  # "storytimeline_501001400.json"
    
    out_dir = os.path.join(OUTPUT_BASE, prefix, sub)
    out_path = os.path.join(out_dir, filename + ".json")
    
    # Skip if already exists
    if os.path.exists(out_path) and os.path.getsize(out_path) > 100:
        return (n, True, "exists")
    
    # Read from dat
    dat_path = os.path.join(DAT_BASE, "dat", h[:2].lower(), h)
    try:
        raw = open(dat_path, "rb").read()
    except FileNotFoundError:
        return (n, False, f"dat_not_found: {dat_path}")
    
    # Decrypt and load
    key_int = int(e) if isinstance(e, (int, str)) else 0
    if isinstance(e, str):
        key_int = int(e)
    else:
        key_int = e
    
    try:
        env = decrypt_and_load(raw, key_int)
    except Exception as ex:
        return (n, False, f"decrypt_load_failed: {ex}")
    
    # Find timeline and clips
    path_map = {}
    timeline_tree = None
    
    for obj in env.objects:
        if obj.type.name == "MonoBehaviour":
            try:
                tree = obj.read_typetree()
            except:
                continue
            if tree is None:
                continue
            if "BlockList" in tree:
                timeline_tree = tree
            else:
                path_map[obj.path_id] = tree
    
    if not timeline_tree:
        return (n, False, "no_timeline")
    
    title = timeline_tree.get("Title", "")
    block_list = timeline_tree.get("BlockList", [])
    
    text_block_list = []
    total_blocks = 0
    total_choices = 0
    
    # Skip Block[0] (dummy), process blocks 1+
    for block in block_list[1:]:
        text_track = block.get("TextTrack", {})
        clips = text_track.get("ClipList", [])
        
        for clip in clips:
            pid = clip.get("m_PathID")
            if not pid or pid not in path_map:
                continue
            
            clip_tree = path_map[pid]
            name_val = clip_tree.get("Name", "")
            text_val = clip_tree.get("Text", "")
            choice_data_list = clip_tree.get("ChoiceDataList", [])
            
            # Clean up: filter out dummy 0 choices
            clean_choices = []
            for cd in choice_data_list:
                if isinstance(cd, dict):
                    ct = cd.get("Text", "")
                    if ct:
                        clean_choices.append(ct)
                elif isinstance(cd, str) and cd:
                    clean_choices.append(cd)
                elif isinstance(cd, (int, float)) and cd != 0:
                    clean_choices.append(str(cd))
            
            block_entry = {}
            if name_val:
                block_entry["name"] = name_val
            if text_val:
                block_entry["text"] = text_val
            if clean_choices:
                block_entry["choice_data_list"] = clean_choices
                total_choices += len(clean_choices)
            
            text_block_list.append(block_entry)
            total_blocks += 1
    
    # Build result JSON
    result = {"no_wrap": True}
    if title and title != "0":
        result["title"] = title
    result["text_block_list"] = text_block_list
    
    # Write output
    os.makedirs(out_dir, exist_ok=True)
    json_str = json.dumps(result, ensure_ascii=False, indent=2)
    # Ensure LF line endings (no CRLF)
    json_str = json_str.replace("\r\n", "\n")
    with open(out_path, "w", encoding="utf-8", newline="\n") as f:
        f.write(json_str)
    
    return (n, True, f"blocks={total_blocks},choices={total_choices}")


def main():
    t0 = time.time()
    
    # Load gap list
    gap_list = json.load(open(r"C:\TMP\remaining_fetch\gap_list.json"))
    print(f"Loaded {len(gap_list)} gap entries")
    
    # Verify all entries have valid dat paths
    valid = 0
    invalid = 0
    for n, h, e in gap_list:
        dat_path = os.path.join(DAT_BASE, "dat", h[:2].lower(), h)
        if os.path.exists(dat_path):
            valid += 1
        else:
            invalid += 1
            if invalid <= 3:
                print(f"  MISSING DAT: {h[:2].lower()}/{h} for {n}")
    print(f"DAT availability: {valid} found, {invalid} missing")
    
    if invalid > 0:
        print("WARNING: Some dat files are missing!")
    
    # Create output dirs
    for pfx in PREFIXES:
        os.makedirs(os.path.join(OUTPUT_BASE, pfx), exist_ok=True)
    
    # Process with pool
    print(f"\nExtracting with {NUM_WORKERS} workers...")
    results = []
    with mp.Pool(NUM_WORKERS) as pool:
        for i, result in enumerate(pool.imap_unordered(extract_single, gap_list, chunksize=64)):
            results.append(result)
            if (i + 1) % 500 == 0:
                elapsed = time.time() - t0
                print(f"  Progress: {i+1}/{len(gap_list)} ({elapsed:.1f}s)")
    
    t1 = time.time()
    
    # Analyze results
    success = [r for r in results if r[1]]
    failed = [r for r in results if not r[1]]
    
    # Check for "exists" (already extracted)
    already = [r for r in success if r[2] == "exists"]
    fresh = [r for r in success if r[2] != "exists"]
    
    # Per-prefix counts
    prefix_counts = {}
    for r in success:
        pfx = r[0].split("/")[2]
        prefix_counts[pfx] = prefix_counts.get(pfx, 0) + 1
    
    # Count totals
    total_blocks = 0
    total_choices = 0
    for r in fresh:
        msg = r[2]
        if msg.startswith("blocks="):
            parts = msg.split(",")
            total_blocks += int(parts[0].split("=")[1])
            total_choices += int(parts[1].split("=")[1])
    
    print(f"\n{'='*60}")
    print(f"EXTRACTION COMPLETE ({t1-t0:.1f}s)")
    print(f"{'='*60}")
    print(f"Total entries: {len(gap_list)}")
    print(f"Success: {len(success)} (fresh={len(fresh)}, already_exist={len(already)})")
    print(f"Failed: {len(failed)}")
    print(f"\nPer-prefix extracted:")
    for pfx in PREFIXES:
        cnt = prefix_counts.get(pfx, 0)
        print(f"  {pfx}: {cnt}")
    print(f"\nTotal blocks: {total_blocks}")
    print(f"Total choices: {total_choices}")
    
    if failed:
        print(f"\nFailed entries ({len(failed)}):")
        for r in failed[:20]:
            print(f"  {r[0]}: {r[2]}")
    
    # Save summary
    summary = {
        "total": len(gap_list),
        "success": len(success),
        "fresh": len(fresh),
        "already_exists": len(already),
        "failed": len(failed),
        "per_prefix": prefix_counts,
        "total_blocks": total_blocks,
        "total_choices": total_choices,
        "elapsed_seconds": round(t1 - t0, 1),
        "failures": [{"name": r[0], "error": r[2]} for r in failed[:50]]
    }
    summary_path = r"C:\TMP\remaining_fetch\extract_summary.json"
    with open(summary_path, "w", encoding="utf-8") as f:
        json.dump(summary, f, ensure_ascii=False, indent=2)
    print(f"\nSummary saved to: {summary_path}")


if __name__ == "__main__":
    main()
