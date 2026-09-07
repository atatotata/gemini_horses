"""Query story_event_story_data for prefix-09 type=1 story IDs."""
import sqlite3
from collections import Counter

MASTER_PATH = r"G:\Games\steamapps\common\UmamusumePrettyDerby_Jpn\UmamusumePrettyDerby_Jpn_Data\Persistent\master\master.mdb"
mconn = sqlite3.connect(MASTER_PATH)
mc = mconn.cursor()

# Get all type_1 story IDs from story_event_story_data
mc.execute("""
    SELECT story_id_1 FROM story_event_story_data 
    WHERE story_type_1 = 1
""")
all_type1 = [row[0] for row in mc.fetchall()]
print(f"Total story_type_1=1 entries: {len(all_type1)}")

# Filter prefix 09
prefix_09 = [sid for sid in all_type1 if str(sid).startswith('09')]
print(f"Prefix 09 type=1 entries: {len(prefix_09)}")

# Show distribution by sub-prefix
sub_prefix = Counter(str(sid)[2:6] for sid in prefix_09)
print(f"\nSub-prefix distribution:")
for sp, cnt in sorted(sub_prefix.items()):
    print(f"  09{sp}: {cnt}")

# Unique sids
unique_09 = sorted(set(prefix_09))
print(f"\nUnique prefix 09 sids: {len(unique_09)}")
print(f"Min: {min(unique_09)}, Max: {max(unique_09)}")
print(f"\nFirst 20: {unique_09[:20]}")
print(f"Last 20: {unique_09[-20:]}")

# Check 20290011 (ghost?)
if 20290011 in all_type1 or 20290011 in prefix_09:
    print(f"\nGhost 20290011 FOUND in story_event_story_data")
else:
    print(f"\nGhost 20290011 NOT in story_event_story_data (correct)")

mconn.close()
