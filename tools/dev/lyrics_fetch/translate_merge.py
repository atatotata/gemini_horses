#!/usr/bin/env python3
"""
Full translation + merge pipeline for 26 gap items.
v2: Fix - explicit lyrics translation tracking.
"""
import os, sys, json, time, urllib.request, urllib.error, re

sys.stdout.reconfigure(encoding='utf-8')

# === Config ===
ENV_PATH = r"C:\Users\Ota\.omniroute\.env"
API_URL = "http://127.0.0.1:20128/v1/chat/completions"
PRIMARY_MODEL = "antigravity/gemini-3.7-flash-low"
FALLBACK_MODELS = [
    "opencode-go/deepseek-v4-flash-low",
    "opencode-go/deepseek-v4-pro-low",
    "antigravity/gemini-3.1-pro-low",
]

LYRICS_SRC = r"C:\TMP\lyrics_fetch\story_json\lyrics"
STORYRACE_SRC = r"C:\TMP\lyrics_fetch\story_json\storyrace"

GEMINI_LYRICS = r"G:\Games\steamapps\common\UmamusumePrettyDerby_Jpn\gemini_horses\localized_data\assets\lyrics"
GEMINI_STORYRACE = r"G:\Games\steamapps\common\UmamusumePrettyDerby_Jpn\gemini_horses\localized_data\assets\race\storyrace\text"
HACHIMI_LYRICS = r"G:\Games\steamapps\common\UmamusumePrettyDerby_Jpn\hachimi\localized_data_1\assets\lyrics"
HACHIMI_STORYRACE = r"G:\Games\steamapps\common\UmamusumePrettyDerby_Jpn\hachimi\localized_data_1\assets\race\storyrace\text"

TRANSLATION_CHECKPOINT = r"C:\TMP\lyrics_fetch\lyrics_translation_checkpoint.json"
MERGE_CHECKPOINT = r"C:\TMP\lyrics_fetch\lyrics_merge_checkpoint.json"

BATCH_SIZE = 50


def get_api_key():
    env = {}
    for line in open(ENV_PATH, 'r'):
        line = line.strip()
        if line and not line.startswith('#') and '=' in line:
            k, v = line.split('=', 1)
            env[k.strip()] = v.strip()
    return env.get('VISION_BRIDGE_API_KEY', '')


def call_api_with_fallback(api_key, system_prompt, user_payload, timeout=180):
    models_to_try = [PRIMARY_MODEL] + FALLBACK_MODELS
    last_error = None
    for model in models_to_try:
        for attempt in range(3):
            try:
                messages = [
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": json.dumps(user_payload, ensure_ascii=False)}
                ]
                data = {
                    "model": model,
                    "messages": messages,
                    "temperature": 0.2,
                    "max_tokens": 16000
                }
                req = urllib.request.Request(
                    API_URL,
                    data=json.dumps(data).encode("utf-8"),
                    headers={
                        "Authorization": f"Bearer {api_key}",
                        "Content-Type": "application/json"
                    }
                )
                with urllib.request.urlopen(req, timeout=timeout) as resp:
                    body = json.loads(resp.read().decode("utf-8"))
                    return body["choices"][0]["message"]["content"], model
            except urllib.error.HTTPError as e:
                last_error = f"{model} HTTP {e.code}: {e.reason}"
                if e.code in (429, 503, 502):
                    time.sleep(3 * (attempt + 1))
                    continue
                break
            except Exception as e:
                last_error = f"{model} error: {e}"
                time.sleep(2)
                continue
        time.sleep(0.5)
    raise RuntimeError(f"All models failed. Last error: {last_error}")


def parse_json_response(raw_text):
    """Parse JSON from LLM response, handling markdown code blocks."""
    text = raw_text.strip()
    if text.startswith("```json"):
        text = text[7:]
    elif text.startswith("```"):
        text = text[3:]
    if text.endswith("```"):
        text = text[:-3]
    text = text.strip()
    return json.loads(text)


def translate_batch(api_key, system_prompt, items_dict, batch_label=""):
    """Generic batch translation. items_dict: {id: text}. Returns {id: translation}."""
    raw_response, model = call_api_with_fallback(api_key, system_prompt, items_dict)
    parsed = parse_json_response(raw_response)
    if isinstance(parsed, dict):
        return parsed, model
    return {}, model


def write_json_file(filepath, data):
    with open(filepath, 'w', encoding='utf-8', newline='\n') as f:
        json.dump(data, f, ensure_ascii=False, indent=4)


def main():
    api_key = get_api_key()
    print(f"API key: {api_key[:8]}...{api_key[-4:]}")

    # Load checkpoint
    checkpoint = {}
    if os.path.exists(TRANSLATION_CHECKPOINT):
        try:
            with open(TRANSLATION_CHECKPOINT, 'r', encoding='utf-8') as f:
                checkpoint = json.load(f)
            print(f"Loaded checkpoint: {len(checkpoint)} entries")
        except:
            pass

    # =========================================================
    # STEP 1: COLLECT ALL ITEMS TO TRANSLATE
    # =========================================================
    all_lyrics_by_file = {}  # fname -> [(entry_id, timestamp_key, jp_text)]
    all_storyrace_by_file = {}  # fname -> [(entry_id, index_str, jp_text)]

    for fname in sorted(os.listdir(LYRICS_SRC)):
        if not fname.endswith('.json'):
            continue
        with open(os.path.join(LYRICS_SRC, fname), 'r', encoding='utf-8') as f:
            data = json.load(f)
        items = []
        for k, v in data.items():
            entry_id = f"{fname}::{k}"
            if entry_id not in checkpoint and v.strip():
                items.append((entry_id, k, v))
        if items:
            all_lyrics_by_file[fname] = items

    for fname in sorted(os.listdir(STORYRACE_SRC)):
        if not fname.endswith('.json'):
            continue
        with open(os.path.join(STORYRACE_SRC, fname), 'r', encoding='utf-8') as f:
            data = json.load(f)
        items = []
        for i, v in enumerate(data):
            entry_id = f"{fname}::{i}"
            if entry_id not in checkpoint and v.strip():
                items.append((entry_id, str(i), v))
        if items:
            all_storyrace_by_file[fname] = items

    total_lyrics = sum(len(v) for v in all_lyrics_by_file.values())
    total_storyrace = sum(len(v) for v in all_storyrace_by_file.values())
    total_pending = total_lyrics + total_storyrace
    print(f"\nPending: {total_lyrics} lyrics + {total_storyrace} storyrace = {total_pending}")

    # =========================================================
    # STEP 2: TRANSLATE LYRICS
    # =========================================================
    if all_lyrics_by_file:
        print(f"\n=== TRANSLATING LYRICS ({len(all_lyrics_by_file)} files, {total_lyrics} entries) ===")
        LYRICS_SYSTEM = """You are a professional translator for Uma Musume Pretty Derby song lyrics.

TASK: Translate Japanese song lyrics to English.

RULES:
1. Translate poetically but preserve meaning and emotional tone.
2. Return a JSON object: {"timestamp_key": "translated_line"} — same keys as input.
3. Preserve formatting markers like [brackets]<angle brackets> exactly.
4. Empty values remain empty strings.
5. Only return the JSON object, no commentary.

OUTPUT: {"key": "translation", ...}"""

        for fname in sorted(all_lyrics_by_file.keys()):
            items = all_lyrics_by_file[fname]
            print(f"\n  {fname}: {len(items)} entries")
            for batch_start in range(0, len(items), BATCH_SIZE):
                batch = items[batch_start:batch_start + BATCH_SIZE]
                items_dict = {k: v for _, k, v in batch}
                batch_ids = [eid for eid, _, _ in batch]

                try:
                    result, model = translate_batch(api_key, LYRICS_SYSTEM, items_dict)
                    translated_count = 0
                    for eid, (orig_key, _) in zip(batch_ids, [(k, v) for _, k, v in batch]):
                        if orig_key in result:
                            checkpoint[eid] = result[orig_key]
                            translated_count += 1
                    print(f"    Batch {batch_start // BATCH_SIZE + 1}: {translated_count}/{len(batch)} via {model}")
                except Exception as e:
                    print(f"    Batch {batch_start // BATCH_SIZE + 1}: ERROR: {e}")
                time.sleep(0.3)

                # Atomic checkpoint save after each batch
                with open(TRANSLATION_CHECKPOINT, 'w', encoding='utf-8', newline='\n') as f:
                    json.dump(checkpoint, f, ensure_ascii=False)

        print(f"\n  Lyrics checkpoint: {sum(1 for k in checkpoint if '::' in k and not k.endswith('::storyrace'))} entries saved")

    # =========================================================
    # STEP 3: TRANSLATE STORYRACE
    # =========================================================
    if all_storyrace_by_file:
        print(f"\n=== TRANSLATING STORYRACE ({len(all_storyrace_by_file)} files, {total_storyrace} entries) ===")
        SR_SYSTEM = """You are a professional translator for Uma Musume Pretty Derby race commentary.

TASK: Translate Japanese storyrace commentary to English.

RULES:
1. Translate naturally as race commentary — keep excitement and drama.
2. Preserve \\n as literal \\n (line break marker).
3. Preserve \\u3000 as regular space.
4. Preserve [brackets]<angle brackets> as-is.
5. Standard romanization for horse names: Oguri Cap, Mejiro, etc.
6. Return ONLY a JSON array of translated strings in the same order.

OUTPUT: ["line 1", "line 2", ...]"""

        for fname in sorted(all_storyrace_by_file.keys()):
            items = all_storyrace_by_file[fname]
            print(f"\n  {fname}: {len(items)} entries")
            for batch_start in range(0, len(items), BATCH_SIZE):
                batch = items[batch_start:batch_start + BATCH_SIZE]
                batch_payload = [[int(k), v] for _, k, v in batch]
                batch_ids = [eid for eid, _, _ in batch]

                try:
                    raw_response, model = call_api_with_fallback(api_key, SR_SYSTEM, batch_payload)
                    parsed = parse_json_response(raw_response)
                    if isinstance(parsed, list):
                        for i, eid in enumerate(batch_ids):
                            if i < len(parsed):
                                checkpoint[eid] = parsed[i]
                        print(f"    Batch: {len(parsed)}/{len(batch)} via {model}")
                    else:
                        print(f"    Batch: parse FAILED (not list)")
                except Exception as e:
                    print(f"    Batch ERROR: {e}")
                time.sleep(0.3)

                with open(TRANSLATION_CHECKPOINT, 'w', encoding='utf-8', newline='\n') as f:
                    json.dump(checkpoint, f, ensure_ascii=False)

    # Save final checkpoint
    with open(TRANSLATION_CHECKPOINT, 'w', encoding='utf-8', newline='\n') as f:
        json.dump(checkpoint, f, ensure_ascii=False)
    print(f"\nTranslation checkpoint: {len(checkpoint)} total entries")

    # =========================================================
    # STEP 4: MERGE TO BOTH REPOS
    # =========================================================
    print(f"\n=== MERGING TO BOTH REPOS ===")
    merge_count = 0
    identical = True

    # Merge lyrics
    for fname in sorted(os.listdir(LYRICS_SRC)):
        if not fname.endswith('.json'):
            continue
        with open(os.path.join(LYRICS_SRC, fname), 'r', encoding='utf-8') as f:
            raw_data = json.load(f)

        translated = {}
        found = 0
        for k, v in raw_data.items():
            entry_id = f"{fname}::{k}"
            if entry_id in checkpoint:
                translated[k] = checkpoint[entry_id]
                found += 1
            else:
                translated[k] = v

        write_json_file(os.path.join(GEMINI_LYRICS, fname), translated)
        write_json_file(os.path.join(HACHIMI_LYRICS, fname), translated)
        merge_count += 1
        if found > 0:
            print(f"  Lyrics {fname}: {found}/{len(raw_data)} translated")

    # Merge storyrace
    for fname in sorted(os.listdir(STORYRACE_SRC)):
        if not fname.endswith('.json'):
            continue
        with open(os.path.join(STORYRACE_SRC, fname), 'r', encoding='utf-8') as f:
            raw_data = json.load(f)

        translated = []
        found = 0
        for i, v in enumerate(raw_data):
            entry_id = f"{fname}::{i}"
            if entry_id in checkpoint:
                translated.append(checkpoint[entry_id])
                found += 1
            else:
                translated.append(v)

        write_json_file(os.path.join(GEMINI_STORYRACE, fname), translated)
        write_json_file(os.path.join(HACHIMI_STORYRACE, fname), translated)
        merge_count += 1
        if found > 0:
            print(f"  Storyrace {fname}: {found}/{len(raw_data)} translated")

    # Verify identical
    for fname in sorted(os.listdir(GEMINI_LYRICS)):
        if not fname.endswith('.json'):
            continue
        g_path = os.path.join(GEMINI_LYRICS, fname)
        h_path = os.path.join(HACHIMI_LYRICS, fname)
        if os.path.exists(h_path):
            with open(g_path, 'rb') as gf, open(h_path, 'rb') as hf:
                if gf.read() != hf.read():
                    identical = False
                    print(f"  MISMATCH lyrics: {fname}")

    for fname in sorted(os.listdir(GEMINI_STORYRACE)):
        if not fname.endswith('.json'):
            continue
        g_path = os.path.join(GEMINI_STORYRACE, fname)
        h_path = os.path.join(HACHIMI_STORYRACE, fname)
        if os.path.exists(h_path):
            with open(g_path, 'rb') as gf, open(h_path, 'rb') as hf:
                if gf.read() != hf.read():
                    identical = False
                    print(f"  MISMATCH storyrace: {fname}")

    # Save merge checkpoint
    merge_data = {
        "merge_count": merge_count,
        "identical_repos": identical,
        "translated_entries": len(checkpoint),
    }
    with open(MERGE_CHECKPOINT, 'w', encoding='utf-8', newline='\n') as f:
        json.dump(merge_data, f, ensure_ascii=False, indent=2)

    print(f"\n=== FINAL SUMMARY ===")
    print(f"Translated: {len(checkpoint)} entries")
    print(f"Merged: {merge_count} files")
    print(f"Repos identical: {identical}")


if __name__ == '__main__':
    main()
