import apsw, os, sys

conn = apsw.Connection(r"G:\Games\steamapps\common\UmamusumePrettyDerby_Jpn\UmamusumePrettyDerby_Jpn_Data\Persistent\meta")
key = "f170cea4dfcea3e1a5d8c70bd1"
cursor = conn.cursor()
cursor.execute(f"PRAGMA key = \"x'{key}'\";")
cursor.execute("SELECT h, n, e FROM a WHERE n LIKE '%041001001%';")
rows = cursor.fetchall()
print("Found rows:", rows)

if rows:
    h, n, e = rows[0]
    dat_path = os.path.join(r"G:\Games\steamapps\common\UmamusumePrettyDerby_Jpn\UmamusumePrettyDerby_Jpn_Data\Persistent\dat", h[:2], h)
    print("Dat path exists:", os.path.exists(dat_path))
    
    # Decrypt with hachimi-tools decrypt logic
    sys.path.insert(0, r"G:\Games\steamapps\common\UmamusumePrettyDerby_Jpn\gemini_horses\tools\hachimi-tools")
    import decrypt
    dec_data = decrypt.decrypt_asset(open(dat_path, "rb").read(), e)
    
    import UnityPy
    env = UnityPy.load(dec_data)
    clip_objects = {}
    timeline_tree = None
    for obj in env.objects:
        if obj.type.name == "MonoBehaviour":
            tree = obj.read_typetree()
            if tree and isinstance(tree, dict):
                if "BlockList" in tree:
                    timeline_tree = tree
                elif "Text" in tree:
                    clip_objects[obj.path_id] = tree
                    
    print("Total BlockList in 041001001 bundle:", len(timeline_tree["BlockList"]))
    for i, b in enumerate(timeline_tree["BlockList"][:5]):
        tt = b.get("TextTrack", {})
        clips = tt.get("ClipList", [])
        txt = ""
        for c in clips:
            pid = c.get("m_PathID")
            if pid in clip_objects:
                txt = clip_objects[pid].get("Text")
        sys.stdout.buffer.write(f"BlockList[{i}]: {repr(txt)}\n".encode("utf-8"))
