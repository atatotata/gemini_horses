import json, os, time, glob
ckpt = "C:/TMP/opencode/supp_fetch/supp_story_checkpoint.json"
with open(ckpt, 'r', encoding='utf-8') as f:
    d = json.load(f)
print(f"Entries: {len(d)}")
print(f"Size: {os.path.getsize(ckpt)/1024/1024:.2f} MB")
print(f"Mtime: {time.ctime(os.path.getmtime(ckpt))}")
# show last entry
if d:
    print(f"Last entry id: {d[-1].get('id','?')[:120]}")
    # count by file
    from collections import Counter
    files = Counter(x['rel_path'] for x in d)
    print(f"Files covered: {len(files)}")
# backup
old = ckpt + ".old"
if os.path.exists(old):
    with open(old,'r',encoding='utf-8') as f:
        d2=json.load(f)
    print(f"Old backup entries: {len(d2)}")
# logs
for p in ["C:/TMP/opencode/supp_fetch/translate.log","C:/TMP/opencode/supp_fetch/translate.err.log"]:
    if os.path.exists(p):
        print(f"{p}: {os.path.getsize(p)} bytes, mtime {time.ctime(os.path.getmtime(p))}")
        with open(p,'r',encoding='utf-8',errors='replace') as f:
            lines=f.readlines()
            print("--- tail 30 ---")
            for l in lines[-30:]:
                print(l.rstrip()[:300])
