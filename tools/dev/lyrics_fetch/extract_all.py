#!/usr/bin/env python3
"""
FULL PIPELINE: Extract 26 gaps from encrypted bundles, translate, merge to both repos.
"""
import os, sys, struct, json, UnityPy, apsw, hashlib, time, traceback

sys.stdout.reconfigure(encoding='utf-8')

# === Config ===
META_DB = r"G:\Games\steamapps\common\UmamusumePrettyDerby_Jpn\UmamusumePrettyDerby_Jpn_Data\Persistent\meta"
DAT_DIR = r"G:\Games\steamapps\common\UmamusumePrettyDerby_Jpn\UmamusumePrettyDerby_Jpn_Data\Persistent\dat"
GEMINI_REPO = r"G:\Games\steamapps\common\UmamusumePrettyDerby_Jpn\gemini_horses\localized_data\assets"
HACHIMI_REPO = r"G:\Games\steamapps\common\UmamusumePrettyDerby_Jpn\hachimi\localized_data_1\assets"

LYRICS_OUT = r"C:\TMP\lyrics_fetch\story_json\lyrics"
STORYRACE_OUT = r"C:\TMP\lyrics_fetch\story_json\storyrace"
CHECKPOINT_PATH = r"C:\TMP\lyrics_fetch\lyrics_checkpoint.json"

AB_KEY = b'\x53\x2B\x46\x31\xE4\xA7\xB9\x47\x3E\x7C\xFB'
DB_BASE_KEY = b'\xF1\x70\xCE\xA4\xDF\xCE\xA3\xE1\xA5\xD8\xC7\x0B\xD1\x00\x00\x00'
DB_KEY = b'\x6D\x5B\x65\x33\x63\x36\x63\x25\x54\x71\x2D\x73\x50\x53\x63\x38\x6D\x34\x37\x7B\x35\x63\x70\x23\x37\x34\x53\x29\x73\x43\x36\x33'

# === Crypto ===
def _derive_decryption_key(key, base_key):
    key = bytearray(key)
    for i in range(len(key)):
        key[i] ^= base_key[i % 13]
    return bytes(key)

def _derive_asset_key(key_long):
    if key_long == 0:
        return None
    key_bytes = struct.pack('<q', key_long)
    base_len = len(AB_KEY)
    final_key = bytearray(base_len * 8)
    for i in range(base_len):
        b = AB_KEY[i]
        base_offset = i * 8
        for j in range(8):
            final_key[base_offset + j] = b ^ key_bytes[j]
    return bytes(final_key)

def decrypt_bundle(raw_data, asset_key_int):
    if asset_key_int == 0:
        return raw_data
    decryption_key = _derive_asset_key(asset_key_int)
    if decryption_key and len(raw_data) > 256:
        data = bytearray(raw_data)
        key_len = len(decryption_key)
        for j in range(256, len(data)):
            data[j] ^= decryption_key[j % key_len]
        return bytes(data)
    return raw_data

# === Extraction ===
def extract_lyrics_csv(decrypted_data):
    """Lyrics bundles are TextAsset with CSV: time,lyrics\\n..."""
    env = UnityPy.load(decrypted_data)
    for obj in env.objects:
        if obj.type.name == "TextAsset":
            data = obj.read()
            script_bytes = bytes(data.m_Script) if isinstance(data.m_Script, memoryview) else data.m_Script
            text = script_bytes.decode('utf-8-sig')
            lines = text.strip().split('\n')
            result = {}
            for line in lines[1:]:  # skip header "time,lyrics"
                line = line.strip()
                if not line:
                    continue
                parts = line.split(',', 1)
                if len(parts) == 2:
                    ts, lyric = parts[0].strip(), parts[1].strip()
                    if ts:
                        result[ts] = lyric
            return result
    return None

def extract_storyrace_typetree(decrypted_data):
    """Storyrace bundles are MonoBehaviour with textData[].text -> list of strings."""
    env = UnityPy.load(decrypted_data)
    for obj in env.objects:
        if obj.type.name == "MonoBehaviour":
            tree = obj.read_typetree()
            if tree and isinstance(tree, dict) and 'textData' in tree:
                texts = []
                for item in tree['textData']:
                    if isinstance(item, dict) and 'text' in item:
                        texts.append(item['text'])
                return texts
    return None

def main():
    os.makedirs(LYRICS_OUT, exist_ok=True)
    os.makedirs(STORYRACE_OUT, exist_ok=True)

    # Connect to meta
    conn = apsw.Connection(META_DB)
    final_key = _derive_decryption_key(DB_KEY, DB_BASE_KEY)
    conn.pragma("cipher", "chacha20")
    conn.pragma("hexkey", final_key.hex())
    next(conn.cursor().execute("PRAGMA quick_check"))

    # Get all lyrics + storyrace from meta
    lyrics_rows = list(conn.cursor().execute("SELECT n, h, e FROM a WHERE n LIKE 'live/musicscores/%_lyrics%'"))
    storyrace_rows = list(conn.cursor().execute("SELECT n, h, e FROM a WHERE n LIKE 'race/storyrace/text/storyrace_%' AND n NOT LIKE '%ast_ruby%'"))
    conn.close()

    # Get local files (gemini = truth)
    local_lyrics = set(f for f in os.listdir(os.path.join(GEMINI_REPO, 'lyrics')) if f.endswith('.json'))
    local_storyrace = set(f for f in os.listdir(os.path.join(GEMINI_REPO, 'race/storyrace/text')) if f.endswith('.json'))

    # Find gaps
    gaps_lyrics = [(n, h, e, os.path.basename(n) + '.json') for n, h, e in lyrics_rows if os.path.basename(n) + '.json' not in local_lyrics]
    gaps_storyrace = [(n, h, e, os.path.basename(n) + '.json') for n, h, e in storyrace_rows if os.path.basename(n) + '.json' not in local_storyrace]
    all_gaps = gaps_lyrics + gaps_storyrace

    print(f"=== GAPS: {len(gaps_lyrics)} lyrics + {len(gaps_storyrace)} storyrace = {len(all_gaps)} total ===")

    extraction_stats = []
    checkpoint = {"lyrics": {}, "storyrace": {}, "uniques": 0, "checkpoint_count": 0}

    for n, h, e, fname in all_gaps:
        is_lyrics = 'lyrics' in n
        bundle_path = os.path.join(DAT_DIR, h[:2].upper(), h)
        if not os.path.exists(bundle_path):
            print(f"  SKIP (no bundle): {fname}")
            continue

        print(f"  Extracting: {fname} (hash={h[:16]}...)")
        try:
            raw = open(bundle_path, 'rb').read()
            decrypted = decrypt_bundle(raw, e)

            if is_lyrics:
                result = extract_lyrics_csv(decrypted)
                if result:
                    out_path = os.path.join(LYRICS_OUT, fname)
                    with open(out_path, 'w', encoding='utf-8', newline='\n') as f:
                        json.dump(result, f, ensure_ascii=False, indent=4)
                    extraction_stats.append((fname, 'lyrics', len(result)))
                    checkpoint['lyrics'][fname] = result
                    print(f"    OK: {len(result)} lyric entries")
                else:
                    print(f"    FAIL: no lyrics data")
                    extraction_stats.append((fname, 'lyrics', 0))
            else:
                result = extract_storyrace_typetree(decrypted)
                if result:
                    out_path = os.path.join(STORYRACE_OUT, fname)
                    with open(out_path, 'w', encoding='utf-8', newline='\n') as f:
                        json.dump(result, f, ensure_ascii=False, indent=4)
                    extraction_stats.append((fname, 'storyrace', len(result)))
                    checkpoint['storyrace'][fname] = result
                    print(f"    OK: {len(result)} storyrace lines")
                else:
                    print(f"    FAIL: no storyrace data")
                    extraction_stats.append((fname, 'storyrace', 0))
        except Exception as ex:
            print(f"    ERROR: {ex}")
            traceback.print_exc()
            extraction_stats.append((fname, 'unknown', 0))

    # Summary
    total_blocks = sum(c for _, _, c in extraction_stats)
    successful = sum(1 for _, _, c in extraction_stats if c > 0)
    print(f"\n=== EXTRACTION SUMMARY ===")
    print(f"Total: {len(extraction_stats)} files, {total_blocks} blocks, {successful} successful")

    # Save checkpoint
    checkpoint['checkpoint_count'] = len(checkpoint['lyrics']) + len(checkpoint['storyrace'])
    checkpoint['extraction_stats'] = extraction_stats
    with open(CHECKPOINT_PATH, 'w', encoding='utf-8', newline='\n') as f:
        json.dump(checkpoint, f, ensure_ascii=False, indent=2)
    print(f"Checkpoint saved: {checkpoint['checkpoint_count']} items")

if __name__ == '__main__':
    main()
