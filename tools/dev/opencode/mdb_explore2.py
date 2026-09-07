import sqlite3, json, os, sys
sys.stdout.reconfigure(encoding='utf-8', errors='replace')

DB = r'G:\Games\steamapps\common\UmamusumePrettyDerby_Jpn\UmamusumePrettyDerby_Jpn_Data\Persistent\master\master.mdb'
DICT = r'G:\Games\steamapps\common\UmamusumePrettyDerby_Jpn\gemini_horses\localized_data\text_data_dict.json'

con = sqlite3.connect(DB)
cur = con.cursor()

# table name list
tbls = [r[0] for r in cur.execute("SELECT name FROM sqlite_master WHERE type='table' AND name NOT LIKE 'sqlite_%' ORDER BY name")]
print('USER TABLES:', len(tbls))

# text_data categories present in master
cats = [r[0] for r in cur.execute('SELECT DISTINCT category FROM text_data ORDER BY category')]
print('text_data distinct categories in master:', len(cats))
print('category range/min/max:', min(cats), max(cats))

with open(DICT, 'r', encoding='utf-8') as f:
    d = json.load(f)
print('dict top-level type:', type(d).__name__)
if isinstance(d, dict):
    ks = list(d.keys())[:30]
    print('dict top keys sample:', ks)
    print('num top keys:', len(d))
    first_k = list(d.keys())[0]
    v = d[first_k]
    print('first key repr:', repr(first_k), 'val type:', type(v).__name__)
    if isinstance(v, dict):
        vk = list(v.keys())[:10]
        print('inner keys sample:', vk)
        vv = v[list(v.keys())[0]]
        print('inner val type:', type(vv).__name__, 'sample:', repr(vv)[:300])
    else:
        print('inner sample:', repr(v)[:300])
con.close()
