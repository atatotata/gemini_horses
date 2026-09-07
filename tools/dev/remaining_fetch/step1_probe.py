#!/usr/bin/env python3
"""Step 1: Precisely compute story/data gaps for prefixes 50/40/11/80/83."""
import apsw
import os
import json

DB_URI = r"file:C:\TMP\meta_fresh.bin?hexkey=9c2bab97bcf8c0c4f1a9ea7881a213f6c9ebf9d8d4c6a8e43ce5a259bde7e9fd"
LOCALIZED_BASE = r"G:\Games\steamapps\common\UmamusumePrettyDerby_Jpn\gemini_horses\localized_data\assets\story\data"
PREFIXES = ["50", "40", "11", "80", "83"]

db = apsw.Connection(DB_URI, flags=apsw.SQLITE_OPEN_READONLY | apsw.SQLITE_OPEN_URI)

# Get all storytimeline entries from meta per prefix
meta_entries = {}  # prefix -> {full_path: (n, h, e)}
for pfx in PREFIXES:
    like_pat = f"story/data/{pfx}/%/storytimeline_%"
    cur = db.execute("SELECT n, h, e FROM a WHERE n LIKE ?", (like_pat,))
    meta_entries[pfx] = {}
    for row in cur:
        meta_entries[pfx][row[0]] = row  # n -> (n, h, e)
    print(f"Meta prefix {pfx}: {len(meta_entries[pfx])} storytimeline entries")

# Get all localized storytimeline files
localized_entries = {}  # prefix -> set of relative paths
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

# Compute gaps
print("\n=== GAP ANALYSIS ===")
all_gap = []
for pfx in PREFIXES:
    meta_paths = set(meta_entries[pfx].keys())
    loc_paths = localized_entries[pfx]
    gap = meta_paths - loc_paths
    print(f"Prefix {pfx}: meta={len(meta_paths)}, localized={len(loc_paths)}, GAP={len(gap)}")
    for g in sorted(gap):
        entry = meta_entries[pfx][g]
        all_gap.append(entry)

print(f"\nTotal gap files: {len(all_gap)}")

# Save gap list for step 2
gap_list = [(n, h, e) for (n, h, e) in all_gap]
with open(r"C:\TMP\remaining_fetch\gap_list.json", "w") as f:
    json.dump(gap_list, f)
print(f"Saved gap_list.json with {len(gap_list)} entries")

# Verify dat availability
dat_base = r"G:\Games\steamapps\common\UmamusumePrettyDerby_Jpn\UmamusumePrettyDerby_Jpn_Data\Persistent"
found = 0
missing = 0
for n, h, e in all_gap:
    dat_path = os.path.join(dat_base, h[:2], h)
    if os.path.exists(dat_path):
        found += 1
    else:
        missing += 1
        if missing <= 5:
            print(f"  MISSING DAT: {dat_path} (for {n})")
print(f"DAT availability: found={found}, missing={missing}")

db.close()
