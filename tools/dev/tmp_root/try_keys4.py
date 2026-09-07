#!/usr/bin/env python3
"""Probe cipher settings and try key derivation options."""
import apsw

# The header is not standard SQLite, so it IS encrypted.
# Let's try various cipher compat levels and key settings

key_candidates = [
    '9c2bab97.bde7e9fd',
    '9c2bab97.e9fd',
    '9c2bab97',
]

cipher_settings = [
    # (label, setup_sql_list)
    ("compat_default", []),
    ("compat_1", ["PRAGMA cipher_compatibility = 1"]),
    ("compat_2", ["PRAGMA cipher_compatibility = 2"]),
    ("compat_3", ["PRAGMA cipher_compatibility = 3"]),
    ("compat_4", ["PRAGMA cipher_compatibility = 4"]),
    ("compat_default_32k", ["PRAGMA cipher_page_size = 32768"]),
    ("compat_default_wal", ["PRAGMA cipher_use_hmac = OFF"]),
]

for s_label, setup_sqls in cipher_settings:
    for k in key_candidates:
        try:
            db = apsw.Connection(
                'C:/TMP/meta_fresh.bin',
                flags=apsw.SQLITE_OPEN_READONLY,
                vfs='multipleciphers-win32'
            )
            for s in setup_sqls:
                try:
                    db.execute(s)
                except:
                    pass
            # Set key
            db.execute(f"PRAGMA key = '{k}'")
            # Check if we can read
            try:
                tables = [r[0] for r in db.execute("SELECT name FROM sqlite_master WHERE type='table'")]
                if tables:
                    print(f'{s_label} + key={k}: tables={tables[:5]}')
                    if 'a' in tables:
                        count = db.execute("SELECT COUNT(*) FROM a").fetchone()[0]
                        print(f'  SUCCESS! COUNT(*) = {count}')
                        db.close()
                        exit(0)
                else:
                    pc = db.execute("PRAGMA page_count").fetchone()[0]
                    if pc > 0:
                        print(f'{s_label} + key={k}: no tables but page_count={pc} (wrong key?)')
            except Exception as e2:
                pass
            db.close()
        except Exception as e:
            err = str(e)[:80]
            # Only print if not the usual "not a database"
            if "not a database" not in err:
                print(f'{s_label} + key={k}: {err}')

print("\nNo combination worked. Trying raw PRAGMA cipher settings...")
# Try explicit cipher settings that SQLCipher v4 uses
for k in key_candidates:
    try:
        db = apsw.Connection(
            'C:/TMP/meta_fresh.bin',
            flags=apsw.SQLITE_OPEN_READONLY,
            vfs='multipleciphers-win32'
        )
        # Standard SQLCipher v4 settings
        db.execute("PRAGMA cipher_compatibility = 4")
        db.execute("PRAGMA kdf_iter = 256000")
        db.execute(f"PRAGMA key = '{k}'")
        tables = [r[0] for r in db.execute("SELECT name FROM sqlite_master WHERE type='table'")]
        if tables:
            print(f'SQLCipher v4 + key={k}: tables={tables[:5]}')
            if 'a' in tables:
                count = db.execute("SELECT COUNT(*) FROM a").fetchone()[0]
                print(f'  SUCCESS! COUNT(*) = {count}')
        else:
            pc = db.execute("PRAGMA page_count").fetchone()[0]
            print(f'SQLCipher v4 + key={k}: no tables, page_count={pc}')
        db.close()
    except Exception as e:
        err = str(e)[:100]
        if "not a database" not in err:
            print(f'SQLCipher v4 + key={k}: {err}')

print("\nTrying plain sqlite3 (maybe file is not encrypted or re-encrypted)...")
import sqlite3
for k in key_candidates:
    try:
        conn = sqlite3.connect(f'file:C:/TMP/meta_fresh.bin?mode=ro&uri=1')
        conn.execute(f"PRAGMA key = '{k}'")
        tables = [r[0] for r in conn.execute("SELECT name FROM sqlite_master WHERE type='table'")]
        if tables:
            print(f'sqlite3 + key={k}: tables={tables[:5]}')
        conn.close()
    except Exception as e:
        pass

# Try reading the file without any key - maybe it was decrypted
print("\nTrying plain read (no encryption)...")
try:
    conn = sqlite3.connect('C:/TMP/meta_fresh.bin', uri=True)
    tables = [r[0] for r in conn.execute("SELECT name FROM sqlite_master WHERE type='table'")]
    if tables:
        print(f'Plain: tables={tables[:5]}')
    else:
        print('Plain: no tables')
    conn.close()
except Exception as e:
    err = str(e)[:100]
    print(f'Plain: {err}')
