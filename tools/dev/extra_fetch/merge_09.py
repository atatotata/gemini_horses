"""
Merge 198 translated 09 files to BOTH repos lockstep.
For each SID: load JP source, map via checkpoint, wrap 42 cols, write to both repos.
"""
import os
import json
import re
import hashlib
from pathlib import Path

ROOT_DIR = Path(r"C:/TMP/extra_fetch")
STORY_DIR = ROOT_DIR / "story_json" / "09"
CHECKPOINT_PATH = ROOT_DIR / "extra_checkpoint.json"

GH_BASE = Path(r"G:/Games/steamapps/common/UmamusumePrettyDerby_Jpn/gemini_horses/localized_data/assets/story/data/09")
HA_BASE = Path(r"G:/Games/steamapps/common/UmamusumePrettyDerby_Jpn/hachimi/localized_data_1/assets/story/data/09")

EXCLUDE_SIDS = {"90016001", "90021001", "90032001", "90054007"}

# Tag-aware wrapping
TAG_RE = re.compile(r'<[^>]+>')

def strip_tags(text):
    return TAG_RE.sub('', text)

def display_width(text):
    """Calculate display width: CJK=2, others=1."""
    w = 0
    for ch in strip_tags(text):
        cp = ord(ch)
        if (cp > 0x2E7F or (0x4E00 <= cp <= 0x9FFF) or
            (0x3040 <= cp <= 0x309F) or (0x30A0 <= cp <= 0x30FF) or
            (0xFF00 <= cp <= 0xFFEF)):
            w += 2
        else:
            w += 1
    return w

def wrap_paragraph(text, max_cols=42):
    """Wrap text to max_cols display width, space-break, tag-aware.
    Preserve \\n paragraph breaks. Use ' \\n' for soft breaks."""
    paras = text.split('\n')
    result = []
    for para in paras:
        if not para:
            result.append('')
            continue
        if display_width(para) <= max_cols:
            result.append(para)
            continue
        # Word wrap within paragraph
        parts = re.split(r'(<[^>]+>|\s+)', para)
        lines = []
        current = ''
        current_w = 0
        for part in parts:
            if not part:
                continue
            if TAG_RE.match(part):
                current += part
                continue
            pw = display_width(part)
            if current_w + pw <= max_cols:
                current += part
                current_w += pw
            else:
                if current.rstrip():
                    lines.append(current.rstrip())
                current = part.lstrip()
                current_w = display_width(current)
        if current.rstrip():
            lines.append(current.rstrip())
        result.extend(lines)
    return ' \n'.join(result)

def normalize_key(text):
    """Normalize text for key lookup: \\r\\n -> \\n, strip trailing spaces."""
    text = text.replace("\r\n", "\n").replace("\r", "\n")
    lines = [line.rstrip() for line in text.split("\n")]
    return "\n".join(lines)

def translate_choice_data(choice_data_list, checkpoint):
    """Translate choice_data_list items (can be strings or dicts)."""
    result = []
    for ch in choice_data_list:
        if isinstance(ch, str):
            key = normalize_key(ch)
            en = checkpoint.get(key, ch)
            # Wrap the choice text
            wrapped = wrap_paragraph(en, 42)
            result.append(wrapped)
        elif isinstance(ch, dict):
            new_ch = dict(ch)
            if "text" in new_ch:
                key = normalize_key(new_ch["text"])
                en = checkpoint.get(key, new_ch["text"])
                new_ch["text"] = wrap_paragraph(en, 42)
            result.append(new_ch)
        else:
            result.append(ch)
    return result

def merge_file(sid, sub, checkpoint):
    """Merge a single file: load JP, translate, wrap, write to both repos."""
    jp_path = STORY_DIR / sub / f"storytimeline_{sid}.json"
    if not jp_path.exists():
        print(f"  ERROR: JP source not found: {jp_path}")
        return False
    
    with open(jp_path, encoding="utf-8") as f:
        jp_data = json.load(f)
    
    # Build EN block list
    en_blocks = []
    for block in jp_data.get("text_block_list", []):
        en_block = {}
        
        # Translate name
        name = block.get("name", "")
        if name:
            key = normalize_key(name)
            en_block["name"] = checkpoint.get(key, name)
        else:
            en_block["name"] = ""
        
        # Translate and wrap text
        text = block.get("text", "")
        if text:
            key = normalize_key(text)
            en_text = checkpoint.get(key, text)
            en_block["text"] = wrap_paragraph(en_text, 42)
        else:
            en_block["text"] = ""
        
        # Translate choices
        choices = block.get("choice_data_list", [])
        if choices:
            en_block["choice_data_list"] = translate_choice_data(choices, checkpoint)
        else:
            en_block["choice_data_list"] = []
        
        en_blocks.append(en_block)
    
    # Build output JSON
    en_data = {
        "no_wrap": True,
        "text_block_list": en_blocks
    }
    
    # Serialize with LF line endings, no trailing newline beyond JSON
    json_str = json.dumps(en_data, ensure_ascii=False, indent=2)
    # Ensure LF endings (no CRLF)
    json_str = json_str.replace("\r\n", "\n")
    # Ensure file ends with single newline
    if not json_str.endswith("\n"):
        json_str += "\n"
    file_bytes = json_str.encode("utf-8")
    
    # Write to gemini_horses
    gh_path = GH_BASE / sub / f"storytimeline_{sid}.json"
    gh_path.parent.mkdir(parents=True, exist_ok=True)
    with open(gh_path, "wb") as f:
        f.write(file_bytes)
    
    # Byte-copy identical to hachimi
    ha_path = HA_BASE / sub / f"storytimeline_{sid}.json"
    ha_path.parent.mkdir(parents=True, exist_ok=True)
    with open(ha_path, "wb") as f:
        f.write(file_bytes)
    
    # Verify identical
    with open(gh_path, "rb") as f:
        gh_bytes = f.read()
    with open(ha_path, "rb") as f:
        ha_bytes = f.read()
    
    return gh_bytes == ha_bytes

def check_max_cols(data, checkpoint):
    """Scan all wrapped text blocks for max display columns."""
    max_w = 0
    max_text = ""
    for block in data.get("text_block_list", []):
        text = block.get("text", "")
        # Already wrapped, check display width of each line
        for line in text.split("\n"):
            line = line.rstrip()  # strip trailing soft break marker
            w = display_width(line)
            if w > max_w:
                max_w = w
                max_text = text[:60]
        
        choices = block.get("choice_data_list", [])
        for ch in choices:
            if isinstance(ch, str):
                for line in ch.split("\n"):
                    w = display_width(line.rstrip())
                    if w > max_w:
                        max_w = w
                        max_text = ch[:60]
            elif isinstance(ch, dict):
                ct = ch.get("text", "")
                for line in ct.split("\n"):
                    w = display_width(line.rstrip())
                    if w > max_w:
                        max_w = w
                        max_text = ct[:60]
    return max_w, max_text

def main():
    # Load checkpoint
    with open(CHECKPOINT_PATH, encoding="utf-8") as f:
        checkpoint = json.load(f)
    print(f"Loaded checkpoint: {len(checkpoint)} entries")
    
    # Collect 198 files
    all_files = []
    for subdir in sorted(os.listdir(STORY_DIR)):
        sub_path = STORY_DIR / subdir
        if not sub_path.is_dir():
            continue
        for fname in sorted(os.listdir(sub_path)):
            if not fname.startswith("storytimeline_") or not fname.endswith(".json"):
                continue
            sid = fname.replace("storytimeline_", "").replace(".json", "")
            if sid in EXCLUDE_SIDS:
                continue
            all_files.append({"sid": sid, "sub": subdir})
    
    print(f"Merging {len(all_files)} files to both repos...")
    
    success = 0
    failed = 0
    hash_mismatches = 0
    global_max_w = 0
    global_max_text = ""
    crlf_issues = 0
    
    for i, finfo in enumerate(all_files):
        sid = finfo["sid"]
        sub = finfo["sub"]
        
        identical = merge_file(sid, sub, checkpoint)
        if identical:
            success += 1
        else:
            hash_mismatches += 1
            print(f"  HASH MISMATCH: {sid}")
        
        # Verify no_wrap, CRLF on written file
        gh_path = GH_BASE / sub / f"storytimeline_{sid}.json"
        with open(gh_path, encoding="utf-8") as f:
            written_data = json.load(f)
        
        if not written_data.get("no_wrap", False):
            print(f"  WARNING: no_wrap missing in {sid}")
        
        # Check for CRLF in raw bytes
        with open(gh_path, "rb") as f:
            raw = f.read()
        if b"\r\n" in raw:
            crlf_issues += 1
            print(f"  CRLF found in {sid}")
        
        # Check max columns
        mw, mt = check_max_cols(written_data, checkpoint)
        if mw > global_max_w:
            global_max_w = mw
            global_max_text = mt
        
        if (i + 1) % 50 == 0:
            print(f"  Progress: {i+1}/{len(all_files)}")
    
    print(f"\n=== Merge Complete ===")
    print(f"Files merged: {success}/{len(all_files)}")
    print(f"Hash mismatches: {hash_mismatches}")
    print(f"CRLF issues: {crlf_issues}")
    print(f"Max display columns: {global_max_w}")
    if global_max_text:
        print(f"Max width sample: {repr(global_max_text[:80])}")
    
    # Verify final counts
    gh_count = sum(1 for _ in GH_BASE.rglob("*.json"))
    ha_count = sum(1 for _ in HA_BASE.rglob("*.json"))
    print(f"\ngemini_horses 09 total: {gh_count}")
    print(f"hachimi 09 total: {ha_count}")
    
    # Sample hash check
    sample_sid = all_files[0]["sid"]
    sample_sub = all_files[0]["sub"]
    gh_sample = GH_BASE / sample_sub / f"storytimeline_{sample_sid}.json"
    ha_sample = HA_BASE / sample_sub / f"storytimeline_{sample_sid}.json"
    gh_hash = hashlib.blake2b(open(gh_sample, "rb").read()).hexdigest()
    ha_hash = hashlib.blake2b(open(ha_sample, "rb").read()).hexdigest()
    print(f"\nSample hash {sample_sid}:")
    print(f"  GH: {gh_hash}")
    print(f"  HA: {ha_hash}")
    print(f"  Match: {gh_hash == ha_hash}")
    
    # Show block 0 EN for 090009001
    sample_path = GH_BASE / "0009" / "storytimeline_090009001.json"
    with open(sample_path, encoding="utf-8") as f:
        d = json.load(f)
    b0 = d["text_block_list"][0]
    print(f"\nWrap excerpt (090009001 block 0 EN):")
    print(f"  name: {b0['name']}")
    print(f"  text: {repr(b0['text'])}")
    
    # Show display width of each line in block 0
    for j, line in enumerate(b0["text"].split("\n")):
        w = display_width(line.rstrip())
        print(f"    line {j}: {w}w {repr(line.rstrip())}")

if __name__ == "__main__":
    main()
