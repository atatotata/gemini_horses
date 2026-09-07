"""
Translate Story Event 09 remaining 198 files.
Reuses translate_extra.py pattern: dedicated name/dialogue/choice queues,
6 Flash dial + 2 Flash choice workers, atomic flush every 5s.
"""
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
ROOT_DIR = Path(r"C:/TMP/extra_fetch")
CHECKPOINT_PATH = ROOT_DIR / "extra_checkpoint.json"
CHECKPOINT_09_PATH = ROOT_DIR / "extra_checkpoint_09.json"
NAMES_PATH = ROOT_DIR / "unresolved_names_09.json"
DIALOGUES_PATH = ROOT_DIR / "unique_dialogues_09.json"
CHOICES_PATH = ROOT_DIR / "unique_choices_09.json"
PRE_RESOLVED_PATH = ROOT_DIR / "pre_resolved_names_09.json"
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
3. Use official/canonical character names (e.g., Efforia, Symboli Kris S, Curren Chan, Agnes Tachyon, Gold Ship, Special Week, Chairwoman Akikawa, Mejiro McQueen, Viron, Vivas, Vivlos, Sakura Chiyono O, Nakayama Festa, Matikanefukukitaru, Meisho Doto, Haru Urara, TM Opera O, Admire Vega, Gold Ship, Grass Wonder, Hishi Amazon, Silence Suzuka, Tokai Teio, Maruzensky, Fuji Kiseki, Oguri Cap, Vodka, Daiwa Scarlet, Taiki Shuttle, Symboli Rudolf, Rice Shower, Rice Shower).
4. For speaker names that are not recognizable character names, translate them naturally (e.g., "イベントスタッフ" -> "Event Staff", "インタビュアー" -> "Interviewer", "観客" -> "Spectator").
5. Output strictly a JSON array of objects with "id" and "en":
   [{"id": <id>, "en": "<translated_text>"}]
No markdown codeblocks, no commentary, only the raw JSON array.
"""

SYSTEM_PROMPT_NAMES = """You are an expert Japanese-to-English translator for the game Umamusume: Pretty Derby.
Translate the provided JSON array of Japanese speaker names/labels into their English equivalents.

Rules:
1. Use official/canonical character names where possible (e.g., Matikanefukukitaru, Meisho Doto, Haru Urara, TM Opera O, Admire Vega, Gold Ship, Grass Wonder, Hishi Amazon, etc.)
2. For group labels, translate naturally: "2人" -> "Both", "3人" -> "All Three", "4人" -> "All Four", etc.
3. For generic labels: "モノローグ" -> "Narrator", "イベントスタッフ" -> "Event Staff", "インタビュアー" -> "Interviewer", "観客" -> "Spectator", etc.
4. For NPC names not in the bible, translate phonetically if they seem like a name, or naturally if they're a role/title.
5. Output strictly a JSON array of objects with "id" and "en":
   [{"id": <id>, "en": "<translated_name>"}]
No markdown codeblocks, no commentary, only the raw JSON array.
"""

# Global State
checkpoint = {}       # Combined: existing + newly translated in this run
checkpoint_lock = threading.Lock()
stop_event = threading.Event()

def load_checkpoint():
    global checkpoint
    # Load base checkpoint (26 stories)
    if CHECKPOINT_PATH.exists():
        try:
            print(f"Loading base checkpoint from {CHECKPOINT_PATH}...")
            with open(CHECKPOINT_PATH, "r", encoding="utf-8") as f:
                checkpoint = json.load(f)
            print(f"Loaded {len(checkpoint)} base translations.")
        except Exception as ex:
            print(f"Error loading base checkpoint: {ex}")
            checkpoint = {}
    
    # Load 09 checkpoint if exists (incremental)
    if CHECKPOINT_09_PATH.exists():
        try:
            with open(CHECKPOINT_09_PATH, "r", encoding="utf-8") as f:
                cp09 = json.load(f)
            added = 0
            for k, v in cp09.items():
                if k not in checkpoint:
                    checkpoint[k] = v
                    added += 1
            print(f"Loaded {len(cp09)} 09 checkpoint entries, {added} new.")
        except Exception as ex:
            print(f"Error loading 09 checkpoint: {ex}")
    
    # Seed pre-resolved names
    if PRE_RESOLVED_PATH.exists():
        try:
            with open(PRE_RESOLVED_PATH, "r", encoding="utf-8") as f:
                pre_names = json.load(f)
            added = 0
            for jp, en in pre_names.items():
                if jp not in checkpoint:
                    checkpoint[jp] = en
                    added += 1
            print(f"Seeded {added} pre-resolved names into checkpoint.")
        except Exception as ex:
            print(f"Error loading pre-resolved names: {ex}")

def checkpoint_flusher():
    while not stop_event.is_set():
        time.sleep(5)
        save_checkpoint_09()

def save_checkpoint_09():
    """Save only 09-relevant entries to checkpoint_09.json, plus full to base."""
    with checkpoint_lock:
        data_copy = dict(checkpoint)
    
    # Save 09-specific checkpoint
    tmp_path_09 = ROOT_DIR / "extra_checkpoint_09.json.tmp"
    try:
        with open(tmp_path_09, "w", encoding="utf-8") as f:
            json.dump(data_copy, f, ensure_ascii=False, indent=1)
        if os.path.exists(CHECKPOINT_09_PATH):
            os.replace(str(tmp_path_09), str(CHECKPOINT_09_PATH))
        else:
            os.rename(str(tmp_path_09), str(CHECKPOINT_09_PATH))
    except Exception as ex:
        print(f"Error saving 09 checkpoint: {ex}")
    
    # Also save merged base checkpoint
    tmp_path_base = ROOT_DIR / "extra_checkpoint.json.tmp"
    try:
        with open(tmp_path_base, "w", encoding="utf-8") as f:
            json.dump(data_copy, f, ensure_ascii=False, indent=1)
        if os.path.exists(CHECKPOINT_PATH):
            os.replace(str(tmp_path_base), str(CHECKPOINT_PATH))
        else:
            os.rename(str(tmp_path_base), str(CHECKPOINT_PATH))
    except Exception as ex:
        print(f"Error saving base checkpoint: {ex}")

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
                    else:
                        print(f"[{model}] Partial result: {len(parsed)}/{len(batch)}")
            except urllib.error.HTTPError as e:
                err_code = e.code
                print(f"[{model}] HTTP {err_code} on attempt {attempt+1}/{model_retries}")
                if err_code == 429:
                    jitter = 15 * attempt + random.uniform(1, 5)
                    print(f"[{model}] 429 rate limit. Jitter wait {jitter:.1f}s")
                    time.sleep(jitter)
                    continue
                elif err_code == 400:
                    print(f"[{model}] 400 Bad Request. Skipping model.")
                    return None
                else:
                    print(f"[{model}] HTTP Error {e.code}: {e}")
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

def call_api_names_with_fallback(primary_model, batch, retries=3, timeout=30, fallback_models=None):
    """API call variant with names-specific system prompt."""
    if fallback_models is None:
        fallback_models = FALLBACK_MODELS

    def _try_model(model, model_retries, model_timeout):
        payload = {
            "model": model,
            "messages": [
                {"role": "system", "content": SYSTEM_PROMPT_NAMES},
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
                    if len(parsed) >= len(batch) * 0.5:
                        return parsed
            except urllib.error.HTTPError as e:
                err_code = e.code
                print(f"[{model}] Names HTTP {err_code} on attempt {attempt+1}")
                if err_code == 429:
                    jitter = 15 * attempt + random.uniform(1, 5)
                    time.sleep(jitter)
                    continue
                elif err_code == 400:
                    return None
            except Exception as e:
                err_str = str(e).lower()
                if "timed out" in err_str or "timeout" in err_str:
                    return None
                return None
        return None

    result = _try_model(primary_model, retries, timeout)
    if result is not None:
        return result

    for fallback in fallback_models:
        print(f"[FALLBACK] Names: Trying {fallback}")
        result = _try_model(fallback, 2, 30)
        if result is not None:
            return result
    return None

def worker_thread(worker_id, model, work_queue, batch_size, timeout, stats_counter, system_prompt_override=None):
    while not stop_event.is_set():
        batch = []
        try:
            while len(batch) < batch_size:
                item = work_queue.get_nowait()
                batch.append(item)
        except queue.Empty:
            if not batch:
                break
        
        # Use names prompt if batch contains name-type items
        api_payload = [{"id": i, "jp": text} for i, (idx, text) in enumerate(batch)]
        
        t0 = time.time()
        if system_prompt_override:
            # Custom call with names prompt
            payload = {
                "model": model,
                "messages": [
                    {"role": "system", "content": system_prompt_override},
                    {"role": "user", "content": json.dumps(api_payload, ensure_ascii=False)}
                ],
                "temperature": 0.2,
                "max_tokens": 4096
            }
            data_bytes = json.dumps(payload).encode("utf-8")
            results = None
            for attempt in range(3):
                try:
                    req = urllib.request.Request(OMNI_URL, headers=HEADERS, data=data_bytes)
                    with urllib.request.urlopen(req, timeout=timeout) as resp:
                        resp_data = json.loads(resp.read().decode("utf-8"))
                        content = resp_data["choices"][0]["message"]["content"]
                        results = parse_translations(content, len(batch))
                        break
                except urllib.error.HTTPError as e:
                    if e.code == 429:
                        jitter = 15 * attempt + random.uniform(1, 5)
                        print(f"[{worker_id}] 429 jitter {jitter:.1f}s")
                        time.sleep(jitter)
                    elif e.code == 400:
                        print(f"[{worker_id}] 400 skip")
                        break
                    else:
                        print(f"[{worker_id}] HTTP {e.code}")
                        time.sleep(2)
                except Exception as e:
                    err_str = str(e).lower()
                    if "timeout" in err_str:
                        print(f"[{worker_id}] Timeout attempt {attempt+1}")
                        break
                    print(f"[{worker_id}] Error: {e}")
                    break
        else:
            results = call_api_with_fallback(model, api_payload, retries=3, timeout=timeout)
        
        elapsed = time.time() - t0
        
        if results:
            success_count = 0
            with checkpoint_lock:
                for i, (idx, jp_text) in enumerate(batch):
                    if i in results:
                        checkpoint[jp_text] = results[i]
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

def main():
    print("=== Starting Story Event 09 Translation Pipeline ===")
    load_checkpoint()
    
    flusher = threading.Thread(target=checkpoint_flusher, daemon=True)
    flusher.start()
    
    print("\nPreparing queues...")
    with open(NAMES_PATH, "r", encoding="utf-8") as f:
        unresolved_names = json.load(f)
    with open(DIALOGUES_PATH, "r", encoding="utf-8") as f:
        dialogues = json.load(f)
    with open(CHOICES_PATH, "r", encoding="utf-8") as f:
        choices = json.load(f)
    
    name_queue = queue.Queue()
    choice_queue = queue.Queue()
    dialogue_queue = queue.Queue()
    
    untranslated_names = [n for n in unresolved_names if n not in checkpoint]
    untranslated_choices = [c for c in choices if c not in checkpoint]
    untranslated_dialogues = [d for d in dialogues if d not in checkpoint]
    
    print(f"Remaining unresolved names: {len(untranslated_names)}")
    print(f"Remaining dialogues: {len(untranslated_dialogues)}")
    print(f"Remaining choices: {len(untranslated_choices)}")
    total = len(untranslated_names) + len(untranslated_dialogues) + len(untranslated_choices)
    print(f"Total remaining to translate: {total}")
    
    # Phase 1: Translate names in bulk first (fast, high value)
    if untranslated_names:
        print(f"\n--- Phase 1: Translating {len(untranslated_names)} speaker names ---")
        name_batch_size = 100
        for i in range(0, len(untranslated_names), name_batch_size):
            batch_slice = untranslated_names[i:i+name_batch_size]
            api_batch = [{"id": j, "jp": name} for j, name in enumerate(batch_slice)]
            res = call_api_names_with_fallback(PRIMARY_MODEL, api_batch, retries=3, timeout=30)
            if res:
                with checkpoint_lock:
                    for j, name in enumerate(batch_slice):
                        if j in res:
                            checkpoint[name] = res[j]
            progress = min(i+name_batch_size, len(untranslated_names))
            print(f"Names progress: {progress}/{len(untranslated_names)}")
            save_checkpoint_09()
        
        print(f"Names phase complete. Checkpoint: {len(checkpoint)}")
    
    # Phase 2: Fill queues for dialogues and choices
    untranslated_dialogues = [d for d in dialogues if d not in checkpoint]
    untranslated_choices = [c for c in choices if c not in checkpoint]
    
    for i, d in enumerate(untranslated_dialogues):
        dialogue_queue.put((i, d))
    for i, c in enumerate(untranslated_choices):
        choice_queue.put((i, c))
    
    print(f"\n--- Phase 2: Translating {len(untranslated_dialogues)} dialogues + {len(untranslated_choices)} choices ---")
    
    stats_counter = [0]
    threads = []
    
    # 6 Gemini Flash workers for dialogue
    for w in range(6):
        t = threading.Thread(
            target=worker_thread,
            args=(f"Flash-Dial-{w+1}", PRIMARY_MODEL, dialogue_queue, 50, 60, stats_counter),
            daemon=True
        )
        threads.append(t)
        t.start()
    
    # 2 Gemini Flash workers for choices
    for w in range(2):
        t = threading.Thread(
            target=worker_thread,
            args=(f"Flash-Choice-{w+1}", PRIMARY_MODEL, choice_queue, 50, 60, stats_counter),
            daemon=True
        )
        threads.append(t)
        t.start()
    
    print(f"Dispatched {len(threads)} worker threads.")
    
    try:
        while True:
            alive = any(t.is_alive() for t in threads)
            cq = choice_queue.qsize()
            dq = dialogue_queue.qsize()
            nq = name_queue.qsize()
            print(f"[Status] Remaining -> Dialogues: {dq}, Choices: {cq} | Translated: {stats_counter[0]} | Checkpoint: {len(checkpoint)}")
            if not alive and (cq == 0 and dq == 0):
                break
            time.sleep(10)
    except KeyboardInterrupt:
        print("\nInterrupt received. Stopping threads...")
        stop_event.set()
    
    stop_event.set()
    for t in threads:
        t.join(timeout=2)
    
    save_checkpoint_09()
    print(f"\nTranslation complete. Checkpoint has {len(checkpoint)} entries.")
    print(f"Total translated this run: {stats_counter[0]}")

if __name__ == "__main__":
    main()
