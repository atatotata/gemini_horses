"""Investigate why 198 sids lack dat files. Check patterns."""
import json, os
from pathlib import Path
from collections import Counter

GAME_DIR = Path(r"G:/Games/steamapps/common/UmamusumePrettyDerby_Jpn")
DAT_DIR = GAME_DIR / "UmamusumePrettyDerby_Jpn_Data/Persistent/dat"

with open(r"C:\TMP\extra_fetch\story_json\analysis_09.json", "r", encoding="utf-8") as f:
    analysis = json.load(f)

no_dat = analysis['missing_202_no_dat']
with_dat = analysis['missing_202_with_dat']
meta_all = analysis['meta_09_count']

# Group no_dat by sub-prefix (event group)
no_dat_subs = Counter(str(sid)[2:6] for sid in no_dat)
print(f"No-dat sids: {len(no_dat)} across {len(no_dat_subs)} event groups")
print(f"\nEvent groups without dat:")
for sub, cnt in sorted(no_dat_subs.items()):
    print(f"  09{sub}: {cnt} sids")

# The 10 meta entries that DO have dat files
all_dat = analysis['meta_with_dat']
print(f"\nAll 09 meta entries WITH dat ({len(all_dat)}):")
for sid in sorted(all_dat):
    print(f"  {sid}")

# Check if the no-dat sids are all from events that never had bundles
# (e.g., events that were added after client update)
# Look at the event id pattern
no_dat_event_ids = sorted(set(str(sid)[2:6] for sid in no_dat))
print(f"\nNo-dat event sub-prefixes: {no_dat_event_ids}")

# How many TOTAL dat files exist
total_dat_count = sum(1 for _ in DAT_DIR.rglob("*") if _.is_file())
print(f"\nTotal files in dat dir: {total_dat_count}")

# Check if perhaps bundles were cleared
# Look for .bundle or other patterns
sample_dirs = list(DAT_DIR.iterdir())[:5]
for d in sample_dirs:
    if d.is_dir():
        count = len(list(d.iterdir()))
        print(f"  {d.name}/: {count} files")
