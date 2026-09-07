import sys, os, json, sqlite3
sys.path.insert(0, r'G:/Games/steamapps/common/UmamusumePrettyDerby_Jpn/gemini_horses/tools/umamusu-utils/scripts')
from utils import _derive_decryption_key, DB_KEY, DB_BASE_KEY, dict_factory
import apsw

conn = apsw.Connection(r'G:/Games/steamapps/common/UmamusumePrettyDerby_Jpn/UmamusumePrettyDerby_Jpn_Data/Persistent/meta')
conn.row_trace = dict_factory
final_key = _derive_decryption_key(DB_KEY, DB_BASE_KEY)
conn.pragma('cipher', 'chacha20')
conn.pragma('hexkey', final_key.hex())
c = conn.cursor()

c.execute("SELECT DISTINCT m FROM a WHERE m LIKE '%story%'")
print("m distinct:", [r['m'] for r in c.fetchall()])

# Query using indexed prefix comparison
c.execute("SELECT count(1) as cnt FROM a WHERE n >= 'story/data/' AND n < 'story/data0'")
print("story/data count:", c.fetchone()['cnt'])

# Sample entries
c.execute("SELECT n, h, e, m FROM a WHERE n >= 'story/data/' AND n < 'story/data0' LIMIT 10")
for r in c.fetchall():
    print(r['n'], r['h'], r['m'])
