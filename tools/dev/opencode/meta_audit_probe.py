import apsw

DB_BASE_KEY = b'\xF1\x70\xCE\xA4\xDF\xCE\xA3\xE1\xA5\xD8\xC7\x0B\xD1\x00\x00\x00'
DB_KEY = b'\x6D\x5B\x65\x33\x63\x36\x63\x25\x54\x71\x2D\x73\x50\x53\x63\x38\x6D\x34\x37\x7B\x35\x63\x70\x23\x37\x34\x53\x29\x73\x43\x36\x33'

key = bytearray(DB_KEY)
for i in range(len(key)):
    key[i] ^= DB_BASE_KEY[i % 13]
final = bytes(key)

# list supported ciphers
conn = apsw.Connection(':memory:')
try:
    cur = conn.cursor()
    rows = cur.execute("SELECT * FROM pragma_cipher_list").fetchall()
    print('supported ciphers:', [r[0] for r in rows])
except Exception as e:
    print('cipher list err:', e)

for path, label in [
    (r'C:\TMP\opencode\meta_copy', 'copy'),
    (r'G:\Games\steamapps\common\UmamusumePrettyDerby_Jpn\UmamusumePrettyDerby_Jpn_Data\Persistent\meta', 'live'),
]:
    try:
        c2 = apsw.Connection(path)
        c2.pragma('cipher', 'chacha20')
        c2.pragma('hexkey', final.hex())
        c = c2.cursor()
        n = c.execute('SELECT count(*) FROM a').fetchone()[0]
        print(f'[{label}] chacha20 OK, a count={n}')
        c2.close()
    except Exception as e:
        print(f'[{label}] FAIL {type(e).__name__}: {e}')
