import apsw
from collections import Counter
KEY = "9c2bab97bcf8c0c4f1a9ea7881a213f6c9ebf9d8d4c6a8e43ce5a259bde7e9fd"
path = r'C:\TMP\meta_fresh.bin'
conn = apsw.Connection(f'file:{path}?hexkey={KEY}', flags=apsw.SQLITE_OPEN_READONLY | apsw.SQLITE_OPEN_URI)
cur = conn.cursor()

rows = cur.execute("SELECT n FROM a WHERE n LIKE '%storyrace%'").fetchall()
print("== storyrace rows by top/next ==")
c = Counter()
for (n,) in rows:
    p = n.split('/')
    key = '/'.join(p[:3]) if len(p) >= 3 else n
    c[key] += 1
for k, v in sorted(c.items()):
    print(v, k)
print("\n== samples under top 'race' ==")
for (n,) in rows:
    if n.startswith('race/'):
        print("  ", n)

print("\n== home/data classification ==")
rows = cur.execute("SELECT n FROM a WHERE n LIKE 'home/data/%'").fetchall()
cnt = Counter()
plain_ids = set()
for (n,) in rows:
    p = n.split('/')
    if len(p) == 5:
        f = p[4]
        if f.startswith('ast_dot_') or f.startswith('ast_ruby_'):
            cnt['ast_var'] += 1
        elif f.startswith('hometimeline_'):
            cnt['plain'] += 1
            plain_ids.add(f)
        else:
            cnt['other'] += 1
            if cnt['other'] <= 5: print("  other sample:", n)
    else:
        cnt[f'depth_{len(p)}'] += 1
print("home/data:", dict(cnt), "distinct plain basenames:", len(plain_ids))

print("\n== story/data classification ==")
rows = cur.execute("SELECT n FROM a WHERE n LIKE 'story/data/%'").fetchall()
cnt = Counter()
plain = []
res = 0
ast = Counter()
for (n,) in rows:
    p = n.split('/')
    if len(p) == 5:
        f = p[4]
        if f.startswith('storytimeline_'):
            plain.append((p[2], f))
            cnt['plain'] += 1
        elif f.startswith('ast_dot_') or f.startswith('ast_ruby_'):
            ast[f.split('_')[0] + '_' + p[2]] += 1
            cnt['ast_var'] += 1
        else:
            cnt['other'] += 1
    elif len(p) == 6 and p[4] == 'resourcelist':
        res += 1
    else:
        cnt[f'depth_{len(p)}'] += 1
print("story/data:", dict(cnt))
print("  resources rows:", res)
print("  ast_var by type+prefix:", dict(ast))
# plain story prefix counts
pc = Counter(x[0] for x in plain)
print("  plain storytimeline by prefix:", dict(sorted(pc.items())), "sum", len(plain))
