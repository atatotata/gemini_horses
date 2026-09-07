import sqlite3, json, os, sys, re

DB = r'G:/Games/steamapps/common/UmamusumePrettyDerby_Jpn/UmamusumePrettyDerby_Jpn_Data/Persistent/master/master.mdb'
LD = r'G:/Games/steamapps/common/UmamusumePrettyDerby_Jpn/gemini_horses/localized_data'

con = sqlite3.connect(DB)
cur = con.cursor()

# Stage 0: keyword tables with row counts
cur.execute("SELECT name FROM sqlite_master WHERE type='table'")
tables = sorted(r[0] for r in cur.fetchall())
kw = ['jikkyo', 'live', 'race', 'comment']
kwtables = [t for t in tables if any(k in t for k in kw)]

print("=== KEYWORD TABLES ===")
for t in kwtables:
    try:
        cur.execute(f'SELECT COUNT(*) FROM "{t}"')
        c = cur.fetchone()[0]
        cols = [r[1] for r in cur.execute(f'PRAGMA table_info("{t}")')]
        print(f"{t}\trows={c}\tcols={len(cols)}")

        # detect a text-ish column that could hold JP strings
        # dump schema types
        types = {r[1]: r[2] for r in cur.execute(f'PRAGMA table_info("{t}")')}
        # find value-ish columns
        valcols = [c for c in types if types[c].lower() in ('text',) or c in ('text','name','value','data','message','jikkyo_message','comment','announce','win_comment','color','content')]
        # count non-numeric values in the first text col
        for vc in valcols[:1]:
            try:
                cur.execute(f'SELECT COUNT(*) FROM "{t}" WHERE "{vc}" IS NOT NULL AND "{vc}" != ""')
                nn = cur.fetchone()[0]
                cur.execute(f'SELECT COUNT(*) FROM "{t}" WHERE "{vc}" GLOB "*[ぁ-んァ-ヶ一-龠]*"')
                jp = cur.fetchone()[0]
                if nn or jp:
                    print(f"   textcol={vc} nonnull={nn} has_jp_chars={jp}")
            except Exception as e:
                pass
    except Exception as e:
        print(f"{t}\tERR {e}")

print()
print("=== FOCUS TABLES schema + counts ===")
focus = ['race_jikkyo_message','race_jikkyo_message_window','race_jikkyo_phase_condition','race_comment_group','race_jikkyo_comment']
for t in focus:
    if t not in tables:
        print(f"{t}\tMISSING IN DB")
        continue
    cur.execute(f'SELECT COUNT(*) FROM "{t}"')
    c = cur.fetchone()[0]
    print(f"\n[{t}] rows={c}")
    for r in cur.execute(f'PRAGMA table_info("{t}")'):
        print(f"   {r[1]} {r[2]}")
    # sample row
    try:
        cols = [d[1] for d in cur.execute(f'PRAGMA table_info("{t}")')]
        print("   sample:", cur.execute(f'SELECT * FROM "{t}" LIMIT 2').fetchall())
    except Exception as e:
        print("   sample ERR", e)

print()
print("=== LOCALIZED DICT FILES ===")
for f in ['race_jikkyo_message_dict.json','race_jikkyo_comment_dict.json']:
    p = os.path.join(LD, f)
    if not os.path.exists(p):
        print(f, "MISSING")
        continue
    d = json.load(open(p, encoding='utf-8'))
    print(f"\n[{f}] type={type(d).__name__} len={len(d)}")
    items = list(d.items())[:5] if isinstance(d, dict) else d[:5]
    for it in items:
        s = str(it)
        print("   ", s[:300])
