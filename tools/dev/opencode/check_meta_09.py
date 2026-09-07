import sys
sys.path.insert(0, r'G:\Games\steamapps\common\UmamusumePrettyDerby_Jpn\gemini_horses\tools\umamusu-utils\scripts')
from utils import _derive_decryption_key, DB_KEY, DB_BASE_KEY, dict_factory
import apsw

META_PATH = r'G:\Games\steamapps\common\UmamusumePrettyDerby_Jpn\UmamusumePrettyDerby_Jpn_Data\Persistent\meta'
conn = apsw.Connection(META_PATH)
conn.row_trace = dict_factory
final_key = _derive_decryption_key(DB_KEY, DB_BASE_KEY)
conn.pragma('cipher', 'chacha20')
conn.pragma('hexkey', final_key.hex())
c = conn.cursor()

# Use COUNT for speed
r1 = list(c.execute("SELECT COUNT(*) as cnt FROM a WHERE n LIKE 'story/data/09/%storytimeline_%' AND n NOT LIKE '%resourcelist%'"))
print(f"Meta 09 storytimeline entries: {r1[0]['cnt']}", flush=True)

r2 = list(c.execute("SELECT COUNT(*) as cnt FROM a WHERE n LIKE 'story/data/%storytimeline_%' AND n NOT LIKE '%resourcelist%'"))
print(f"Meta total storytimeline entries: {r2[0]['cnt']}", flush=True)

# Get all 09 entries with h,e
entries = []
for row in c.execute("SELECT n, h, e FROM a WHERE n LIKE 'story/data/09/%storytimeline_%' AND n NOT LIKE '%resourcelist%'"):
    entries.append(row)
print(f"Collected {len(entries)} entries", flush=True)

# Show a few samples
for e in entries[:3]:
    print(e, flush=True)
    
# Extract sids from paths
sids = set()
for e in entries:
    n = e['n']
    sid_str = n.split('_')[-1]
    try:
        sids.add(int(sid_str))
    except ValueError:
        pass
print(f"Unique 09 sids in meta: {len(sids)}", flush=True)
print(f"Min: {min(sids)}, Max: {max(sids)}", flush=True)

conn.close()
