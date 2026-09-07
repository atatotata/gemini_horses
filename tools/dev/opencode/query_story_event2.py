"""Query story_event_story_data for actual IDs."""
import sqlite3

MASTER_PATH = r"G:\Games\steamapps\common\UmamusumePrettyDerby_Jpn\UmamusumePrettyDerby_Jpn_Data\Persistent\master\master.mdb"
mconn = sqlite3.connect(MASTER_PATH)
mc = mconn.cursor()

# Check what format story IDs are in
mc.execute("SELECT story_id_1, story_type_1, story_event_id FROM story_event_story_data WHERE story_type_1 = 1 LIMIT 20")
for row in mc.fetchall():
    print(f"  story_id_1={row[0]}, type_1={row[1]}, event_id={row[2]}")

# Check if there are 9xxx IDs
mc.execute("SELECT DISTINCT story_id_1 FROM story_event_story_data WHERE story_type_1 = 1")
all_ids = sorted([row[0] for row in mc.fetchall()])
print(f"\nTotal unique story_id_1 with type=1: {len(all_ids)}")
print(f"Sample: {all_ids[:30]}")
print(f"Max: {max(all_ids)}")

# Check for 90001001 style IDs (without leading 09)
mc.execute("SELECT DISTINCT story_id_1 FROM story_event_story_data WHERE story_type_1 = 1 AND story_id_1 BETWEEN 90001000 AND 90099999")
ids_90 = sorted([row[0] for row in mc.fetchall()])
print(f"\nIDs in 90001000-90099999 range: {len(ids_90)}")
if ids_90:
    print(f"First 20: {ids_90[:20]}")

# These are the 09 prefix IDs (without leading 09 since they're stored as 9000xxxx)
# The meta path uses full 9-digit like 090001001
mconn.close()
