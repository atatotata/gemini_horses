#!/usr/bin/env python3
"""Try different PRAGMA key formats for the meta DB."""
import apsw

db = apsw.Connection(
    'C:/TMP/meta_fresh.bin',
    flags=apsw.SQLITE_OPEN_READONLY,
    vfs='multipleciphers-win32'
)

# The PRAGMA key with proper quoting
key_variants = [
    ('hex_bare_16', b'\x9c\x2b\xab\x97\xbd\xe7\xe9\xfd'),
    ('hex_bare_8', b'\x9c\x2b\xab\x97'),
    ('hex_bare_8_e9fd', b'\x9c\x2b\xab\x97\xe9\xfd'),
]

# Use parameterized PRAGMA doesn't work, use direct execute with proper SQL
# apsw PRAGMA key should be: PRAGMA key = "hex_value"
# But let's try setting the key as a passphrase via the VFS

for label, key_bytes in key_variants:
    try:
        # For multipleciphers VFS, use PRAGMA key with string
        key_hex = key_bytes.hex()
        sql = "PRAGMA key = '" + key_hex + "'"
        print(f"Trying: {label}: {sql}")
        db.execute(sql)
        tables = [r[0] for r in db.execute("SELECT name FROM sqlite_master WHERE type='table'")]
        if tables:
            print(f'  tables={tables}')
            count = db.execute("SELECT COUNT(*) FROM a").fetchone()[0]
            print(f'  COUNT(*) = {count}')
            break
        else:
            print(f'  no tables')
    except Exception as e:
        err = str(e)[:100]
        print(f'  ERROR: {err}')

db.close()

# Also try via URI hexkey with full bytes
print("\n--- URI hexkey approach ---")
for label, key_bytes in key_variants:
    key_hex = key_bytes.hex()
    try:
        uri = f'file:C:/TMP/meta_fresh.bin?hexkey={key_hex}'
        print(f"Trying: {label}: uri hexkey={key_hex}")
        db2 = apsw.Connection(uri, flags=apsw.SQLITE_OPEN_READONLY | apsw.SQLITE_OPEN_URI, vfs='multipleciphers-win32')
        count = db2.execute("SELECT COUNT(*) FROM a").fetchone()[0]
        print(f'  COUNT(*) = {count}')
        db2.close()
        break
    except Exception as e:
        err = str(e)[:100]
        print(f'  ERROR: {err}')
