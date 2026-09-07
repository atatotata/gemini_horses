import urllib.request
import json
import sqlite3
import os
import sys

API_KEY = "sk-ae42a8a723e74bcf7991316b23d9b1c1cb1fb278a2e164f79693bc2fce77a5ea"
OMNI_URL = "http://127.0.0.1:20128/v1/chat/completions"
MODEL = "antigravity/gemini-3.7-flash-low"

JP_MASTER = r"G:\Games\steamapps\common\UmamusumePrettyDerby_Jpn\UmamusumePrettyDerby_Jpn_Data\Persistent\master\master.mdb"
TEXT_DATA_DICT = r"G:\Games\steamapps\common\UmamusumePrettyDerby_Jpn\gemini_horses\localized_data\text_data_dict.json"

print("1. Fetching UmaTL lore category 48 from release branch...")
url_lore = "https://raw.githubusercontent.com/UmaTL/hachimi-tl-en/release/localized_data/text_data_dict.json"
req_lore = urllib.request.Request(url_lore, headers={"User-Agent": "Mozilla/5.0"})
with urllib.request.urlopen(req_lore, timeout=20) as resp:
    lore_dict = json.loads(resp.read().decode("utf-8"))

umatl_cat48 = lore_dict.get("48", {})
print(f"Loaded {len(umatl_cat48)} UmaTL human lore skill descriptions.")

print("2. Reading JP master text_data category 48...")
conn = sqlite3.connect(JP_MASTER)
c = conn.cursor()
c.execute("SELECT [index], text FROM text_data WHERE category = 48")
all_jp_skills = {str(r[0]): r[1] for r in c.fetchall()}
conn.close()
print(f"Loaded {len(all_jp_skills)} skills from master.mdb.")

missing_skills = {k: v for k, v in all_jp_skills.items() if k not in umatl_cat48}
print(f"Identified {len(missing_skills)} skills needing translation into natural lore style.")

# Batch translate missing skills
items = [{"id": k, "jp": v} for k, v in missing_skills.items()]
batch_size = 35
translated_missing = {}

system_prompt = """You are an expert translator for Umamusume: Pretty Derby.
Translate each skill description from Japanese to natural, idiomatic, narrative English in the style of official game descriptions or UmaTL lore translations.

CRITICAL RULES:
- Do NOT use numerical skill data formulas (e.g. no "Target Speed +0.25 m/s", no "duration 5 s", no math equations).
- Do NOT use HTML tags like <b>, </b>, <color>, etc.
- Use natural gameplay phrasing: "Slightly increases speed...", "When competing near the front during the mid-race...", "Accelerates when entering the final stretch...", etc.
- Preserve proper nouns and Umamusume racing terms (Runner, Leader, Betweener, Chaser, Turf, Dirt, Sprint, Mile, Medium, Long, etc.).

Return ONLY a JSON object:
{"translations": [{"id": "...", "en": "..."}]}"""

for i in range(0, len(items), batch_size):
    batch = items[i:i+batch_size]
    print(f"Translating batch {i//batch_size + 1}/{(len(items)+batch_size-1)//batch_size} ({len(batch)} items)...")
    
    payload = {
        "model": MODEL,
        "messages": [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": json.dumps(batch, ensure_ascii=False)}
        ],
        "temperature": 0.2
    }
    
    req = urllib.request.Request(OMNI_URL, data=json.dumps(payload).encode("utf-8"), headers={
        "Content-Type": "application/json",
        "Authorization": f"Bearer {API_KEY}"
    })
    
    for attempt in range(3):
        try:
            with urllib.request.urlopen(req, timeout=30) as resp:
                res = json.loads(resp.read().decode("utf-8"))
            content = res["choices"][0]["message"]["content"].strip()
            if content.startswith("```"):
                lines = content.splitlines()
                if lines[0].startswith("```"):
                    lines = lines[1:]
                if lines and lines[-1].startswith("```"):
                    lines = lines[:-1]
                content = "\n".join(lines).strip()
            
            parsed = json.loads(content)
            for item in parsed.get("translations", []):
                translated_missing[str(item["id"])] = item["en"]
            break
        except Exception as e:
            print(f"  Attempt {attempt+1} failed: {e}")
            if attempt == 2:
                print("  Failed batch! Falling back to raw text.")
                for item in batch:
                    translated_missing[str(item["id"])] = item["jp"]

print(f"Translated {len(translated_missing)} missing skills.")

# Combine UmaTL lore (1858) + translated missing (309)
combined_cat48 = {}
for k in all_jp_skills:
    if k in umatl_cat48:
        combined_cat48[k] = umatl_cat48[k]
    elif k in translated_missing:
        combined_cat48[k] = translated_missing[k]
    else:
        combined_cat48[k] = all_jp_skills[k]

print(f"Combined category 48 total: {len(combined_cat48)} skills.")

# Verify no HTML tags in cat 48
has_html = sum(1 for v in combined_cat48.values() if "<b>" in v or "Target Speed" in v)
print(f"Sanity check: skills containing '<b>' or 'Target Speed': {has_html} (should be 0)")

print("3. Updating localized_data/text_data_dict.json...")
with open(TEXT_DATA_DICT, "r", encoding="utf-8") as f:
    full_dict = json.load(f)

full_dict["48"] = combined_cat48

with open(TEXT_DATA_DICT, "w", encoding="utf-8", newline="\n") as f:
    json.dump(full_dict, f, ensure_ascii=False, indent=2)

print("text_data_dict.json successfully updated for Lore Edition!")
