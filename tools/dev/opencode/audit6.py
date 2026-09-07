import sqlite3, json, re
DB=r'G:\Games\steamapps\common\UmamusumePrettyDerby_Jpn\UmamusumePrettyDerby_Jpn_Data\Persistent\master\master.mdb'
con=sqlite3.connect(DB); con.text_factory=lambda b: b.decode('utf-8','replace'); cur=con.cursor()
print('table count:', cur.execute("SELECT COUNT(*) FROM sqlite_master WHERE type='table'").fetchone()[0])
print('distinct character_id in character_system_text:', cur.execute('SELECT COUNT(DISTINCT character_id) FROM character_system_text').fetchone()[0])

for t,c in [('race_jikkyo_comment','voice'),('race_jikkyo_message','voice'),
            ('character_system_text','cue_sheet'),('character_system_text','lip_sync_data'),
            ('character_system_text','text')]:
    n=cur.execute(f'SELECT COUNT(*) FROM "{t}" WHERE "{c}" IS NOT NULL AND "{c}"!=""').fetchone()[0]
    print(f'{t}.{c} nonempty: {n}')

# race_jikkyo_message: are missing ids a contiguous block? summarize coverage
rjm=json.load(open(r'G:\Games\steamapps\common\UmamusumePrettyDerby_Jpn\gemini_horses\localized_data\race_jikkyo_message_dict.json',encoding='utf-8'))
ids=[r[0] for r in cur.execute('SELECT id FROM race_jikkyo_message')]
covered=[i for i in ids if str(i) in rjm]
missing=[i for i in ids if str(i) not in rjm]
print('rjm: ids',len(ids),'covered',len(covered),'missing',len(missing))
print('rjm missing min/max:', min(missing), max(missing))
# block analysis
s=sorted(missing); blocks=[]; start=prev=s[0]
for x in s[1:]:
    if x!=prev+1: blocks.append((start,prev)); start=x
    prev=x
blocks.append((start,prev))
print('rjm missing blocks (first 10):', blocks[:10])
print('rjm covered ids: covered[:30] =', sorted(covered)[:30])

rjc=json.load(open(r'G:\Games\steamapps\common\UmamusumePrettyDerby_Jpn\gemini_horses\localized_data\race_jikkyo_comment_dict.json',encoding='utf-8'))
ids=[r[0] for r in cur.execute('SELECT id FROM race_jikkyo_comment')]
missing=[i for i in ids if str(i) not in rjc]
s=sorted(missing); blocks=[]; start=prev=s[0]
for x in s[1:]:
    if x!=prev+1: blocks.append((start,prev)); start=x
    prev=x
blocks.append((start,prev))
print('rjc missing blocks:', blocks)
print('rjc dict keys sample:', sorted(int(k) for k in rjc if k.isdigit())[:20])