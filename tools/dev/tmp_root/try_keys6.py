#!/usr/bin/env python3
"""Try cipher_ pragmas with multipleciphers VFS - look at what works."""
import apsw

db = apsw.Connection(
    'C:/TMP/meta_fresh.bin',
    flags=apsw.SQLITE_OPEN_READONLY,
    vfs='multipleciphers-win32'
)

# Try setting key directly
try:
    db.execute("PRAGMA key = '9c2bab97.bde7e9fd'")
    print("PRAGMA key set OK")
except Exception as e:
    print(f"PRAGMA key error: {e}")

# Check what PRAGMAs are available
print("\n--- All PRAGMA keywords ---")
try:
    # Try getting all PRAGMA options via a special query
    all_pragmas = db.execute("PRAGMA pragma_list").fetchall()
    for row in all_pragmas:
        name = row[0]
        if 'cipher' in name.lower() or 'key' in name.lower() or 'kdf' in name.lower() or 'hmac' in name.lower():
            print(f"  {name}")
except Exception as e:
    print(f"pragma_list error: {e}")

# Try cipher_ pragmas specifically
print("\n--- cipher_ pragmas ---")
cipher_pragmas = [
    'cipher_compatibility',
    'cipher_default_compatibility',
    'cipher_page_size',
    'cipher_use_hmac',
    'cipher_hmac_algorithm', 
    'cipher_kdf_algorithm',
    'cipher_default_kdf_iter',
    'cipher_salt',
    'cipher_iter',
    'cipher_memory_security',
    'cipher_plaintext_header_size',
    'cipher_plaintext_page_size',
    'cipher_profile',
    'cipher_FIPS',
    'cipher_verbose',
    'cipher_provider',
    'cipher_migrate',
    'cipher_add_random',
    'cipher_triad_size',
    'cipher_hmac_salt_use',
]
for p in cipher_pragmas:
    try:
        r = db.execute(f"PRAGMA {p}").fetchone()
        val = r[0] if r else "NULL"
        print(f"  {p}: {val}")
    except Exception as e:
        err = str(e)[:80]
        if "not authorized" not in err:
            print(f"  {p}: ERROR: {err}")
        else:
            print(f"  {p}: NOT AUTHORIZED")

db.close()
