import sqlite3, json

conn = sqlite3.connect(
    "file:G:/Games/steamapps/common/UmamusumePrettyDerby_Jpn/UmamusumePrettyDerby_Jpn_Data/Persistent/master/master.mdb?mode=ro",
    uri=True,
)
conn.text_factory = bytes
keys = [(1, 973), (10, 333), (23, 333), (24, 333), (63, 374), (63, 383),
        (377, 10), (378, 10), (394, 60)]
jp = {}
for c, i in keys:
    r = conn.execute(
        "SELECT text FROM text_data WHERE category=? AND `index`=?", (c, i)
    ).fetchone()
    jp[f"{c}/{i}"] = r[0].decode("utf-8", "replace") if r else None

repo = json.load(open(
    "G:/Games/steamapps/common/UmamusumePrettyDerby_Jpn/gemini_horses/localized_data/text_data_dict.json",
    encoding="utf-8"))
live = json.load(open(
    "G:/Games/steamapps/common/UmamusumePrettyDerby_Jpn/hachimi/localized_data_1/text_data_dict.json",
    encoding="utf-8"))
out = {}
for k in jp:
    c, i = k.split("/")
    out[k] = {
        "jp": jp[k],
        "repo": (repo.get(c, {}).get(i)),
        "live": (live.get(c, {}).get(i)),
    }
json.dump(out, open("C:/TMP/opencode/trainer_ability_check.json", "w", encoding="utf-8"),
          ensure_ascii=False, indent=2)
print("wrote check file")
