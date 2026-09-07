#!/usr/bin/env python3
"""
Home Timeline Translation Pipeline
===================================
Fan-out dual-engine: names bulk + 6 dialogue workers, 50/batch, 42-col tag-aware wrap.
Reuses translate_09.py / translate_extra.py pattern.
Home is low-choice (0 choices), high-name (52 unresolved names + 9746 dialogues).
"""
import os
import sys
import json
import time
import re
import queue
import random
import threading
import unicodedata
import urllib.request
from pathlib import Path

# ── Paths ──────────────────────────────────────────────────────────────
ROOT_DIR = Path(r"C:/TMP/home_fetch")
HOME_SRC = ROOT_DIR / "story_json" / "home" / "data"
CHECKPOINT_PATH = ROOT_DIR / "home_checkpoint.json"
PRE_RESOLVED_PATH = ROOT_DIR / "home_pre_resolved_names.json"
UNRESOLVED_NAMES_PATH = ROOT_DIR / "home_unresolved_names.json"
DIALOGUES_PATH = ROOT_DIR / "home_unique_dialogues.json"
SCAN_PATH = ROOT_DIR / "scan_home.json"
ENV_PATH = r"C:\Users\Ota\.omniroute\.env"
GH_HOME = Path(r"G:/Games/steamapps/common/UmamusumePrettyDerby_Jpn/gemini_horses/localized_data/assets/home/data")
HA_HOME = Path(r"G:/Games/steamapps/common/UmamusumePrettyDerby_Jpn/hachimi/localized_data_1/assets/home/data")

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

Context: These are casual home/dormitory/training timeline dialogues — relaxed everyday chatter between characters at the training facility. Keep the tone light and conversational.

Rules:
1. Maintain the emotional tone, personality, and nuance of the speaker.
2. Preserve in-game formatting tokens and tags EXACTLY:
   - <chrname>, <support>, <username>, <i>, <b>
   - Color tags like <color=...>...</color>
   - \\n for line breaks (do NOT strip line breaks or double-escape them)
3. Use official/canonical character names (e.g., Efforia, Symboli Kris S, Curren Chan, Agnes Tachyon, Gold Ship, Special Week, Chairwoman Akikawa, Mejiro McQueen, Viron, Vivas, Vivlos, Sakura Chiyono O, Nakayama Festa, Matikanefukukitaru, Meisho Doto, Haru Urara, TM Opera O, Admire Vega, Grass Wonder, Hishi Amazon, Silence Suzuka, Tokai Teio, Maruzensky, Fuji Kiseki, Oguri Cap, Vodka, Daiwa Scarlet, Taiki Shuttle, Symboli Rudolf, Rice Shower).
4. For speaker names that are not recognizable character names, translate them naturally (e.g., "イベントスタッフ" -> "Event Staff", "2人" -> "Both", "全員" -> "Everyone").
5. Output strictly a JSON array of objects with "id" and "en":
   [{"id": <id>, "en": "<translated_text>"}]
No markdown codeblocks, no commentary, only the raw JSON array.
"""

SYSTEM_PROMPT_NAMES = """You are an expert Japanese-to-English translator for the game Umamusume: Pretty Derby.
Translate the provided JSON array of Japanese speaker names/labels into their English equivalents.

Context: These are names from the training dormitory home timeline.

Rules:
1. Use official/canonical character names where possible (from voice bible).
2. For paired group labels (X＆Y format), translate both names to their short English equivalents:
   - e.g., "ゴルシ＆ジョーダン" -> "Gold Ship & Jordan", "タキオン＆カフェ" -> "Tachyon & Cafe"
3. For numeric group labels: "2人" -> "Both", "3人" -> "All Three", "全員" -> "Everyone"
4. For NPC names not in the bible, translate naturally.
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
                    print(f"[{model}] Incomplete batch ({len(parsed)}/{len(batch)}). Retrying...")
            except urllib.error.HTTPError as e:
                err_code = e.code
                if err_code == 429:
                    jitter = 15 * attempt + random.uniform(1, 5)
                    print(f"[{model}] 429 rate limit. Jitter {jitter:.1f}s")
                    time.sleep(jitter)
                    continue
                elif err_code in (400, 401, 403):
                    print(f"[{model}] HTTP {err_code} (non-retryable). Skipping.")
                    return None
                else:
                    print(f"[{model}] HTTP {err_code}: {e}")
                    return None
            except Exception as e:
                err_str = str(e).lower()
                if "timed out" in err_str or "timeout" in err_str:
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

def worker_thread(worker_id, model, work_queue, batch_size, timeout, stats_counter):
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

# ── MAIN ───────────────────────────────────────────────────────────────
def main():
    print("=== Home Timeline Translation Pipeline ===")
    t_start = time.time()

    load_checkpoint()

    flusher = threading.Thread(target=checkpoint_flusher, daemon=True)
    flusher.start()

    print("\nPreparing queues...")
    with open(UNRESOLVED_NAMES_PATH, "r", encoding="utf-8") as f:
        unresolved_names = json.load(f)
    with open(DIALOGUES_PATH, "r", encoding="utf-8") as f:
        dialogues = json.load(f)

    dialogue_queue = queue.Queue()

    untranslated_names = [n for n in unresolved_names if n not in checkpoint]
    untranslated_dialogues = [d for d in dialogues if d not in checkpoint]

    print(f"Unresolved names: {len(untranslated_names)}")
    print(f"Dialogues: {len(untranslated_dialogues)}")
    print(f"Total remaining: {len(untranslated_names) + len(untranslated_dialogues)}")

    # ── Phase 1: Translate names in bulk ──
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

    # ── Phase 2: Translate dialogues via 6 Flash workers ──
    untranslated_dialogues = [d for d in dialogues if d not in checkpoint]
    print(f"\nRemaining dialogues after names: {len(untranslated_dialogues)}")

    for i, d in enumerate(untranslated_dialogues):
        dialogue_queue.put((i, d))

    print(f"\n--- Phase 2: Translating {len(untranslated_dialogues)} dialogues (6 workers) ---")

    stats_counter = [0]
    threads = []

    for w in range(6):
        t = threading.Thread(
            target=worker_thread,
            args=(f"Flash-Dial-{w+1}", PRIMARY_MODEL, dialogue_queue, 50, 60, stats_counter),
            daemon=True
        )
        threads.append(t)
        t.start()

    print(f"Dispatched {len(threads)} worker threads.")

    try:
        while True:
            alive = any(t.is_alive() for t in threads)
            dq = dialogue_queue.qsize()
            print(f"[Status] Dialogues: {dq} | Translated: {stats_counter[0]} | Checkpoint: {len(checkpoint)}")
            if not alive and dq == 0:
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
