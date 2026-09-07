#!/usr/bin/env python3
"""
Re-probe Persistent/dat local presence after full download — strictly read-only.
"""
import json, time, os
from pathlib import Path
import apsw

KEY = "9c2bab97bcf8c0c4f1a9ea7881a213f6c9ebf9d8d4c6a8e43ce5a259bde7e9fd"
META = Path(r'C:\TMP\meta_fresh.bin')
DAT = Path(r'G:\Games\steamapps\common\UmamusumePrettyDerby_Jpn\UmamusumePrettyDerby_Jpn_Data\Persistent\dat')
LOC = Path(r'G:\Games\steamapps\common\UmamusumePrettyDerby_Jpn\gemini_horses\localized_data\assets')

# ── Step 1: ensure meta_fresh.bin exists ──
META_SRC = Path(r'G:\Games\steamapps\common\UmamusumePrettyDerby_Jpn\UmamusumePrettyDerby_Jpn_Data\Persistent\meta')
if not META.exists():
    print(f"Copying meta → {META} ...")
    import shutil
    shutil.copy2(META_SRC, META)
    print(f"  Copied {META.stat().st_size:,} bytes")
else:
    print(f"meta_fresh.bin present: {META.stat().st_size:,} bytes")

# ── Step 2: open meta via hexkey URI (default VFS) ──
uri = f'file:{META}?hexkey={KEY}'
print(f"\nOpening meta via default VFS with hexkey...")
db = apsw.Connection(uri, flags=apsw.SQLITE_OPEN_READONLY | apsw.SQLITE_OPEN_URI)

count = db.execute("SELECT COUNT(*) FROM a").fetchone()[0]
print(f"Row count: {count}")
assert count == 365808, f"Expected 365808, got {count}"

# ── Step 3: Collect meta entries per prefix ──
# Meta has n=name, h=hash, e=? columns
# story/data/{prefix}/{sid}/storytimeline_{sid}.json  — paths with depth 5
# home/data/{sub}/{hometimeline_XXX}.json
# live/musicscores/{sub}/mXXXX_lyrics
# race/storyrace/text/storyrace_XXXXX

# ── 3a. Story data ──
story_prefixes = ["50", "40", "11", "80", "83"]
meta_story = {}  # prefix -> list of (n, h, sid)
for pfx in story_prefixes:
    rows = db.execute(
        "SELECT n, h FROM a WHERE n LIKE ?",
        (f"story/data/{pfx}/%storytimeline_%",)
    ).fetchall()
    # Extract SID from the filename
    items = []
    for n, h in rows:
        parts = n.split("/")
        if len(parts) >= 5:
            fname = parts[-1]
            if fname.startswith("storytimeline_"):
                sid = fname[len("storytimeline_"):]
                items.append((n, h, sid))
    meta_story[pfx] = items
    print(f"  meta story/{pfx}: {len(items)} storytimelines")

# Also get the total meta entries for this prefix (includes resourcelist, ast_ etc.)
meta_story_total = {}
for pfx in story_prefixes:
    total = db.execute(
        "SELECT COUNT(*) FROM a WHERE n LIKE ?",
        (f"story/data/{pfx}/%",)
    ).fetchone()[0]
    meta_story_total[pfx] = total

# ── 3b. Home data ──
meta_home_rows = db.execute("SELECT n, h FROM a WHERE n LIKE 'home/data/%'").fetchall()
meta_home = []
for n, h in meta_home_rows:
    parts = n.split("/")
    if len(parts) >= 5:
        fname = parts[-1]
        if fname.startswith("hometimeline_"):
            meta_home.append((n, h, fname))
print(f"  meta home: {len(meta_home)} hometimelines (total home/data: {len(meta_home_rows)})")

# ── 3c. Lyrics ──
meta_lyrics_rows = db.execute("SELECT n, h FROM a WHERE n LIKE 'live/musicscores/%' AND n LIKE '%_lyrics'").fetchall()
meta_lyrics = []
for n, h in meta_lyrics_rows:
    meta_lyrics.append((n, h, n.split("/")[-1]))
print(f"  meta lyrics: {len(meta_lyrics)} entries")

# ── 3d. Storyrace ──
meta_sr_rows = db.execute("SELECT n, h FROM a WHERE n LIKE 'race/storyrace/text/%'").fetchall()
meta_sr = []
for n, h in meta_sr_rows:
    fname = n.split("/")[-1]
    if fname.startswith("storyrace_"):
        sr_id = fname[len("storyrace_"):]
        meta_sr.append((n, h, sr_id))
print(f"  meta storyrace: {len(meta_sr)} entries (total race/storyrace/text: {len(meta_sr_rows)})")

# ── Step 3e: Count localized files ──
import re
re_plain = re.compile(r'^storytimeline_(\d+)\.json$')
re_home = re.compile(r'^hometimeline_[^/]+\.json$')
re_lyric = re.compile(r'^m\d+_lyrics\.json$')
re_sr = re.compile(r'^storyrace_(\d+)\.json$')

# Story localized
loc_story = {}  # prefix -> set of SIDs
for pfx in story_prefixes:
    d = LOC / "story" / "data" / pfx
    sids = set()
    if d.exists():
        for f in d.rglob("storytimeline_*.json"):
            m = re_plain.match(f.name)
            if m:
                sids.add(m.group(1))
    loc_story[pfx] = sids
    print(f"  localized story/{pfx}: {len(sids)} SIDs")

# Home localized
loc_home_sids = set()
home_dir = LOC / "home" / "data"
if home_dir.exists():
    for f in home_dir.rglob("*.json"):
        m = re_home.match(f.name)
        if m:
            loc_home_sids.add(f.name)
print(f"  localized home: {len(loc_home_sids)} hometimeline files")

# Lyrics localized
loc_lyrics_sids = set()
lyrics_dir = LOC / "lyrics"
if lyrics_dir.exists():
    for f in lyrics_dir.glob("*_lyrics.json"):
        loc_lyrics_sids.add(f.name)
print(f"  localized lyrics: {len(loc_lyrics_sids)} files")

# Storyrace localized
loc_sr_sids = set()
sr_dir = LOC / "race" / "storyrace"
if sr_dir.exists():
    for f in sr_dir.rglob("storyrace_*.json"):
        m = re_sr.match(f.name)
        if m:
            loc_sr_sids.add(m.group(1))
print(f"  localized storyrace: {len(loc_sr_sids)} SIDs")

db.close()

# ── Step 4: Compute gaps and probe dat ──
print("\n── Probing dat local presence for gap items ──")
results = {}
total_gap = 0
total_local = 0
total_cdn = 0

# Story prefixes
for pfx in story_prefixes:
    meta_sids = {sid for _, _, sid in meta_story[pfx]}
    loc_sids = loc_story.get(pfx, set())
    gap_sids = meta_sids - loc_sids
    
    local_present = 0
    need_cdn = 0
    missing_local_samples = []
    
    # Build a lookup: sid -> h
    sid_to_h = {sid: h for n, h, sid in meta_story[pfx]}
    
    for sid in sorted(gap_sids):
        h = sid_to_h.get(sid)
        if h:
            dat_path = DAT / h[:2] / h
            if dat_path.exists():
                local_present += 1
            else:
                need_cdn += 1
                if len(missing_local_samples) < 5:
                    missing_local_samples.append(sid)
    
    gap_actual = local_present + need_cdn
    ratio = (local_present / gap_actual * 100) if gap_actual > 0 else 100.0
    total_gap += gap_actual
    total_local += local_present
    total_cdn += need_cdn
    
    results[f"story_{pfx}"] = {
        "meta": len(meta_story[pfx]),
        "meta_total_incl_ast": meta_story_total.get(pfx, 0),
        "localized": len(loc_sids),
        "gap": gap_actual,
        "local_present": local_present,
        "need_cdn": need_cdn,
        "local_ratio": round(ratio, 1),
        "sample_missing_local_sids": missing_local_samples[:5],
    }
    print(f"  story/{pfx}: gap={gap_actual}, local={local_present}, cdn={need_cdn}, ratio={ratio:.1f}%")

# Home
meta_home_sids = {sid for _, _, sid in meta_home}
gap_home_sids = meta_home_sids - loc_home_sids
local_home = 0
cdn_home = 0
missing_home_samples = []
sid_to_h_home = {sid: h for n, h, sid in meta_home}
for sid in sorted(gap_home_sids):
    h = sid_to_h_home.get(sid)
    if h:
        dat_path = DAT / h[:2] / h
        if dat_path.exists():
            local_home += 1
        else:
            cdn_home += 1
            if len(missing_home_samples) < 5:
                missing_home_samples.append(sid)
gap_home = local_home + cdn_home
ratio_home = (local_home / gap_home * 100) if gap_home > 0 else 100.0
total_gap += gap_home
total_local += local_home
total_cdn += cdn_home
results["home"] = {
    "meta": len(meta_home),
    "meta_total_incl_ast": len(meta_home_rows),
    "localized": len(loc_home_sids),
    "gap": gap_home,
    "local_present": local_home,
    "need_cdn": cdn_home,
    "local_ratio": round(ratio_home, 1),
    "sample_missing_local_sids": missing_home_samples[:5],
}
print(f"  home: gap={gap_home}, local={local_home}, cdn={cdn_home}, ratio={ratio_home:.1f}%")

# Lyrics
meta_lyrics_files = {fname for _, _, fname in meta_lyrics}
gap_lyrics = meta_lyrics_files - loc_lyrics_sids
local_lyrics = 0
cdn_lyrics = 0
missing_lyrics_samples = []
sid_to_h_lyrics = {fname: h for n, h, fname in meta_lyrics}
for fname in sorted(gap_lyrics):
    h = sid_to_h_lyrics.get(fname)
    if h:
        dat_path = DAT / h[:2] / h
        if dat_path.exists():
            local_lyrics += 1
        else:
            cdn_lyrics += 1
            if len(missing_lyrics_samples) < 5:
                missing_lyrics_samples.append(fname)
gap_lyrics_actual = local_lyrics + cdn_lyrics
ratio_lyrics = (local_lyrics / gap_lyrics_actual * 100) if gap_lyrics_actual > 0 else 100.0
total_gap += gap_lyrics_actual
total_local += local_lyrics
total_cdn += cdn_lyrics
results["lyrics"] = {
    "meta": len(meta_lyrics),
    "localized": len(loc_lyrics_sids),
    "gap": gap_lyrics_actual,
    "local_present": local_lyrics,
    "need_cdn": cdn_lyrics,
    "local_ratio": round(ratio_lyrics, 1),
    "sample_missing_local_sids": missing_lyrics_samples[:5],
}
print(f"  lyrics: gap={gap_lyrics_actual}, local={local_lyrics}, cdn={cdn_lyrics}, ratio={ratio_lyrics:.1f}%")

# Storyrace
meta_sr_ids = {sid for _, _, sid in meta_sr}
gap_sr = meta_sr_ids - loc_sr_sids
local_sr = 0
cdn_sr = 0
missing_sr_samples = []
sid_to_h_sr = {sid: h for n, h, sid in meta_sr}
for sid in sorted(gap_sr):
    h = sid_to_h_sr.get(sid)
    if h:
        dat_path = DAT / h[:2] / h
        if dat_path.exists():
            local_sr += 1
        else:
            cdn_sr += 1
            if len(missing_sr_samples) < 5:
                missing_sr_samples.append(sid)
gap_sr_actual = local_sr + cdn_sr
ratio_sr = (local_sr / gap_sr_actual * 100) if gap_sr_actual > 0 else 100.0
total_gap += gap_sr_actual
total_local += local_sr
total_cdn += cdn_sr
results["storyrace"] = {
    "meta": len(meta_sr),
    "localized": len(loc_sr_sids),
    "gap": gap_sr_actual,
    "local_present": local_sr,
    "need_cdn": cdn_sr,
    "local_ratio": round(ratio_sr, 1),
    "sample_missing_local_sids": missing_sr_samples[:5],
}
print(f"  storyrace: gap={gap_sr_actual}, local={local_sr}, cdn={cdn_sr}, ratio={ratio_sr:.1f}%")

total_ratio = (total_local / total_gap * 100) if total_gap > 0 else 100.0
print(f"\n  TOTAL: gap={total_gap}, local={total_local}, cdn={total_cdn}, ratio={total_ratio:.1f}%")

# ── Step 5: Write report ──
report = {
    "timestamp": time.strftime("%Y-%m-%dT%H:%M:%S"),
    "meta_count": 365808,
    "meta_file_size": META.stat().st_size,
    "dat_dir": str(DAT),
    "dat_file_count": sum(1 for _ in DAT.rglob("*") if _.is_file()),
    "total_gap": total_gap,
    "total_local_present": total_local,
    "total_need_cdn": total_cdn,
    "total_local_ratio": round(total_ratio, 1),
    "prefixes": results,
    "notes": [
        "Strictly read-only — no downloads, no extractions.",
        "gap = meta entries (storytimelines/hometimelines/lyrics/storyrace) not in localized_data.",
        "local_present = gap items where dat/{h[:2]}/{h} exists on disk.",
        "need_cdn = gap items NOT found in local dat.",
        "local_ratio = local_present / gap * 100.",
        "After full download, dat grew +33k bundles.",
    ]
}

out_path = Path(r"C:\TMP\dat_probe_fresh.json")
out_path.write_text(json.dumps(report, indent=2, ensure_ascii=False), encoding="utf-8")
print(f"\nReport written to {out_path}")
print(json.dumps(report, indent=2, ensure_ascii=True))
