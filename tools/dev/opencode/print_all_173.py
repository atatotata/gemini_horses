import json, sys

vb = json.load(open(r"G:\Games\steamapps\common\UmamusumePrettyDerby_Jpn\gemini_horses\tools\voice_bible\uma_voice_bible.json", encoding="utf-8"))
for cid, entry in sorted(vb.items(), key=lambda x: int(x[0])):
    v_en = entry.get("en", "")
    jp = entry.get("jp", "")
    sys.stdout.buffer.write(f"{cid}\t{jp}\t{v_en}\n".encode("utf-8"))
