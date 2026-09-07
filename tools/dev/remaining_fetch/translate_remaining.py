#!/usr/bin/env python3
"""
Remaining Story Translation Pipeline
=====================================
Translates 4,280 story JSON files (13,768 unique strings).
Phase 1: Names bulk 100/batch.
Phase 2: 6 Flash dial workers 50/batch + 2 choice workers.
Atomic checkpoint flush every 5s.
"""
import os, sys, json, time, re, queue, random, threading, unicodedata, urllib.request
from pathlib import Path

# ── Paths ──────────────────────────────────────────────────────────────
ROOT_DIR = Path(r"C:/TMP/remaining_fetch")
SCAN_PATH = ROOT_DIR / "scan_remaining.json"
CHECKPOINT_PATH = ROOT_DIR / "remaining_checkpoint.json"
ENV_PATH = r"C:\Users\Ota\.omniroute\.env"

# ── API Configuration ──────────────────────────────────────────────────
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
                    return line.split("=", 1)[1].strip("\"' ")
                elif line.startswith("API_KEY="):
                    return line.split("=", 1)[1].strip("\"' ")
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
3. Use official/canonical character names (e.g., Efforia, Symboli Kris S, Curren Chan, Agnes Tachyon, Gold Ship, Special Week, Chairwoman Akikawa, Mejiro McQueen, Viron, Vivas, Vivlos, Sakura Chiyono O, Nakayama Festa).
4. Output strictly a JSON array of objects with "id" and "en":
   [{"id": <id>, "en": "<translated_text>"}]
No markdown codeblocks, no commentary, only the raw JSON array.
"""

SYSTEM_PROMPT_NAMES = """You are an expert Japanese-to-English translator for Umamusume: Pretty Derby.
Translate the provided JSON array of Japanese character/speaker names into English.

Rules:
1. Use official/canonical character names where possible.
2. For paired group labels, translate naturally.
3. For numeric group labels: "2人" -> "Both", "3人" -> "All Three", "全員" -> "Everyone"
4. For NPC/generic names not in the bible, translate naturally.
5. Output strictly a JSON array of objects with "id" and "en":
   [{"id": <id>, "en": "<translated_name>"}]
No markdown codeblocks, no commentary, only the raw JSON array.
"""

# ── 42-col wrap (tag-aware) ────────────────────────────────────────────
TAG_RE = re.compile(r"<[^>]+>")
LIMIT = 42

def char_w(ch):
    eaw = unicodedata.east_asian_width(ch)
    return 2 if eaw in ("W", "F") else 1

def disp_width(s):
    stripped = TAG_RE.sub("", s)
    return sum(char_w(c) for c in stripped)

def wrap_paragraph(para, limit):
    para = para.strip()
    if not para:
        return []
    words = para.split()
    if not words:
        return []
    lines = []
    cur = words[0]
    cur_w = disp_width(cur)
    for w in words[1:]:
        w_w = disp_width(w)
        if w_w > limit:
            lines.append(cur)
            cur = w
            cur_w = w_w
            continue
        sep_w = 1
        if cur_w + sep_w + w_w <= limit:
            cur += " " + w
            cur_w += sep_w + w_w
        else:
            lines.append(cur)
            cur = w
            cur_w = w_w
    lines.append(cur)
    return lines

def wrap_field(text, limit=LIMIT):
    if not text:
        return text
    norm = text.replace("\r\n", "\n").replace("\r", "\n")
    if "\n\n" in norm:
        paras = re.split(r"\n\s*\n", norm)
        out_paras = []
        for para in paras:
            collapsed = re.sub(r"\s+", " ", para.replace("\n", " ").strip())
            if not collapsed:
                out_paras.append("")
                continue
            wrapped = wrap_paragraph(collapsed, limit)
            out_paras.append(" \n".join(wrapped))
        return "\n\n".join(out_paras)
    else:
        collapsed = re.sub(r"\s+", " ", norm.replace("\n", " ").strip())
        if not collapsed:
            return ""
        wrapped = wrap_paragraph(collapsed, limit)
        return " \n".join(wrapped)

# ── Global State ───────────────────────────────────────────────────────
checkpoint = {}
checkpoint_lock = threading.Lock()
stop_event = threading.Event()

def load_checkpoint():
    global checkpoint
    checkpoint = {}
    if CHECKPOINT_PATH.exists():
        try:
            print(f"Loading existing checkpoint from {CHECKPOINT_PATH}...")
            with open(CHECKPOINT_PATH, "r", encoding="utf-8") as f:
                checkpoint = json.load(f)
            print(f"Loaded {len(checkpoint)} existing translations.")
        except Exception as ex:
            print(f"Error loading checkpoint: {ex}")

    # Seed from home checkpoint (prior names reuse)
    hc_path = Path(r"C:/TMP/home_fetch/home_checkpoint.json")
    if hc_path.exists():
        try:
            with open(hc_path, "r", encoding="utf-8") as f:
                hc = json.load(f)
            added = 0
            for jp, en in hc.items():
                if jp not in checkpoint:
                    checkpoint[jp] = en
                    added += 1
            print(f"Seeded {added} pre-resolved from home_checkpoint.")
        except Exception as ex:
            print(f"Error seeding home_checkpoint: {ex}")

def checkpoint_flusher():
    while not stop_event.is_set():
        time.sleep(5)
        save_checkpoint()

def save_checkpoint():
    with checkpoint_lock:
        data_copy = dict(checkpoint)
    tmp_path = CHECKPOINT_PATH.with_suffix(".json.tmp")
    try:
        with open(tmp_path, "w", encoding="utf-8") as f:
            json.dump(data_copy, f, ensure_ascii=False, indent=1)
        if os.path.exists(CHECKPOINT_PATH):
            os.replace(str(tmp_path), str(CHECKPOINT_PATH))
        else:
            os.rename(str(tmp_path), str(CHECKPOINT_PATH))
    except Exception as ex:
        print(f"Error saving checkpoint: {ex}")

# ── Parse / API ────────────────────────────────────────────────────────
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
    # Fallback regex
    res = {}
    pattern = re.compile(r'\{\s*"id"\s*:\s*(\d+)\s*,\s*"en"\s*:\s*"(.*?)(?<!\\)"\s*\}', re.DOTALL)
    for m in pattern.finditer(raw_content):
        try:
            item_id = int(m.group(1))
            en_text = m.group(2).encode("utf-8").decode("unicode_escape")
            res[item_id] = en_text
        except Exception:
            pass
    return res

def call_api_with_fallback(primary_model, batch, retries=3, timeout=60, fallback_models=None, system_prompt=None):
    if fallback_models is None:
        fallback_models = FALLBACK_MODELS
    if system_prompt is None:
        system_prompt = SYSTEM_PROMPT

    def _try_model(model, model_retries, model_timeout):
        payload = {
            "model": model,
            "messages": [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": json.dumps(batch, ensure_ascii=False)}
            ],
            "temperature": 0.2,
            "max_tokens": 4096
        }
        for attempt in range(model_retries):
            try:
                req = urllib.request.Request(
                    OMNI_URL,
                    data=json.dumps(payload, ensure_ascii=False).encode("utf-8"),
                    headers=HEADERS,
                    method="POST"
                )
                with urllib.request.urlopen(req, timeout=model_timeout) as resp:
                    raw = json.loads(resp.read().decode("utf-8"))
                    content = raw["choices"][0]["message"]["content"]
                    return parse_translations(content, len(batch))
            except urllib.error.HTTPError as e:
                code = e.code
                print(f"[{model}] HTTP {code} on attempt {attempt+1}/{model_retries}")
                if code == 429:
                    wait = min(2 ** attempt * 5, 30)
                    print(f"  Rate limited, waiting {wait}s...")
                    time.sleep(wait)
                    continue
                elif code >= 500:
                    time.sleep(3)
                    continue
                else:
                    print(f"[{model}] HTTP Error {e.code}: {e}")
                    break
            except Exception as e:
                err_str = str(e).lower()
                if "timed out" in err_str or "timeout" in err_str:
                    print(f"[{model}] Timeout on attempt {attempt+1}/{model_retries}")
                    time.sleep(2)
                    continue
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

# ── Worker ─────────────────────────────────────────────────────────────
def worker_thread(worker_id, model, work_queue, batch_size, timeout, stats_counter, sp=None):
    while not stop_event.is_set():
        batch = []
        try:
            while len(batch) < batch_size:
                item = work_queue.get_nowait()
                batch.append(item)
        except queue.Empty:
            if not batch:
                break

        api_payload = [{"id": i, "jp": text} for i, (idx, text) in enumerate(batch)]
        t0 = time.time()
        results = call_api_with_fallback(model, api_payload, retries=3, timeout=timeout, system_prompt=sp)
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

# ── MAIN ───────────────────────────────────────────────────────────────
def main():
    print("=== Remaining Story Translation Pipeline ===")
    t_start = time.time()

    load_checkpoint()

    flusher = threading.Thread(target=checkpoint_flusher, daemon=True)
    flusher.start()

    # Load scan
    print("\nLoading scan_remaining.json...")
    with open(SCAN_PATH, "r", encoding="utf-8") as f:
        scan = json.load(f)

    unresolved_names = scan["unresolved_names"]
    unique_texts = scan["unique_texts"]
    unique_choices = scan["unique_choices"]

    untranslated_names = [n for n in unresolved_names if n not in checkpoint]
    untranslated_texts = [t for t in unique_texts if t not in checkpoint]
    untranslated_choices = [c for c in unique_choices if c not in checkpoint]

    print(f"Unresolved names: {len(untranslated_names)}")
    print(f"Unique texts: {len(untranslated_texts)}")
    print(f"Unique choices: {len(untranslated_choices)}")
    total_remaining = len(untranslated_names) + len(untranslated_texts) + len(untranslated_choices)
    print(f"Total remaining to translate: {total_remaining}")

    # ── Phase 1: Translate names in bulk (100/batch) ──
    if untranslated_names:
        print(f"\n--- Phase 1: Translating {len(untranslated_names)} speaker names ---")
        name_batch_size = 100
        for i in range(0, len(untranslated_names), name_batch_size):
            batch_slice = untranslated_names[i:i+name_batch_size]
            api_batch = [{"id": j, "jp": name} for j, name in enumerate(batch_slice)]
            res = call_api_with_fallback(
                PRIMARY_MODEL, api_batch, retries=3, timeout=30,
                system_prompt=SYSTEM_PROMPT_NAMES
            )
            if res:
                with checkpoint_lock:
                    for j, name in enumerate(batch_slice):
                        if j in res:
                            checkpoint[name] = res[j]
            progress = min(i + name_batch_size, len(untranslated_names))
            print(f"Names progress: {progress}/{len(untranslated_names)}")
            save_checkpoint()
        print(f"Names phase complete. Checkpoint: {len(checkpoint)}")

    # ── Phase 2: Translate dialogues (6 workers) + choices (2 workers) ──
    untranslated_texts = [t for t in unique_texts if t not in checkpoint]
    untranslated_choices = [c for c in unique_choices if c not in checkpoint]

    print(f"\nRemaining after names: texts={len(untranslated_texts)}, choices={len(untranslated_choices)}")

    dial_queue = queue.Queue()
    choice_queue = queue.Queue()

    for i, t in enumerate(untranslated_texts):
        dial_queue.put((i, t))
    for i, c in enumerate(untranslated_choices):
        choice_queue.put((i, c))

    stats_counter = [0]
    threads = []

    # 6 dialogue workers
    for w in range(6):
        t = threading.Thread(
            target=worker_thread,
            args=(f"Flash-Dial-{w+1}", PRIMARY_MODEL, dial_queue, 50, 60, stats_counter),
            daemon=True
        )
        threads.append(t)
        t.start()

    # 2 choice workers
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
            dq = dial_queue.qsize()
            cq = choice_queue.qsize()
            print(f"[Status] Dial-queue: {dq} | Choice-queue: {cq} | Translated: {stats_counter[0]} | Checkpoint: {len(checkpoint)}")
            if not alive and dq == 0 and cq == 0:
                break
            time.sleep(10)
    except KeyboardInterrupt:
        print("\nInterrupt received. Stopping threads...")
        stop_event.set()

    stop_event.set()
    for t in threads:
        t.join(timeout=2)

    save_checkpoint()

    elapsed = time.time() - t_start
    print(f"\n=== Translation Complete ===")
    print(f"Checkpoint: {len(checkpoint)} entries")
    print(f"Translated this run: {stats_counter[0]}")
    print(f"Elapsed: {elapsed:.1f}s ({elapsed/60:.1f} min)")

if __name__ == "__main__":
    main()
