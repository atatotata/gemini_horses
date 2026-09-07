"""Quick probe of meta_fresh.bin to understand how to open it."""
import apsw
import apsw._sqlite3mc as mc

print("apsw version:", apsw.apswversion())
print("_sqlite3mc module:", mc)

# Approach 1: Direct path without URI
try:
    conn = apsw.Connection(r"C:\TMP\meta_fresh.bin", flags=apsw.SQLITE_OPEN_READONLY)
    cur = conn.cursor()
    print("Direct open OK")
    print(list(cur.execute("SELECT COUNT(*) FROM a")))
    conn.close()
except Exception as ex:
    print(f"Direct open fail: {ex}")

# Approach 2: URI with hexkey
try:
    uri = "file:C:/TMP/meta_fresh.bin?hexkey=9c2bab97_bde7e9fd"
    conn = apsw.Connection(uri, flags=apsw.SQLITE_OPEN_READONLY | apsw.SQLITE_OPEN_URI)
    cur = conn.cursor()
    print("URI open OK")
    print(list(cur.execute("SELECT COUNT(*) FROM a")))
    conn.close()
except Exception as ex:
    print(f"URI open fail: {ex}")

# Approach 3: PRAGMA key after opening
try:
    conn = apsw.Connection(r"C:\TMP\meta_fresh.bin", flags=apsw.SQLITE_OPEN_READONLY)
    cur = conn.cursor()
    cur.execute("PRAGMA key = \"x'9c2bab97bde7e9fd'\"")
    print("PRAGMA key OK")
    print(list(cur.execute("SELECT COUNT(*) FROM a")))
    conn.close()
except Exception as ex:
    print(f"PRAGMA key fail: {ex}")

# Approach 4: Check how existing scripts open it
# from utils import _derive_decryption_key, DB_KEY
# Look at existing scripts for the right way
try:
    from pathlib import Path
    GAME_DIR = Path(r"G:/Games/steamapps/common/UmamusumePrettyDerby_Jpn")
    sys_path_utils = GAME_DIR / "gemini_horses/tools/umamusu-utils/scripts"
    import sys
    sys.path.insert(0, str(sys_path_utils))
    from utils import DB_KEY, dict_factory
    print(f"DB_KEY from utils: {DB_KEY}")
except Exception as ex:
    print(f"utils import fail: {ex}")
