import apsw
KEY = "9c2bab97bcf8c0c4f1a9ea7881a213f6c9ebf9d8d4c6a8e43ce5a259bde7e9fd"
path = r'C:\TMP\meta_fresh.bin'
conn = apsw.Connection(f'file:{path}?hexkey={KEY}', flags=apsw.SQLITE_OPEN_READONLY | apsw.SQLITE_OPEN_URI)
cur = conn.cursor()

for label, like in [
    ("storyrace anywhere", "%storyrace%"),
    ("live top", "live/%"),
    ("exact storytimeline 4-part", None),
]:
    rows = cur.execute("SELECT n FROM a WHERE n LIKE ?", (like,)).fetchall()
    print(f"\n[{label}] LIKE {like}: {len(rows)} rows")
    from collections import Counter
    c = Counter()
    for (n,) in rows[:200000]:
        c[n.split('/')[0]] += 1
    print("  by top:", dict(sorted(c.items())))

# exact storytimeline (4 parts, no resources)
rows = cur.execute("SELECT n FROM a WHERE n LIKE 'story/data/%/%'").fetchall()
plain = [n for (n,) in rows if n.count('/')==3 and n.split('/')[3].startswith('storytimeline_') and not n.endswith('_resources')]
res   = [n for (n,) in rows if n.count('/')==4 and '_resources' in n]
print("\nexact 4-part storytimeline plain:", len(plain))
c = Counter(n.split('/')[2] for n in plain)
print("  by prefix:", dict(sorted(c.items())))
print("4-part resources count:", len(res))
# ast variants under story/data
ast = [n for (n,) in rows if 'ast_' in n and n.count('/')==4]
print("story ast_* variants:", len(ast))

# home/data
rows = cur.execute("SELECT n FROM a WHERE n LIKE 'home/data/%'").fetchall()
hs = [n for (n,) in rows]
plain_h = [n for n in hs if n.count('/')==4 and n.split('/')[3].startswith('hometimeline_') and not n.startswith('home/data/00000/01/ast')]
ast_h = [n for n in hs if '/ast_' in n]
print("\nhome/data rows:", len(hs))
print("  plain hometimeline_* (4-part):", len(plain_h))
print("  ast_* variants:", len(ast_h))
c2 = Counter()
for n in plain_h:
    p = n.split('/')
    c2[(p[2], p[3][:len('hometimeline_00000_01_')])] += 1
print("  sample plain:", plain_h[:3])
# distinct hometimeline ids
ids = set()
for n in plain_h:
    ids.add(n.split('/')[3])
print("  distinct hometimeline basenames:", len(ids))
# ast set too
astids = set()
for n in ast_h:
    b = n.split('/')[3]
    astids.add(b)
print("  ast distinct basenames:", len(astids))

# lyrics live
rows = cur.execute("SELECT n FROM a WHERE n LIKE 'live/%lyrics%'").fetchall()
print("\nlive lyrics rows:", len(rows))
for (n,) in rows[:10]:
    print("   ", n)
rows2 = cur.execute("SELECT n FROM a WHERE n LIKE 'live/musicscores/%/lyrics%'").fetchall()
print("musicscores .../lyrics:", len(rows2))
