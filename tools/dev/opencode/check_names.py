import json, sys

vb = json.load(open(r"G:\Games\steamapps\common\UmamusumePrettyDerby_Jpn\gemini_horses\tools\voice_bible\uma_voice_bible.json", encoding="utf-8"))
td = json.load(open(r"G:\Games\steamapps\common\UmamusumePrettyDerby_Jpn\gemini_horses\localized_data\text_data_dict.json", encoding="utf-8"))["6"]

print(f"Total in voice bible: {len(vb)}")
print(f"Total in text_data cat 6: {len(td)}")

discrepancies = []
for cid, entry in sorted(vb.items(), key=lambda x: int(x[0])):
    v_en = entry.get("en", "")
    t_en = td.get(cid, "")
    jp = entry.get("jp", "")
    if v_en != t_en:
        discrepancies.append((cid, jp, v_en, t_en))

print(f"Discrepancies between voice bible and text_data_dict cat 6: {len(discrepancies)}")
for d in discrepancies:
    sys.stdout.buffer.write(f"ID {d[0]} [{d[1]}]: voice_bible='{d[2]}' vs text_data='{d[3]}'\n".encode("utf-8"))
