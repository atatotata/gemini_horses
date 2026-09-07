#!/usr/bin/env python3
"""Check cipher defaults and try key with PRAGMA cipher settings before key."""
import apsw

# First check cipher defaults on in-memory db
db0 = apsw.Connection(':memory:', vfs='multipleciphers-win32')
pragmas_check = [
    'PRAGMA cipher_compatibility',
    'PRAGMA cipher_page_size',
    'PRAGMA cipher_use_hmac',
    'PRAGMA cipher_hmac_algorithm',
    'PRAGMA cipher_kdf_algorithm',
    'PRAGMA cipher_default_plaintext_header_size',
    'PRAGMA cipher_default_page_size',
    'PRAGMA cipher_default_iter',
    'PRAGMA cipher_default_kdf_iter',
]
print("=== Cipher defaults (memory db) ===")
for p in pragmas_check:
    try:
        r = db0.execute(p).fetchone()
        print(f'  {p}: {r[0] if r else "no result"}')
    except Exception as e:
        print(f'  {p}: {str(e)[:80]}')
db0.close()

# Now try the meta with cipher settings BEFORE setting key
print("\n=== Trying cipher settings before key ===")
settings_sets = [
    ("defaults", []),
    ("compat3", ["PRAGMA cipher_compatibility = 3"]),
    ("compat4", ["PRAGMA cipher_compatibility = 4"]),
    ("iter4000", ["PRAGMA cipher_kdf_iter = 4000"]),
    ("iter256k", ["PRAGMA cipher_kdf_iter = 256000"]),
    ("nohmac", ["PRAGMA cipher_use_hmac = OFF"]),
    ("pt_header8", ["PRAGMA cipher_plaintext_header_size = 8"]),
    ("pt_header16", ["PRAGMA cipher_plaintext_header_size = 16"]),
    ("pt_header32", ["PRAGMA cipher_plaintext_header_size = 32"]),
    ("pt_header4096", ["PRAGMA cipher_plaintext_header_size = 4096"]),
    ("compat3_noiter", ["PRAGMA cipher_compatibility = 3", "PRAGMA cipher_kdf_iter = 4000"]),
    ("compat3_noiter_nohmac", ["PRAGMA cipher_compatibility = 3", "PRAGMA cipher_kdf_iter = 4000", "PRAGMA cipher_use_hmac = OFF"]),
    ("pt32_compat4", ["PRAGMA cipher_plaintext_header_size = 32", "PRAGMA cipher_compatibility = 4"]),
]

key_candidates = [
    '9c2bab97.bde7e9fd',
    '9c2bab97.e9fd',
    '9c2bab97',
]

found = False
for s_label, setup_sqls in settings_sets:
    for k in key_candidates:
        if found:
            break
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
            db.execute(f"PRAGMA key = '{k}'")
            try:
                tables = [r[0] for r in db.execute("SELECT name FROM sqlite_master WHERE type='table'")]
                if tables:
                    print(f'  FOUND: {s_label} + key={k}: tables={tables[:5]}')
                    if 'a' in tables:
                        count = db.execute("SELECT COUNT(*) FROM a").fetchone()[0]
                        print(f'  COUNT(*) = {count}')
                    found = True
                else:
                    pc = db.execute("PRAGMA page_count").fetchone()[0]
                    if pc > 0 and pc != 1:
                        print(f'  {s_label} + key={k}: page_count={pc} (close?)')
            except Exception as e2:
                err = str(e2)[:80]
                if "not a database" not in err:
                    print(f'  {s_label} + key={k}: {err}')
            db.close()
        except Exception as e:
            pass
    if found:
        break

if not found:
    print("No combination worked.")
    
    # Last resort: check if the file might have been decrypted already
    # or if it's some other format
    import struct
    with open('C:/TMP/meta_fresh.bin', 'rb') as f:
        header = f.read(100)
    print(f"\nFile header (hex): {header[:32].hex()}")
    print(f"File size: {__import__('os').path.getsize('C:/TMP/meta_fresh.bin'):,}")
    
    # Check if maybe it's a different size (was it copied correctly?)
    src = 'G:/Games/steamapps/common/UmamusumePrettyDerby_Jpn/UmamusumePrettyDerby_Jpn_Data/Persistent/meta'
    if __import__('os').path.exists(src):
        src_size = __import__('os').path.getsize(src)
        print(f"Source meta size: {src_size:,}")
        print(f"Fresh copy size:  {__import__('os').path.getsize('C:/TMP/meta_fresh.bin'):,}")
        print(f"Match: {src_size == __import__('os').path.getsize('C:/TMP/meta_fresh.bin')}")
