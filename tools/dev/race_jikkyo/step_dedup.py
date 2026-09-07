import json

# Load checkpoints
try:
    extra = json.load(open(r"C:/TMP/extra_fetch/extra_checkpoint.json", "r", encoding="utf-8"))
    print(f"extra_checkpoint: {len(extra)} entries")
except:
    extra = {}
    print("extra_checkpoint: not found")

# Load missing data
missing = json.load(open(r"C:/TMP/race_jikkyo/missing_data.json", "r", encoding="utf-8"))
msg_count = missing["missing_msg_count"]
cmt_count = missing["missing_cmt_count"]
print(f"missing msg: {msg_count}, cmt: {cmt_count}")

# Check how many missing JP texts already exist in checkpoint
found_msg = 0
found_cmt = 0
dedup_map = {}

for mid, row in missing["message"].items():
    jp = row["message"]
    if jp in extra:
        found_msg += 1
        dedup_map[mid] = {"type": "message", "jp": jp, "en": extra[jp]}

for mid, row in missing["comment"].items():
    jp = row["message"]
    if jp in extra:
        found_cmt += 1
        dedup_map[mid] = {"type": "comment", "jp": jp, "en": extra[jp]}

print(f"Missing msg already in checkpoint: {found_msg}")
print(f"Missing cmt already in checkpoint: {found_cmt}")
print(f"Total dedup: {found_msg + found_cmt}")
print(f"Need API calls: {1200 - found_msg - found_cmt}")

# Show a few dedup samples
for k, v in list(dedup_map.items())[:5]:
    print(f"  dedup {k}: {v['jp'][:40]} -> {v['en'][:40]}")

# Save dedup map
with open(r"C:/TMP/race_jikkyo/dedup_map.json", "w", encoding="utf-8", newline="\n") as f:
    json.dump(dedup_map, f, ensure_ascii=False, indent=2)
