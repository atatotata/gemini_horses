#!/usr/bin/env python3
"""Try different PRAGMA key formats for the meta DB."""
import apsw

db = apsw.Connection(
    'C:/TMP/meta_fresh.bin',
    flags=apsw.SQLITE_OPEN_READONLY,
    vfs='multipleciphers-win32'
)

keys = [
    ('hex_bare', 'x"9c2bab97bde7e9fd"'),
    ('hex_bare_e9fd', 'x"9c2bab97e9fd"'),
    ('hex_short', 'x"9c2bab97"'),
    ('text_dot1', '9c2bab97.bde7e9fd'),
    ('text_dot2', '9c2bab97.e9fd'),
    ('text_short', '9c2bab97'),
    ('hex_full_16byte', 'x"9c2bab97bde7e9fd0000000000000000"'),
    ('hex_maybe_rev', 'x"9ce9fd7e9db7ab97"'),
]

for label, key in keys:
    try:
        db.execute(f'PRAGMA key = {key}')
        # Try reading table names first
        tables = [r[0] for r in db.execute("SELECT name FROM sqlite_master WHERE type='table'")]
        if tables:
            print(f'{label}: tables={tables}')
            count = db.execute("SELECT COUNT(*) FROM a").fetchone()[0]
            print(f'  COUNT(*) = {count}')
            break
        else:
            print(f'{label}: no tables (maybe wrong key)')
    except Exception as e:
        err = str(e)[:80]
        print(f'{label}: ERROR: {err}')

db.close()
