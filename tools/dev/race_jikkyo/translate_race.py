import os
import sys
import json
import time
import re
import queue
import random
import threading
import urllib.request
from pathlib import Path

# Paths
ROOT_DIR = Path(r"C:/TMP/race_jikkyo")
CHECKPOINT_PATH = ROOT_DIR / "race_checkpoint.json"
MDB_PATH = Path(r"G:/Games/steamapps/common/UmamusumePrettyDerby_Jpn/UmamusumePrettyDerby_Jpn_Data/Persistent/master/master.mdb")
MSG_DICT_GEMINI = Path(r"G:/Games/steamapps/common/UmamusumePrettyDerby_Jpn/gemini_horses/localized_data/race_jikkyo_message_dict.json")
CMT_DICT_GEMINI = Path(r"G:/Games/steamapps/common/UmamusumePrettyDerby_Jpn/gemini_horses/localized_data/race_jikkyo_comment_dict.json")
MSG_DICT_HACHIMI = Path(r"G:/Games/steamapps/common/UmamusumePrettyDerby_Jpn/hachimi/localized_data_1/race_jikkyo_message_dict.json")
CMT_DICT_HACHIMI = Path(r"G:/Games/steamapps/common/UmamusumePrettyDerby_Jpn/hachimi/localized_data_1/race_jikkyo_comment_dict.json")
ENV_PATH = r"C:\Users\Ota\.omniroute\.env"

# API Configuration
OMNI_URL = "http://localhost:20128/v1/chat/completions"
PRIMARY_MODEL = "antigravity/gemini-3.7-flash-low"
FALLBACK_MODELS = [
    "opencode-go/deepseek-v4-flash",
    "opencode-go/qwen3.8-flash",
    "opencode-go/deepseek-v4-pro",
    "antigravity/gemini-3.1-pro-low",
]

BATCH_SIZE = 50
NUM_WORKERS = 5
FLUSH_INTERVAL = 5

SYSTEM_PROMPT = """You are an expert Japanese-to-English translator for Umamusume: Pretty Derby race commentary.

Translate the provided JSON array of Japanese race commentary texts into natural, energetic English.

Rules:
1. Race announcer style: terse, energetic, exciting.
2. Preserve proper nouns exactly: G1 race names (Feb Stakes, Victoria Mile, etc.), horse girl names (Special Week, Silence Suzuka, etc.).
3. Preserve formatting tokens EXACTLY: %course, %ground, %distance, %race, %h_num_no, %a_h_pop1, %a_h_pop2, %a_h_pop3, %h_player, %h_rank1, etc.
4. Preserve \\n line breaks (do NOT strip or double-escape).
5. No wrapping needed - dict values are single logical lines.
6. Output strictly a JSON array of objects with "id" and "en":
   [{"id": <id>, "en": "<translated_text>"}]
No markdown codeblocks, no commentary, only the raw JSON array.
"""

# Global State
checkpoint = {}
checkpoint_lock = threading.Lock()
stop_event = threading.Event()
work_queue = queue.Queue()
stats_counter = [0]


def get_api_key():
    if os.path.exists(ENV_PATH):
        with open(ENV_PATH, encoding="utf-8", errors="ignore") as f:
            for line in f:
                line = line.strip()
                if line.startswith("VISION_BRIDGE_API_KEY="):
                    return line.split("=", 1)[1].strip('"\' ')
                elif line.startswith("API_KEY="):
                    return line.split("=", 1)[1].strip('"\' ')
    return ""


API_KEY = get_api_key()
HEADERS = {
    "Authorization": f"Bearer {API_KEY}",
    "Content-Type": "application/json"
}


def load_checkpoint():
    global checkpoint
    if CHECKPOINT_PATH.exists():
        try:
            print(f"Loading existing checkpoint from {CHECKPOINT_PATH}...")
            with open(CHECKPOINT_PATH, "r", encoding="utf-8") as f:
                checkpoint = json.load(f)
            print(f"Loaded {len(checkpoint)} existing translations.")
        except Exception as ex:
            print(f"Error loading checkpoint: {ex}")
            checkpoint = {}


def save_checkpoint():
    with checkpoint_lock:
        data_copy = dict(checkpoint)
    tmp_path = ROOT_DIR / "race_checkpoint.json.tmp"
    try:
        with open(tmp_path, "w", encoding="utf-8") as f:
            json.dump(data_copy, f, ensure_ascii=False, indent=1)
        if os.path.exists(CHECKPOINT_PATH):
            os.replace(tmp_path, CHECKPOINT_PATH)
        else:
            os.rename(tmp_path, CHECKPOINT_PATH)
    except Exception as ex:
        print(f"Error saving checkpoint: {ex}")


def checkpoint_flusher():
    while not stop_event.is_set():
        time.sleep(FLUSH_INTERVAL)
        save_checkpoint()


def parse_translations(raw_content, expected_count):
    clean = raw_content.strip()
    if "```json" in clean:
        clean = clean.split("```json")[1].split("```")[0].strip()
    elif "```" in clean:
        clean = clean.split("```")[1].split("```")[0].strip()

    try:
        data = json.loads(clean)
        if isinstance(data, list):
            res = {}
            for item in data:
                if isinstance(item, dict) and "id" in item and "en" in item:
                    res[item["id"]] = item["en"]
            return res
        elif isinstance(data, dict):
            for k in ["translations", "results", "data", "items"]:
                if k in data and isinstance(data[k], list):
                    res = {}
                    for item in data[k]:
                        if isinstance(item, dict) and "id" in item and "en" in item:
                            res[item["id"]] = item["en"]
                    return res
            return {}
    except Exception:
        pass

    # Regex fallback
    res = {}
    pattern = re.compile(r'\{\s*"id"\s*:\s*(\d+)\s*,\s*"en"\s*:\s*"(.*?)(?<!\\)"\s*\}', re.DOTALL)
    for m in pattern.finditer(raw_content):
        try:
            item_id = int(m.group(1))
            en_text = m.group(2).encode('utf-8').decode('unicode_escape')
            res[item_id] = en_text
        except Exception:
            pass
    return res


def call_api_with_fallback(primary_model, batch, retries=3, timeout=60, fallback_models=None):
    if fallback_models is None:
        fallback_models = FALLBACK_MODELS

    def _try_model(model, model_retries, model_timeout):
        payload = {
            "model": model,
            "messages": [
                {"role": "system", "content": SYSTEM_PROMPT},
                {"role": "user", "content": json.dumps(batch, ensure_ascii=False)}
            ],
            "temperature": 0.2,
            "max_tokens": 4096
        }
        data_bytes = json.dumps(payload).encode("utf-8")

        for attempt in range(model_retries):
            try:
                req = urllib.request.Request(OMNI_URL, headers=HEADERS, data=data_bytes)
                with urllib.request.urlopen(req, timeout=model_timeout) as resp:
                    resp_data = json.loads(resp.read().decode("utf-8"))
                    content = resp_data["choices"][0]["message"]["content"]
                    parsed = parse_translations(content, len(batch))
                    if len(parsed) >= len(batch) * 0.8:
                        return parsed
                    print(f"[{model}] Warning: incomplete batch ({len(parsed)}/{len(batch)}). Retrying...")
            except urllib.error.HTTPError as e:
                if e.code == 429:
                    wait_time = (attempt + 1) * 15 + random.uniform(1, 5)
                    print(f"[{model}] 429 Rate limited. Waiting {wait_time:.1f}s...")
                    time.sleep(wait_time)
                elif e.code in (400, 401, 403):
                    print(f"[{model}] HTTP {e.code} (non-retryable). Skipping model immediately.")
                    return None
                else:
                    print(f"[{model}] HTTP Error {e.code}: {e}")
                    return None
            except Exception as e:
                err_str = str(e).lower()
                if "timed out" in err_str or "timeout" in err_str:
                    print(f"[{model}] Timeout on attempt {attempt+1}/{model_retries}. Skipping model.")
                    return None
                print(f"[{model}] Error: {e}")
                return None
        return None

    result = _try_model(primary_model, retries, timeout)
    if result is not None:
        return result

    for fallback in fallback_models:
        print(f"[FALLBACK] Trying {fallback} after {primary_model} failed")
        result = _try_model(fallback, 2, 45)
        if result is not None:
            return result

    return None


def worker_thread(worker_id, model, batch_size, timeout):
    while not stop_event.is_set():
        batch = []
        try:
            while len(batch) < batch_size:
                item = work_queue.get_nowait()
                batch.append(item)
        except queue.Empty:
            if not batch:
                break

        api_payload = [{"id": idx, "jp": text} for idx, text in batch]
        t0 = time.time()
        results = call_api_with_fallback(model, api_payload, retries=3, timeout=timeout)
        elapsed = time.time() - t0

        if results:
            success_count = 0
            with checkpoint_lock:
                for idx, jp_text in batch:
                    if idx in results:
                        checkpoint[jp_text] = results[idx]
                        success_count += 1
                    else:
                        work_queue.put((idx, jp_text))
            stats_counter[0] += success_count
            print(f"[{worker_id}] Translated {success_count}/{len(batch)} in {elapsed:.2f}s | Queue: {work_queue.qsize()}")
        else:
            print(f"[{worker_id}] Batch FAILED. Re-queueing {len(batch)} items...")
            for item in batch:
                work_queue.put(item)
            time.sleep(3)


def extract_missing():
    """Query master.mdb and local dicts, return {type: [(id_str, jp_text)]}"""
    import sqlite3
    conn = sqlite3.connect(f"file:{MDB_PATH}?mode=ro", uri=True)
    c = conn.cursor()

    # Load local dicts
    with open(MSG_DICT_GEMINI, encoding="utf-8") as f:
        msg_dict = json.load(f)
    with open(CMT_DICT_GEMINI, encoding="utf-8") as f:
        cmt_dict = json.load(f)

    missing = {"message": [], "comment": []}

    # race_jikkyo_message
    c.execute('SELECT DISTINCT "id" FROM "race_jikkyo_message"')
    master_msg_ids = {str(r[0]) for r in c.fetchall()}
    missing_msg_ids = master_msg_ids - set(msg_dict.keys())
    for mid in sorted(missing_msg_ids, key=int):
        c.execute('SELECT "message" FROM "race_jikkyo_message" WHERE "id" = ?', (int(mid),))
        row = c.fetchone()
        if row:
            jp = row[0]
            # Normalize backslash-n
            jp = jp.replace("\\n", "\n")
            missing["message"].append((int(mid), jp))

    # race_jikkyo_comment
    c.execute('SELECT DISTINCT "id" FROM "race_jikkyo_comment"')
    master_cmt_ids = {str(r[0]) for r in c.fetchall()}
    missing_cmt_ids = master_cmt_ids - set(cmt_dict.keys())
    for mid in sorted(missing_cmt_ids, key=int):
        c.execute('SELECT "message" FROM "race_jikkyo_comment" WHERE "id" = ?', (int(mid),))
        row = c.fetchone()
        if row:
            jp = row[0]
            jp = jp.replace("\\n", "\n")
            missing["comment"].append((int(mid), jp))

    conn.close()
    return missing


def main():
    print("=== Race Jikkyo Translation Pipeline ===")
    load_checkpoint()

    flusher = threading.Thread(target=checkpoint_flusher, daemon=True)
    flusher.start()

    # Extract missing from master.mdb
    print("\nExtracting missing rows from master.mdb...")
    missing = extract_missing()
    msg_items = missing["message"]
    cmt_items = missing["comment"]
    total_missing = len(msg_items) + len(cmt_items)
    print(f"Missing message: {len(msg_items)}, comment: {len(cmt_items)}, total: {total_missing}")

    # Filter out already-translated (dedup with checkpoint)
    to_translate_msg = []
    for idx, jp in msg_items:
        if jp not in checkpoint:
            to_translate_msg.append((idx, jp))
        else:
            stats_counter[0] += 1

    to_translate_cmt = []
    for idx, jp in cmt_items:
        if jp not in checkpoint:
            to_translate_cmt.append((idx, jp))
        else:
            stats_counter[0] += 1

    to_translate = to_translate_msg + to_translate_cmt
    print(f"Already in checkpoint (dedup): {total_missing - len(to_translate)}")
    print(f"Need API translation: {len(to_translate)}")

    if not to_translate:
        print("Nothing to translate!")
    else:
        # Enqueue all
        for idx, jp in to_translate:
            work_queue.put((idx, jp))

        print(f"\nStarting {NUM_WORKERS} workers, batch size {BATCH_SIZE}...")
        print(f"Estimated batches: {(len(to_translate) + BATCH_SIZE - 1) // BATCH_SIZE}")

        threads = []
        for i in range(NUM_WORKERS):
            t = threading.Thread(
                target=worker_thread,
                args=(f"W{i}", PRIMARY_MODEL, BATCH_SIZE, 60),
                daemon=True
            )
            t.start()
            threads.append(t)

        # Wait for completion
        while not stop_event.is_set():
            cq = work_queue.qsize()
            if cq == 0:
                # Check all threads done
                alive = any(t.is_alive() for t in threads)
                if not alive:
                    break
            time.sleep(2)

        stop_event.set()
        for t in threads:
            t.join(timeout=5)

    save_checkpoint()
    print(f"\nTranslation phase complete. Checkpoint: {len(checkpoint)} entries.")
    print(f"Total translated this run: {stats_counter[0]}")

    # ---- Phase 2: Merge into dicts ----
    print("\n=== MERGE PHASE ===")
    merge_into_dicts(msg_items, cmt_items)


def sanitize_en(text):
    """Clean up translation output."""
    if not text:
        return text
    text = text.replace("\r\n", "\n").replace("\r", "\n")
    # Remove surrounding quotes if present
    text = text.strip()
    if text.startswith('"') and text.endswith('"') and len(text) > 2:
        text = text[1:-1]
    return text


def merge_into_dicts(msg_items, cmt_items):
    """Merge all translated entries into both gemini and hachimi repos."""
    # Load both dicts
    with open(MSG_DICT_GEMINI, encoding="utf-8") as f:
        msg_dict = json.load(f)
    with open(CMT_DICT_GEMINI, encoding="utf-8") as f:
        cmt_dict = json.load(f)

    added_msg = 0
    added_cmt = 0
    missing_en_msg = []
    missing_en_cmt = []

    for idx, jp in msg_items:
        key = str(idx)
        if key not in msg_dict:
            en = checkpoint.get(jp)
            if en:
                msg_dict[key] = sanitize_en(en)
                added_msg += 1
            else:
                missing_en_msg.append(idx)

    for idx, jp in cmt_items:
        key = str(idx)
        if key not in cmt_dict:
            en = checkpoint.get(jp)
            if en:
                cmt_dict[key] = sanitize_en(en)
                added_cmt += 1
            else:
                missing_en_cmt.append(idx)

    print(f"Added to msg_dict: {added_msg}")
    print(f"Added to cmt_dict: {added_cmt}")
    if missing_en_msg:
        print(f"WARNING: msg missing EN in checkpoint: {len(missing_en_msg)} ids: {missing_en_msg[:10]}...")
    if missing_en_cmt:
        print(f"WARNING: cmt missing EN in checkpoint: {len(missing_en_cmt)} ids: {missing_en_cmt[:10]}...")

    # Write to gemini
    def write_dict(path, data):
        tmp = str(path) + ".tmp"
        with open(tmp, "w", encoding="utf-8", newline="\n") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
        os.replace(tmp, str(path))

    write_dict(MSG_DICT_GEMINI, msg_dict)
    write_dict(MSG_DICT_HACHIMI, msg_dict)
    write_dict(CMT_DICT_GEMINI, cmt_dict)
    write_dict(CMT_DICT_HACHIMI, cmt_dict)

    # Verify identical
    def file_hash(p):
        with open(p, "rb") as f:
            return hashlib.md5(f.read()).hexdigest()
    import hashlib
    for name in ["race_jikkyo_message_dict.json", "race_jikkyo_comment_dict.json"]:
        gh = file_hash(str(MSG_DICT_GEMINI) if "message" in name else str(CMT_DICT_GEMINI))
        hh = file_hash(str(MSG_DICT_HACHIMI) if "message" in name else str(CMT_DICT_HACHIMI))
        print(f"{name}: gemini={gh}, hachimi={hh}, identical={gh==hh}")

    # Final counts
    print(f"\nFinal msg_dict keys: {len(msg_dict)}")
    print(f"Final cmt_dict keys: {len(cmt_dict)}")
    print(f"Total added: {added_msg + added_cmt}")

    # Sample EN lines (25-36 fanfare Feb Stakes)
    print("\n=== SAMPLE EN LINES ===")
    for sid in ["25", "26", "27", "28", "29", "30", "31", "32", "33", "34", "35", "36"]:
        if sid in msg_dict:
            print(f"  msg[{sid}]: {msg_dict[sid][:100]}")

    # Show 10 sample cmt entries
    print("\n=== SAMPLE CMT EN LINES ===")
    cmt_keys = sorted([int(k) for k in cmt_dict.keys()])
    for k in cmt_keys[-10:]:
        print(f"  cmt[{k}]: {msg_dict.get(str(k), cmt_dict[str(k)])[:100]}")


if __name__ == "__main__":
    main()
