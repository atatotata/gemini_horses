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
ROOT_DIR = Path(r"C:/TMP/opencode/career_fetch")
CHECKPOINT_PATH = ROOT_DIR / "career_checkpoint.json"
PRE_RESOLVED_PATH = ROOT_DIR / "pre_resolved_names.json"
UNRESOLVED_NAMES_PATH = ROOT_DIR / "unresolved_names.json"
CHOICES_PATH = ROOT_DIR / "unique_choices.json"
DIALOGUES_PATH = ROOT_DIR / "unique_dialogues.json"
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

SYSTEM_PROMPT = """You are an expert Japanese-to-English translator for the game Umamusume: Pretty Derby.
Translate the provided JSON array of Japanese texts into natural, character-accurate English.

Rules:
1. Maintain the emotional tone, personality, and nuance of the speaker.
2. Preserve in-game formatting tokens and tags EXACTLY:
   - <chrname>, <support>, <username>
   - Color tags like <color=...>...</color>
   - \\n for line breaks (do NOT strip line breaks or double-escape them)
3. Use official/canonical character names (e.g., Efforia, Symboli Kris S, Curren Chan, Agnes Tachyon, Gold Ship, Special Week, Chairwoman Akikawa).
4. Output strictly a JSON array of objects with "id" and "en":
   [{"id": <id>, "en": "<translated_text>"}]
No markdown codeblocks, no commentary, only the raw JSON array.
"""

# Global State
checkpoint = {}
checkpoint_lock = threading.Lock()
stop_event = threading.Event()

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
            
    # Load pre-resolved names into checkpoint if not present
    if PRE_RESOLVED_PATH.exists():
        with open(PRE_RESOLVED_PATH, "r", encoding="utf-8") as f:
            pre_names = json.load(f)
        added = 0
        with checkpoint_lock:
            for jp, en in pre_names.items():
                if jp not in checkpoint:
                    checkpoint[jp] = en
                    added += 1
        print(f"Initialized {added} pre-resolved speaker names into checkpoint.")

def checkpoint_flusher():
    while not stop_event.is_set():
        time.sleep(5)
        save_checkpoint()

def save_checkpoint():
    with checkpoint_lock:
        data_copy = dict(checkpoint)
    tmp_path = ROOT_DIR / "career_checkpoint.json.tmp"
    try:
        with open(tmp_path, "w", encoding="utf-8") as f:
            json.dump(data_copy, f, ensure_ascii=False, indent=1)
        if os.path.exists(CHECKPOINT_PATH):
            os.replace(tmp_path, CHECKPOINT_PATH)
        else:
            os.rename(tmp_path, CHECKPOINT_PATH)
    except Exception as ex:
        print(f"Error saving checkpoint: {ex}")

def parse_translations(raw_content: str, expected_count: int):
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
            # Check for keys like "translations" or "results"
            for k in ["translations", "results", "data", "items"]:
                if k in data and isinstance(data[k], list):
                    res = {}
                    for item in data[k]:
                        if isinstance(item, dict) and "id" in item and "en" in item:
                            res[item["id"]] = item["en"]
                    return res
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

def call_api_with_fallback(primary_model: str, batch: list, retries=3, timeout=60, fallback_models=None):
    """Try primary model; on 429 exhaustion, cascade through fallback_models.

    - Primary: retries attempts with exponential backoff + jitter on 429.
    - Fallbacks: tried sequentially (retries=2, timeout=60 each) until one
      returns a parse with >= 80 % coverage.
    - Preserves incomplete-batch retry and general HTTPError handling.
    """
    if fallback_models is None:
        fallback_models = FALLBACK_MODELS

    # --- helper: single-model retry loop ---
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

        return None  # exhausted retries for this model

    # --- try primary ---
    result = _try_model(primary_model, retries, timeout)
    if result is not None:
        return result

    # --- cascade through fallbacks ---
    for fallback in fallback_models:
        print(f"[FALLBACK] Trying {fallback} after {primary_model} 429")
        result = _try_model(fallback, 2, 45)
        if result is not None:
            return result

    return None


def call_api(model: str, batch: list, retries=3, timeout=60):
    """Backward-compatible wrapper -- delegates to fallback-aware function."""
    return call_api_with_fallback(model, batch, retries, timeout, FALLBACK_MODELS)

def worker_thread(worker_id: str, model: str, work_queue: queue.Queue, batch_size: int, timeout: int, stats_counter: list):
    while not stop_event.is_set():
        batch = []
        try:
            while len(batch) < batch_size:
                item = work_queue.get_nowait()
                batch.append(item)
        except queue.Empty:
            if not batch:
                break
                
        # batch: [(idx, jp_text), ...]
        api_payload = [{"id": i, "jp": text} for i, (idx, text) in enumerate(batch)]
        
        t0 = time.time()
        results = call_api(model, api_payload, retries=3, timeout=timeout)
        elapsed = time.time() - t0
        
        if results:
            success_count = 0
            with checkpoint_lock:
                for i, (idx, jp_text) in enumerate(batch):
                    if i in results:
                        checkpoint[jp_text] = results[i]
                        success_count += 1
                    else:
                        # Re-queue missing item
                        work_queue.put((idx, jp_text))
            stats_counter[0] += success_count
            print(f"[{worker_id} - {model.split('/')[-1]}] Translated {success_count}/{len(batch)} in {elapsed:.2f}s | Queue remaining: {work_queue.qsize()}")
        else:
            print(f"[{worker_id} - {model.split('/')[-1]}] Batch FAILED after retries. Re-queueing {len(batch)} items...")
            for item in batch:
                work_queue.put(item)
            time.sleep(3)

def main():
    print("=== Starting Dual-Engine Fan-out Translation Pipeline ===")
    load_checkpoint()
    
    # Background flusher
    flusher = threading.Thread(target=checkpoint_flusher, daemon=True)
    flusher.start()
    
    # Load queues
    print("\nPreparing queues...")
    with open(UNRESOLVED_NAMES_PATH, "r", encoding="utf-8") as f:
        unresolved_names = json.load(f)
    with open(CHOICES_PATH, "r", encoding="utf-8") as f:
        choices = json.load(f)
    with open(DIALOGUES_PATH, "r", encoding="utf-8") as f:
        dialogues = json.load(f)
        
    choice_queue = queue.Queue()
    dialogue_queue = queue.Queue()
    
    # Add items not yet in checkpoint
    untranslated_names = [n for n in unresolved_names if n not in checkpoint]
    untranslated_choices = [c for c in choices if c not in checkpoint]
    untranslated_dialogues = [d for d in dialogues if d not in checkpoint]
    
    print(f"Remaining unresolved names: {len(untranslated_names)}")
    print(f"Remaining choices: {len(untranslated_choices)}")
    print(f"Remaining dialogues: {len(untranslated_dialogues)}")
    print(f"Total remaining to translate: {len(untranslated_names) + len(untranslated_choices) + len(untranslated_dialogues)}")
    
    # Fast path: translate unresolved names first (usually small)
    if untranslated_names:
        print(f"\nTranslating {len(untranslated_names)} speaker names with Gemini Flash...")
        name_batch_size = 100
        for i in range(0, len(untranslated_names), name_batch_size):
            batch_slice = untranslated_names[i:i+name_batch_size]
            api_batch = [{"id": j, "jp": name} for j, name in enumerate(batch_slice)]
            res = call_api("antigravity/gemini-3.7-flash-low", api_batch, retries=3, timeout=30)
            if res:
                with checkpoint_lock:
                    for j, name in enumerate(batch_slice):
                        if j in res:
                            checkpoint[name] = res[j]
            print(f"Names progress: {min(i+name_batch_size, len(untranslated_names))}/{len(untranslated_names)}")
        save_checkpoint()
        
    for i, c in enumerate(untranslated_choices):
        choice_queue.put((i, c))
    for i, d in enumerate(untranslated_dialogues):
        dialogue_queue.put((i, d))
        
    stats_counter = [0]
    threads = []
    
    # Pool A: Gemini Flash workers (bulk dialogues + remaining choices)
    # 6 workers for dialogue
    for w in range(6):
        t = threading.Thread(
            target=worker_thread,
            args=(f"Flash-Dial-{w+1}", "antigravity/gemini-3.7-flash-low", dialogue_queue, 50, 60, stats_counter),
            daemon=True
        )
        threads.append(t)
        t.start()
        
    # 2 workers on Flash for choices
    for w in range(2):
        t = threading.Thread(
            target=worker_thread,
            args=(f"Flash-Choice-{w+1}", "antigravity/gemini-3.7-flash-low", choice_queue, 50, 60, stats_counter),
            daemon=True
        )
        threads.append(t)
        t.start()
        
    # Pool B: Muse Spark Contributor workers (choices + nuanced dialogues)
    # 2 workers on Muse Spark for choices
    for w in range(2):
        t = threading.Thread(
            target=worker_thread,
            args=(f"Muse-Choice-{w+1}", "opencode-go/muse-spark-1.2-contributor", choice_queue, 20, 90, stats_counter),
            daemon=True
        )
        threads.append(t)
        t.start()
        
    print(f"\nDispatched {len(threads)} worker threads across Gemini Flash & Muse Spark Contributor.")
    
    try:
        while True:
            alive = any(t.is_alive() for t in threads)
            cq = choice_queue.qsize()
            dq = dialogue_queue.qsize()
            print(f"[Status Monitor] Remaining -> Choices: {cq}, Dialogues: {dq} | Checkpoint total: {len(checkpoint)}")
            if not alive and (cq == 0 and dq == 0):
                break
            time.sleep(10)
    except KeyboardInterrupt:
        print("\nInterrupt received. Stopping threads...")
        stop_event.set()
        
    stop_event.set()
    for t in threads:
        t.join(timeout=2)
        
    save_checkpoint()
    print("\nTranslation run completed or saved cleanly.")

if __name__ == "__main__":
    main()
