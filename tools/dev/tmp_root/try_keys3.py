#!/usr/bin/env python3
"""Try even more key variants for the meta DB."""
import apsw

db = apsw.Connection(
    'C:/TMP/meta_fresh.bin',
    flags=apsw.SQLITE_OPEN_READONLY,
    vfs='multipleciphers-win32'
)

# Try PRAGMA key with different SQL string formats
key_sql_variants = [
    ("hex_nodot_concat", "PRAGMA key = X'9c2bab97bde7e9fd'"),
    ("hex_nodot_concat_e9fd", "PRAGMA key = X'9c2bab97e9fd'"),
    ("hex_nodot_short", "PRAGMA key = X'9c2bab97'"),
    ("str_dot1", "PRAGMA key = '9c2bab97.bde7e9fd'"),
    ("str_dot2", "PRAGMA key = '9c2bab97.e9fd'"),
    ("str_short", "PRAGMA key = '9c2bab97'"),
    ("hex_nodot_reversed", "PRAGMA key = X'9ce9fd7e9db7ab2c'"),
    ("hex_nodot_full_16", "PRAGMA key = X'9c2bab97bde7e9fd0000000000000000'"),
]

for label, sql in key_sql_variants:
    try:
        # Need fresh connection for each attempt
        db.close()
    except:
        pass
    try:
        db = apsw.Connection(
            'C:/TMP/meta_fresh.bin',
            flags=apsw.SQLITE_OPEN_READONLY,
            vfs='multipleciphers-win32'
        )
        db.execute(sql)
        # Try to read
        tables = [r[0] for r in db.execute("SELECT name FROM sqlite_master WHERE type='table'")]
        if tables:
            print(f'{label}: tables={tables}')
            if 'a' in tables:
                count = db.execute("SELECT COUNT(*) FROM a").fetchone()[0]
                print(f'  COUNT(*) = {count}')
            break
        else:
            # check page count
            try:
                pc = db.execute("PRAGMA page_count").fetchone()[0]
                print(f'{label}: no tables, page_count={pc}')
            except:
                print(f'{label}: no tables')
    except Exception as e:
        err = str(e)[:100]
        print(f'{label}: ERROR: {err}')

try:
    db.close()
except:
    pass

# Also try URI approach with different hex encodings
print("\n--- URI hexkey variants ---")
uri_variants = [
    ("concat_16", "9c2bab97bde7e9fd"),
    ("concat_8e9fd", "9c2bab97e9fd"),
    ("concat_8", "9c2bab97"),
    ("full_32", "9c2bab97bde7e9fd0000000000000000"),
    ("with_dots", "9c2bab97.bde7e9fd"),
    ("e9fd_only", "e9fd"),
]

for label, hexkey in uri_variants:
    try:
        uri = f'file:C:/TMP/meta_fresh.bin?hexkey={hexkey}'
        db = apsw.Connection(uri, flags=apsw.SQLITE_OPEN_READONLY | apsw.SQLITE_OPEN_URI, vfs='multipleciphers-win32')
        count = db.execute("SELECT COUNT(*) FROM a").fetchone()[0]
        print(f'{label}: COUNT(*) = {count}')
        db.close()
        break
    except Exception as e:
        err = str(e)[:100]
        print(f'{label}: ERROR: {err}')
