#!/usr/bin/env python3
"""Step 1 v2: Precisely compute story/data gaps - handle meta path differences."""
import apsw
import os
import json

DB_URI = r"file:C:\TMP\meta_fresh.bin?hexkey=9c2bab97bcf8c0c4f1a9ea7881a213f6c9ebf9d8d4c6a8e43ce5a259bde7e9fd"
LOCALIZED_BASE = r"G:\Games\steamapps\common\UmamusumePrettyDerby_Jpn\gemini_horses\localized_data\assets\story\data"
PREFIXES = ["50", "40", "11", "80", "83"]
DAT_BASE = r"G:\Games\steamapps\common\UmamusumePrettyDerby_Jpn\UmamusumePrettyDerby_Jpn_Data\Persistent"

db = apsw.Connection(DB_URI, flags=apsw.SQLITE_OPEN_READONLY | apsw.SQLITE_OPEN_URI)

# Get all storytimeline entries from meta per prefix (both resource and non-resource)
meta_all = {}       # prefix -> {n: (n, h, e)}
meta_resources = {} # prefix -> set of n (resourcelist)
meta_stories = {}   # prefix -> set of n (actual stories)
for pfx in PREFIXES:
    like_pat = f"story/data/{pfx}/%/storytimeline_%"
    cur = db.execute("SELECT n, h, e FROM a WHERE n LIKE ?", (like_pat,))
    meta_all[pfx] = {}
    meta_resources[pfx] = set()
    meta_stories[pfx] = set()
    for row in cur:
        meta_all[pfx][row[0]] = row
        if "/resourcelist/" in row[0]:
            meta_resources[pfx].add(row[0])
        else:
            meta_stories[pfx].add(row[0])
    print(f"Meta prefix {pfx}: total={len(meta_all[pfx])}, stories={len(meta_stories[pfx])}, resources={len(meta_resources[pfx])}")

# Get all localized storytimeline files
localized_entries = {}  # prefix -> set of relative paths (with .json)
for pfx in PREFIXES:
    pfx_dir = os.path.join(LOCALIZED_BASE, pfx)
    localized_entries[pfx] = set()
    if not os.path.isdir(pfx_dir):
        print(f"  Localized dir for {pfx} NOT FOUND")
        continue
    for sub in os.listdir(pfx_dir):
        sub_dir = os.path.join(pfx_dir, sub)
        if os.path.isdir(sub_dir):
            for fn in os.listdir(sub_dir):
                if fn.startswith("storytimeline_") and fn.endswith(".json"):
                    rel_path = f"story/data/{pfx}/{sub}/{fn}"
                    localized_entries[pfx].add(rel_path)
    print(f"Localized prefix {pfx}: {len(localized_entries[pfx])} files")

# Compute gaps: meta_stories that don't have corresponding localized .json
print("\n=== GAP ANALYSIS ===")
all_gap = []
for pfx in PREFIXES:
    # Convert meta story paths to localized-style paths for comparison
    meta_as_localized = {}
    for n in meta_stories[pfx]:
        loc_path = n + ".json"
        meta_as_localized[loc_path] = n
    
    loc_paths = localized_entries[pfx]
    gap_paths = set(meta_as_localized.keys()) - loc_paths
    print(f"Prefix {pfx}: meta_stories={len(meta_stories[pfx])}, localized={len(loc_paths)}, GAP={len(gap_paths)}")
    for g in sorted(gap_paths):
        orig_n = meta_as_localized[g]
        entry = meta_all[pfx][orig_n]
        all_gap.append(entry)

print(f"\nTotal gap files: {len(all_gap)}")

# Save gap list for step 2
gap_list = [(n, h, e) for (n, h, e) in all_gap]
with open(r"C:\TMP\remaining_fetch\gap_list.json", "w") as f:
    json.dump(gap_list, f)
print(f"Saved gap_list.json")

# Verify dat availability
found = 0
missing = 0
missing_samples = []
for n, h, e in all_gap:
    dat_path = os.path.join(DAT_BASE, h[:2], h)
    if os.path.exists(dat_path):
        found += 1
    else:
        missing += 1
        if missing <= 5:
            missing_samples.append((n, dat_path))
print(f"DAT availability: found={found}, missing={missing}")
for n, dp in missing_samples:
    print(f"  MISSING: {dp} for {n}")

# Breakdown by prefix
print("\n=== PER-PREFIX GAP BREAKDOWN ===")
for pfx in PREFIXES:
    pfx_gap = [x for x in all_gap if x[0].startswith(f"story/data/{pfx}/")]
    print(f"  {pfx}: {len(pfx_gap)} files")

db.close()
