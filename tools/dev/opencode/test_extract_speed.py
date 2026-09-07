import os, sys, time, json, sqlite3
from pathlib import Path
from concurrent.futures import ProcessPoolExecutor, ThreadPoolExecutor

GAME_DIR = Path(r"G:/Games/steamapps/common/UmamusumePrettyDerby_Jpn")
DAT_DIR = GAME_DIR / "UmamusumePrettyDerby_Jpn_Data/Persistent/dat"
META_PATH = GAME_DIR / "UmamusumePrettyDerby_Jpn_Data/Persistent/meta"
MASTER_PATH = GAME_DIR / "UmamusumePrettyDerby_Jpn_Data/Persistent/master/master.mdb"

sys.path.insert(0, str(GAME_DIR / "gemini_horses/tools/umamusu-utils/scripts"))
from utils import _derive_decryption_key, _derive_asset_key, DB_KEY, DB_BASE_KEY, dict_factory
import apsw, UnityPy

# 1. Load missing Flag 1 (Horsegirls) story IDs
mconn = sqlite3.connect(str(MASTER_PATH))
mc = mconn.cursor()
mc.execute("SELECT DISTINCT story_id FROM single_mode_story_data WHERE gallery_flag = 1 AND story_id != 0")
all_flag1 = set(r[0] for r in mc.fetchall())
mconn.close()

# Existing
existing = set()
for root, dirs, files in os.walk(GAME_DIR / "gemini_horses/localized_data/assets/story/data/50"):
    for f in files:
        if f.startswith('storytimeline_') and f.endswith('.json'):
            sid = int(f.replace('storytimeline_', '').replace('.json', ''))
            existing.add(sid)

missing = sorted(list(all_flag1 - existing))
print(f"Total missing: {len(missing)}")

# 2. Query meta for first 50
sample_missing = missing[:50]
conn = apsw.Connection(str(META_PATH))
conn.row_trace = dict_factory
final_key = _derive_decryption_key(DB_KEY, DB_BASE_KEY)
conn.pragma('cipher', 'chacha20')
conn.pragma('hexkey', final_key.hex())
c = conn.cursor()

resolved = {}
for sid in sample_missing:
    row = next(c.execute("SELECT n, h, e, m FROM a WHERE n >= ? AND n < ?", (f"story/data/50/{str(sid)[2:6]}/storytimeline_{sid}", f"story/data/50/{str(sid)[2:6]}/storytimeline_{sid}0")), None)
    if not row:
        row = next(c.execute("SELECT n, h, e, m FROM a WHERE n LIKE ?", (f"%storytimeline_{sid}",)), None)
    if row:
        resolved[sid] = row
conn.close()

print(f"Resolved {len(resolved)} / 50 sample sids")

# Test extraction timing on 50 files
t0 = time.time()
extracted_count = 0
total_blocks = 0

for sid, meta_info in resolved.items():
    h = meta_info['h']
    e = meta_info['e']
    bundle_path = DAT_DIR / h[:2] / h
    if not bundle_path.exists():
        continue
    
    with open(bundle_path, 'rb') as f:
        data = bytearray(f.read())
    
    dec_key = _derive_asset_key(e)
    if dec_key and len(data) > 256:
        klen = len(dec_key)
        for j in range(256, len(data)):
            data[j] ^= dec_key[j % klen]
    
    env = UnityPy.load(bytes(data))
    story_data_obj = None
    clip_objects = {}
    
    for obj in env.objects:
        if obj.type.name == "MonoBehaviour":
            try:
                tree = obj.read_typetree()
                if "BlockList" in tree:
                    story_data_obj = tree
                elif "Text" in tree and "ChoiceDataList" in tree:
                    clip_objects[obj.path_id] = tree
            except Exception:
                pass
    
    if story_data_obj:
        extracted_count += 1
        block_list = story_data_obj.get('BlockList', [])
        for blk in block_list[1:]:
            tt = blk.get('TextTrack', {})
            clips = tt.get('ClipList', [])
            total_blocks += 1

dt = time.time() - t0
print(f"Extracted {extracted_count} bundles in {dt:.2f}s ({extracted_count/dt:.1f} bundles/sec)")
print(f"Total blocks in 50 stories: {total_blocks} (avg {total_blocks/extracted_count:.1f} blocks/story)")
