#!/usr/bin/env python3
"""
sync_global.py — overlay Global official master.mdb EN over hachimi-tl-gemini-horses
Priority enforced:  SD (cat 48) > Global > UmaTL > Gemini
For all other categories: Global > UmaTL > Gemini (Gemini/UmaTL already baked into repo).

Global master is plain SQLite (no key) — bundles via meta are BLOCKED until
Global chacha20 key (A713...) is resolved, so this script handles master-derived
dicts only: text_data_dict, character_system_text_dict, race_jikkyo_*.

Usage:
  python sync_global.py              # overlay from default Global install
  python sync_global.py --dry-run    # report only
  python sync_global.py --global-master "D:\\Global\\master.mdb"
"""
import argparse, json, os, re, sqlite3, shutil
from pathlib import Path

GEMINI_DIR = Path(__file__).parent / "localized_data"
HACHIMI_DIR = Path(r"G:\Games\steamapps\common\UmamusumePrettyDerby_Jpn\hachimi\localized_data_1")
GLOBAL_MASTER_DEFAULT = Path(r"G:\Games\steamapps\common\UmamusumePrettyDerby\UmamusumePrettyDerby_Data\Persistent\master\master.mdb")
CJK_RE = re.compile(r"[\u3040-\u30ff\u3400-\u4dbf\u4e00-\u9fff\uf900-\ufaff]")

def load_global_tables(global_master: Path):
    db = sqlite3.connect(str(global_master))
    cur = db.cursor()
    # text_data: (category, index) -> text
    cur.execute('SELECT category, "index", text FROM text_data')
    g_text = {(r[0], r[1]): r[2] for r in cur.fetchall()}
    # character_system_text: (character_id, voice_id) -> text
    cur.execute("SELECT character_id, voice_id, text FROM character_system_text")
    g_cst = {(r[0], r[1]): r[2] for r in cur.fetchall()}
    # race jikkyo
    cur.execute("SELECT id, message FROM race_jikkyo_message")
    g_rjm = {r[0]: r[1] for r in cur.fetchall()}
    cur.execute("SELECT id, message FROM race_jikkyo_comment")
    g_rjc = {r[0]: r[1] for r in cur.fetchall()}
    db.close()
    return g_text, g_cst, g_rjm, g_rjc

def main():
    ap = argparse.ArgumentParser(description="Overlay Global official EN (SD top for cat48)")
    ap.add_argument("--global-master", type=Path, default=GLOBAL_MASTER_DEFAULT)
    ap.add_argument("--dry-run", action="store_true")
    ap.add_argument("--no-hachimi-sync", action="store_true", help="skip mirroring to hachimi/localized_data_1")
    args = ap.parse_args()

    if not args.global_master.exists():
        print(f"Global master not found: {args.global_master}", flush=True)
        raise SystemExit(2)

    g_text, g_cst, g_rjm, g_rjc = load_global_tables(args.global_master)
    print(f"Global master: text_data {len(g_text)} | cst {len(g_cst)} | rjm {len(g_rjm)} | rjc {len(g_rjc)}", flush=True)
    print("Priority: SD(cat48) > Global > UmaTL > Gemini  (cat48 SD bypass keeps 2127 SD numeric)", flush=True)
    if not args.dry_run:
        print("Meta bundles (story/home/lyrics) BLOCKED - Global meta key 12B invalid, needs runtime dump", flush=True)

    # Targets: hachimi-tl-gemini-horses + optional hachimi mirror
    targets = [GEMINI_DIR]
    if not args.no_hachimi_sync and HACHIMI_DIR.exists():
        targets.append(HACHIMI_DIR)

    for base in targets:
        label = "hachimi-tl-gemini-horses" if base == GEMINI_DIR else "hachimi"
        # text_data_dict: nested {cat: {idx: text}}
        p = base / "text_data_dict.json"
        if p.exists():
            d = json.loads(p.read_text(encoding="utf-8"))
            replaced = 0
            skipped_sd = 0
            jp_preserved = 0
            g_only = 0
            for (cat, idx), en in g_text.items():
                ck, ik = str(cat), str(idx)
                # SD bypass: never overwrite cat48 with Global prose
                if cat == 48:
                    skipped_sd += 1
                    continue
                if ck in d and ik in d[ck]:
                    if d[ck][ik] != en:
                        if not args.dry_run:
                            d[ck][ik] = en
                        replaced += 1
                elif ck in d:
                    # key missing -> JP-only preservation check: Global has it but local missing -> would be Global-only addition
                    # We preserve JP-only by NOT adding Global-only keys that don't exist locally
                    g_only += 1
                else:
                    g_only += 1
            # JP-only preservation: count master keys Global lacks (already in repo, keep them)
            # Not adding g_only keeps 43k JP-only intact
            print(f"[{label}] text_data: {replaced} Global>MT overwrites | {skipped_sd} cat48 SD-preserved | {g_only} Global-only skipped (JP-only kept)", flush=True)
            if not args.dry_run:
                # backup once
                bak = p.with_suffix(p.suffix + ".bak_global")
                if not bak.exists():
                    shutil.copy2(p, bak)
                p.write_text(json.dumps(d, ensure_ascii=False, indent=2) + "\n", encoding="utf-8", newline="\n")

        # character_system_text_dict: {char_id: {voice_id: text}}
        p = base / "character_system_text_dict.json"
        if p.exists():
            d = json.loads(p.read_text(encoding="utf-8"))
            repl = 0
            for (cid, vid), en in g_cst.items():
                ck, vk = str(cid), str(vid)
                if ck in d and vk in d[ck] and d[ck][vk] != en:
                    if not args.dry_run:
                        d[ck][vk] = en
                    repl += 1
            print(f"[{label}] cst: {repl} Global>MT overwrites (JP-only preserved)", flush=True)
            if not args.dry_run:
                bak = p.with_suffix(p.suffix + ".bak_global")
                if not bak.exists():
                    shutil.copy2(p, bak)
                p.write_text(json.dumps(d, ensure_ascii=False, indent=2) + "\n", encoding="utf-8", newline="\n")

        # race_jikkyo_message_dict: flat {id: text}
        for fname, gmap in [("race_jikkyo_message_dict.json", g_rjm), ("race_jikkyo_comment_dict.json", g_rjc)]:
            p = base / fname
            if not p.exists():
                continue
            d = json.loads(p.read_text(encoding="utf-8"))
            repl = 0
            for gid, en in gmap.items():
                k = str(gid)
                if k in d and d[k] != en:
                    if not args.dry_run:
                        d[k] = en
                    repl += 1
            print(f"[{label}] {fname}: {repl} Global>MT overwrites", flush=True)
            if not args.dry_run and repl:
                bak = p.with_suffix(p.suffix + ".bak_global")
                if not bak.exists():
                    shutil.copy2(p, bak)
                p.write_text(json.dumps(d, ensure_ascii=False, indent=2) + "\n", encoding="utf-8", newline="\n")

    if args.dry_run:
        print("dry-run: no files written", flush=True)
    else:
        print("done - run `python sync_umatl.py --regen-index` and `git diff --stat` to verify", flush=True)

if __name__ == "__main__":
    main()
