#!/usr/bin/env python3
"""
Proven extraction: use read_typetree() for structure, then extract strings
from raw bytes using the typetree string layout.
"""
import io, os, json, struct, tempfile, UnityPy

DAT_BASE = r"G:\Games\steamapps\common\UmamusumePrettyDerby_Jpn\UmamusumePrettyDerby_Jpn_Data\Persistent"
BUNDLE_BASE_KEY = "532b4631e4a7b9473e7cfb"

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

def extract_utf8_strings(raw_data):
    """Extract length-prefixed UTF-8 strings from raw bytes.
    Returns list of (offset, length, string) tuples, ordered by offset.
    """
    results = []
    i = 0
    while i < len(raw_data) - 4:
        slen = struct.unpack_from('<I', raw_data, i)[0]
        if 0 < slen < 5000 and i + 4 + slen <= len(raw_data):
            candidate = bytes(raw_data[i+4:i+4+slen])
            try:
                s = candidate.decode('utf-8')
                # Verify: all chars should be printable or CR/LF
                # And must contain at least one Japanese or ASCII letter
                has_text = any(c.isalpha() for c in s)
                is_clean = all(c.isprintable() or c in '\r\n\t' for c in s)
                if has_text and is_clean:
                    results.append((i, slen, s))
                    i += 4 + slen  # Skip past this string
                    continue
            except (UnicodeDecodeError, ValueError):
                pass
        i += 1
    return results

def extract_story_from_dat(n, h, e):
    """Extract story JSON from local dat file."""
    dat_path = os.path.join(DAT_BASE, "dat", h[:2].lower(), h)
    raw = open(dat_path, "rb").read()
    
    key_int = int(e)
    if key_int == 0:
        decrypted = raw
    else:
        final_key = _create_final_key(key_int)
        decrypted = bytearray(raw)
        for i in range(256, len(decrypted)):
            decrypted[i] ^= final_key[i % len(final_key)]
        decrypted = bytes(decrypted)
    
    with tempfile.NamedTemporaryFile(delete=False, suffix=".assets") as tmp:
        tmp.write(decrypted)
        tmp_path = tmp.name
    
    try:
        env = UnityPy.load(tmp_path)
        
        path_map = {}
        timeline_tree = None
        clip_objects = {}
        
        for obj in env.objects:
            if obj.type.name == "MonoBehaviour":
                tree = obj.read_typetree()
                if tree and "BlockList" in tree:
                    timeline_tree = tree
                elif tree:
                    clip_objects[obj.path_id] = (obj, tree)
        
        if not timeline_tree:
            return None, "no_timeline"
        
        title = timeline_tree.get("Title", "")
        story_id = timeline_tree.get("StoryId", "")
        block_list = timeline_tree["BlockList"]
        
        text_block_list = []
        total_choices = 0
        
        # Skip Block[0] (dummy), process blocks 1+
        for block in block_list[1:]:
            text_track = block.get("TextTrack", {})
            clips = text_track.get("ClipList", [])
            
            for clip in clips:
                pid = clip.get("m_PathID")
                if not pid or pid not in clip_objects:
                    continue
                
                clip_obj, clip_tree = clip_objects[pid]
                raw_data = bytes(clip_obj.get_raw_data()) if clip_obj.get_raw_data() else None
                
                # Extract strings from raw bytes
                strings = extract_utf8_strings(raw_data) if raw_data else []
                
                # The typetree gives us structure, raw strings give us text
                # Name is typically the shorter first non-empty string
                # Text is the longer one with newlines
                name_val = clip_tree.get("Name", "")
                text_val = clip_tree.get("Text", "")
                
                # Fix garbled strings using raw bytes
                if strings:
                    # Find Name (short string, typically character name)
                    # Find Text (longer string with dialogue)
                    raw_texts = [s for _, _, s in strings if len(s) > 1]
                    
                    # Heuristic: Name is short (<50 chars), Text is long
                    for s in raw_texts:
                        if len(s) < 50 and not name_val:
                            name_val = s
                        elif len(s) > 10:
                            text_val = s
                
                # ChoiceDataList from typetree (list, not strings)
                choice_data_list = clip_tree.get("ChoiceDataList", [])
                # Fix garbled choice texts too
                if choice_data_list and strings:
                    # Choices are the remaining strings after Name and Text
                    used = {name_val, text_val}
                    choice_texts = [s for _, _, s in strings if s not in used and len(s) > 0]
                    if len(choice_texts) == len(choice_data_list):
                        choice_data_list = choice_texts
                    total_choices += len(choice_data_list)
                
                block_entry = {}
                if name_val:
                    block_entry["name"] = name_val
                if text_val:
                    block_entry["text"] = text_val
                if choice_data_list:
                    block_entry["choice_data_list"] = choice_data_list
                
                text_block_list.append(block_entry)
        
        result = {"no_wrap": True}
        if title and title != "0":
            result["title"] = title
        result["text_block_list"] = text_block_list
        
        return result, None
    
    finally:
        os.unlink(tmp_path)


# Test with first gap entry
gap_list = json.load(open(r"C:\TMP\remaining_fetch\gap_list.json"))
n, h, e = gap_list[0]
print(f"Testing: {n}")
result, err = extract_story_from_dat(n, h, e)
if result:
    print(json.dumps(result, ensure_ascii=False, indent=2)[:2000])
    print(f"\nText blocks: {len(result['text_block_list'])}")
else:
    print(f"Error: {err}")
