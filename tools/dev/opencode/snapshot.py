import sqlite3
conn = sqlite3.connect(r'C:\Users\Ota\.omniroute\storage.sqlite')
cur = conn.cursor()
keys_db = ['semanticCacheTTL','alwaysPreserveClientCache','promptCacheDefaultTTL','promptCacheMaxBreakpoints']
keys_comp = ['defaultMode','autoTriggerMode','autoTriggerTokens','engines','rtkConfig','cavemanConfig','sessionDedup','preserveSystemPrompt','preserveToolDefinitions','disableMessageAging']
cur.execute("SELECT namespace, key, value FROM key_value WHERE (namespace='databaseSettings') OR (namespace='compression')")
rows = [r for r in cur.fetchall() if (r[0]=='databaseSettings' and r[1] in keys_db) or (r[0]=='compression' and r[1] in keys_comp)]
print(f'SNAPSHOT: {len(rows)} keys')
for ns, k, v in sorted(rows):
    print(f'{ns}.{k} = {v[:150]}')
conn.close()
