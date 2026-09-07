import sqlite3
import json

MDB = r"G:/Games/steamapps/common/UmamusumePrettyDerby_Jpn/UmamusumePrettyDerby_Jpn_Data/Persistent/master/master.mdb"
conn = sqlite3.connect(f"file:{MDB}?mode=ro", uri=True)
c = conn.cursor()

# Get all message text for missing ids and write to file for examination
c.execute('SELECT "id", "message" FROM "race_jikkyo_message" WHERE "id" = 25')
row = c.fetchone()
msg = row[1]

# Write raw repr to file
with open(r"C:/TMP/race_jikkyo/encoding_debug.txt", "w", encoding="utf-8") as f:
    f.write(f"ID 25 raw repr: {repr(msg)}\n")
    f.write(f"ID 25 len: {len(msg)}\n")
    
    # Check if it's actually valid UTF-8 that just can't display in console
    # Try encoding as various things
    for enc in ['utf-8', 'cp932', 'shift_jis', 'euc_jp']:
        try:
            raw = msg.encode(enc, errors='replace')
            f.write(f"{enc} encode: {raw[:100].hex()}\n")
        except Exception as e:
            f.write(f"{enc} encode error: {e}\n")
    
    # Try reading the raw bytes from the file directly
    f.write(f"\nOrdinals of first 60 chars:\n")
    for i, ch in enumerate(msg[:60]):
        f.write(f"  [{i}] U+{ord(ch):04X} ({ch})\n")
    
    # The key insight: if this is Shift-JIS stored in SQLite and Python reads it as UTF-8
    # with replacement chars, the info is lost. Let's check if the bytes in the 
    # filesystem are accessible differently.
    
    # Actually let's try: maybe it IS UTF-8, just the console can't display it
    f.write(f"\nAttempting UTF-8 decode test:\n")
    try:
        raw_utf8 = msg.encode('utf-8', errors='surrogateescape')
        f.write(f"UTF-8 bytes: {raw_utf8[:200].hex()}\n")
    except Exception as e:
        f.write(f"Error: {e}\n")

# Also get the id=1 sample for comparison
c.execute('SELECT "id", "message" FROM "race_jikkyo_message" WHERE "id" = 1')
row1 = c.fetchone()
msg1 = row1[1]

# And the comment id=3050
c.execute('SELECT "id", "message" FROM "race_jikkyo_comment" WHERE "id" = 3050')
row_c = c.fetchone()
msg_c = row_c[1]

with open(r"C:/TMP/race_jikkyo/encoding_debug2.txt", "w", encoding="utf-8") as f:
    f.write(f"MSG 1: {repr(msg1)}\n")
    f.write(f"MSG 25: {repr(msg)}\n")
    f.write(f"CMT 3050: {repr(msg_c)}\n")
    f.write(f"\nMSG 1 ordinals:\n")
    for i, ch in enumerate(msg1[:60]):
        f.write(f"  [{i}] U+{ord(ch):04X}\n")
    f.write(f"\nMSG 25 ordinals:\n")
    for i, ch in enumerate(msg[:60]):
        f.write(f"  [{i}] U+{ord(ch):04X}\n")

conn.close()
