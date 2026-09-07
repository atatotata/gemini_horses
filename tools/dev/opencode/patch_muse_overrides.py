import sqlite3, json

conn = sqlite3.connect(r'C:\Users\Ota\.omniroute\storage.sqlite')
cur = conn.cursor()

# Set reasoning_efforts override to empty list [] so OmniRoute knows not to send reasoning_effort
models_to_override = [
    'muse-spark-1.2',
    'muse-spark-1.2-contributor',
    'muse-spark-1.2-contributor-xhigh',
    'muse-spark-1.2-contributor-high',
    'muse-spark-1.2-contributor-medium',
    'muse-spark-1.2-contributor-low',
    'muse-spark-1.2-contributor-minimal',
    'muse-spark-1.3',
    'muse-spark-1.3-contributor'
]

for m in models_to_override:
    cur.execute("""
    INSERT OR REPLACE INTO model_capability_overrides (provider, model_id, override_key, override_value, refreshed_at)
    VALUES ('opencode-go', ?, 'reasoning_efforts', '[]', datetime('now'))
    """, (m,))

conn.commit()

cur.execute("SELECT * FROM model_capability_overrides WHERE provider='opencode-go'")
print("Updated overrides:")
for r in cur.fetchall():
    print(r)

conn.close()
