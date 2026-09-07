import sqlite3, json
conn = sqlite3.connect(r'C:\Users\Ota\.omniroute\storage.sqlite')
cur = conn.cursor()
for k in ['outputStyles','ultra','ultraEngine','ultraSlmPrewarm','cavemanOutputMode','comboOverrides','activeComboId','compressionComboId']:
    cur.execute("SELECT value FROM key_value WHERE namespace='compression' AND key=?", (k,))
    row = cur.fetchone()
    print(f'=== {k} ===')
    if row:
        try:
            print(json.dumps(json.loads(row[0]), indent=2))
        except:
            print(row[0])
    else:
        print('None')
conn.close()
