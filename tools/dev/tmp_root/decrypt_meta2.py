#!/usr/bin/env python3
"""Derive meta DB key from baseKey XOR plainKey, then decrypt meta."""
import apsw

base_hex = "f170cea4dfcea3e1a5d8c70bd1"
plain_hex = "6d5b65336336632554712d73505363386d34377b356370233734532973433633"

base = bytes.fromhex(base_hex)
plain = bytes.fromhex(plain_hex)

final_key = bytes([plain[i] ^ base[i % len(base)] for i in range(len(plain))])
hexkey = final_key.hex()

print(f"base key ({len(base)} bytes): {base_hex}")
print(f"plain key ({len(plain)} bytes): {plain_hex}")
print(f"final key ({len(final_key)} bytes): {hexkey}")
print(f"hexkey prefix: {hexkey[:20]}...")

# Try opening with derived key
tmp = r'C:\TMP\meta_copy.bin'
uri = f'file:{tmp}?hexkey={hexkey}'

try:
    db = apsw.Connection(uri, flags=apsw.SQLITE_OPEN_READONLY | apsw.SQLITE_OPEN_URI)
    cur = db.cursor()
    count = cur.execute('SELECT COUNT(*) FROM a').fetchone()
    print(f"\nSUCCESS! Total meta rows: {count[0]}")
    db.close()
except apsw.NotADBError as e:
    print(f"\nNotADBError with derived key: {e}")
    # Try with PRAGMA key approach instead
    print("\nTrying PRAGMA approach...")
    try:
        db = apsw.Connection(tmp, flags=apsw.SQLITE_OPEN_READONLY)
        cur = db.cursor()
        cur.execute(f"PRAGMA key=\"x'{hexkey}'\"")
        count = cur.execute('SELECT COUNT(*) FROM a').fetchone()
        print(f"PRAGMA approach SUCCESS! Total meta rows: {count[0]}")
        db.close()
    except Exception as e2:
        print(f"PRAGMA approach also failed: {e2}")

# Also try the hachimi key with chacha20
print("\n--- Trying hachimi DB_KEY with chacha20 cipher ---")
hachimi_key = '9c2bab97bcf8c0c4f1a9ea7881a213f6c9ebf9d8d4c6a8e43ce5a259bde7e9fd'
try:
    db = apsw.Connection(tmp, flags=apsw.SQLITE_OPEN_READONLY)
    cur = db.cursor()
    cur.execute(f"PRAGMA cipher='chacha20'")
    cur.execute(f"PRAGMA key=\"x'{hachimi_key}'\"")
    count = cur.execute('SELECT COUNT(*) FROM a').fetchone()
    print(f"chacha20+hachimi SUCCESS! Total meta rows: {count[0]}")
    db.close()
except Exception as e3:
    print(f"chacha20+hachimi failed: {e3}")

# Try derived key with chacha20
print("\n--- Trying derived key with chacha20 cipher ---")
try:
    db = apsw.Connection(tmp, flags=apsw.SQLITE_OPEN_READONLY)
    cur = db.cursor()
    cur.execute(f"PRAGMA cipher='chacha20'")
    cur.execute(f"PRAGMA key=\"x'{hexkey}'\"")
    count = cur.execute('SELECT COUNT(*) FROM a').fetchone()
    print(f"chacha20+derived SUCCESS! Total meta rows: {count[0]}")
    db.close()
except Exception as e4:
    print(f"chacha20+derived failed: {e4}")

# Try derived key with URI hexkey= (apsw sqlite3mc style)
print("\n--- Trying derived key with URI hexkey (no cipher pragma) ---")
try:
    uri2 = f'file:{tmp}?hexkey={hexkey}'
    db = apsw.Connection(uri2, flags=apsw.SQLITE_OPEN_READONLY | apsw.SQLITE_OPEN_URI)
    cur = db.cursor()
    count = cur.execute('SELECT COUNT(*) FROM a').fetchone()
    print(f"URI hexkey SUCCESS! Total meta rows: {count[0]}")
    db.close()
except Exception as e5:
    print(f"URI hexkey failed: {e5}")
