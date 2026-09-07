# -*- coding: utf-8 -*-
"""Clean summary + JP line-ceiling analysis."""
import json, io, unicodedata, statistics
from pathlib import Path

RF = Path(r"C:/TMP/opencode/career_fetch")
STORY50 = RF / "story_json/50"
for tag, root in [("04", Path(r"G:/Games/steamapps/common/UmamusumePrettyDerby_Jpn/gemini_horses/localized_data/assets/story/data/04")),
                  ("09", Path(r"G:/Games/steamapps/common/UmamusumePrettyDerby_Jpn/gemini_horses/localized_data/assets/story/data/09")),
                  ("50", Path(r"G:/Games/steamapps/common/UmamusumePrettyDerby_Jpn/gemini_horses/localized_data/assets/story/data/50"))]:
    locals()[tag] = root

def wide(c):
    return 2 if unicodedata.east_asian_width(c) in ("W", "F") else 1

def to_cols(s):
    return sum(wide(c) for c in s)

def jp_lines_of(paths):
    """line lengths in display cols of JP raw career source."""
    for p in paths:
        try:
            d = json.load(io.open(p, encoding="utf-8"))
        except Exception:
            continue
        for blk in d.get("text_block_list", []):
            t = blk.get("text")
            if not t:
                continue
            for ln in t.replace("\\r", "").replace("\r", "").split("\n"):
                yield to_cols(ln)

def en_stats(root):
    lines, cols = [], []
    n_entry = no_nl = 0
    tot_chars = tot_lines = 0
    entries = 0
    nfiles = 0
    for p in Path(root).rglob("storytimeline_*.json"):
        nfiles += 1
        try:
            d = json.load(io.open(p, encoding="utf-8"))
        except Exception:
            continue
        for blk in d.get("text_block_list", []):
            t = blk.get("text")
            if not t:
                continue
            entries += 1
            tot_chars += len(t)
            has_brk = False
            for ln in t.replace("\r", "").split("\n"):
                has_brk = has_brk or True
                lines.append(len(ln))
                tot_lines += 1
            if "\n" not in t and "\r" not in t:
                no_nl += 1
    lines.sort()
    pct = lambda q: lines[min(len(lines) - 1, int(q * len(lines)))]
    return {"files": nfiles, "entries": entries,
            "avgEnt": tot_chars / entries if entries else 0,
            "noNl%": 100 * no_nl / entries if entries else 0,
            "avgLn": tot_chars / tot_lines if tot_lines else 0,
            "med": pct(0.5), "p90": pct(0.9), "p99": pct(0.99), "mx": lines[-1],
            "n_lines": len(lines),
            "gt50%": 100 * sum(1 for l in lines if l > 50) / len(lines),
            "gt60%": 100 * sum(1 for l in lines if l > 60) / len(lines),
            "gt80%": 100 * sum(1 for l in lines if l > 80) / len(lines)}

# JP career raw source ceiling (display cols per visual line)
jp_cols = sorted(jp_lines_of(p for p in Path(STORY50).rglob("storytimeline_*.json")))
jpct = lambda q: jp_cols[min(len(jp_cols) - 1, int(q * len(jp_cols)))]

print("=" * 100)
print(f"JP raw career source (50/): visual lines measured in DISPLAY COLUMNS (full-width=2)")
print(f"  lines={len(jp_cols)}  avg={sum(jp_cols)/len(jp_cols):.1f} cols  "
      f"p50={jpct(0.5)}  p90={jpct(0.9)}  p95={jpct(0.95)}  p99={jpct(0.99)}  max={jp_cols[-1]}")
# ceiling: JP lines are hand-broken so none exceed box width; use max line as rough width cap for full-width text
print("=" * 100)

print(f"\n{'dir':<4}{'files':>6}{'entries':>9}{'avgEnt':>8}{'noNL%':>7}{'avgLn':>8}"
      f"{'medLn':>7}{'p90Ln':>7}{'p99Ln':>7}{'maxLn':>7}{'>50%':>7}{'>60%':>7}{'>80%':>7}")
print("-" * 100)
for label in ("04", "09", "50"):
    s = en_stats(locals()[label])
    print(f"{label:<4}{s['files']:>6}{s['entries']:>9}{s['avgEnt']:>8.1f}{s['noNl%']:>7.1f}"
          f"{s['avgLn']:>8.1f}{s['med']:>7}{s['p90']:>7}{s['p99']:>7}{s['mx']:>7}"
          f"{s['gt50%']:>7.1f}{s['gt60%']:>7.1f}{s['gt80%']:>7.1f}")
