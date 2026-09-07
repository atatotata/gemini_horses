#!/usr/bin/env python3
"""
Step 3: Extract 22 extra story bundles
Uses exact same pattern as proven career_fetch/extract_all_career.py
"""
import os
import sys
import json
from pathlib import Path

import UnityPy

# Import hachimi-tools decrypt
HACHIMI_TOOLS = r'G:\Games\steamapps\common\UmamusumePrettyDerby_Jpn\gemini_horses\tools\hachimi-tools'
sys.path.insert(0, HACHIMI_TOOLS)
from decrypt import decrypt_asset_bundle

DAT_DIR = Path(r'G:\Games\steamapps\common\UmamusumePrettyDerby_Jpn\UmamusumePrettyDerby_Jpn_Data\Persistent\dat')
OUT_DIR = Path(r'C:\TMP\extra_fetch\story_json')

def extract_one(sid, h, e, out_path):
    """Extract a single bundle. Returns (sid, success, info)."""
    if os.path.exists(out_path):
        return sid, True, "exists"
    
    dat_path = DAT_DIR / h[:2] / h
    if not dat_path.exists():
        return sid, False, "missing_dat"
    
    try:
        raw_data = dat_path.read_bytes()
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
        
        # Skip dummy block 0 (same as career)
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
        
        os.makedirs(os.path.dirname(out_path), exist_ok=True)
        with open(out_path, "w", encoding="utf-8", newline="\n") as f:
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
    
    # Load extraction plan
    with open(r'C:\TMP\extraction_plan.json') as f:
        plan = json.load(f)
    
    # Filter: only bundles that exist and are in meta
    plan = [p for p in plan if p['bundle_exists']]
    print(f"Extracting {len(plan)} bundles...")
    
    results = []
    total_blocks = 0
    success_count = 0
    fail_count = 0
    
    for i, item in enumerate(plan):
        sid = item['sid']
        h = item['h']
        e = item['e']
        prefix = item['prefix']
        sub = item['sub']
        out_path = str(OUT_DIR / prefix / sub / f'storytimeline_{sid}.json')
        
        sid_r, ok, info = extract_one(sid, h, e, out_path)
        
        if ok:
            success_count += 1
            if isinstance(info, int):
                total_blocks += info
            print(f"  [{i+1}/{len(plan)}] {sid}: OK ({info} blocks)")
        else:
            fail_count += 1
            print(f"  [{i+1}/{len(plan)}] {sid}: FAIL ({info})")
        
        results.append({
            'sid': sid,
            'prefix': prefix,
            'success': ok,
            'info': info,
            'out_path': out_path,
        })
    
    print(f"\n{'='*60}")
    print(f"EXTRACTION COMPLETE")
    print(f"{'='*60}")
    print(f"Total: {len(plan)}")
    print(f"Success: {success_count}")
    print(f"Failed: {fail_count}")
    print(f"Total blocks: {total_blocks}")
    print(f"\nFiles written:")
    for r in results:
        if r['success']:
            print(f"  {r['out_path']}")
    
    # Save summary
    with open(r'C:\TMP\extraction_summary.json', 'w') as f:
        json.dump(results, f, indent=2)
    print(f"\nSummary: C:\\TMP\\extraction_summary.json")


if __name__ == "__main__":
    main()
