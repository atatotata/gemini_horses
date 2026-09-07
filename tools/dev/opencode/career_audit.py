# -*- coding: utf-8 -*-
"""Career story overflow audit (step 1-3). Read-only analysis."""
import json, io, os, random, unicodedata, statistics
from pathlib import Path

RF = Path(r"C:/TMP/opencode/career_fetch")
G50 = Path(r"G:/Games/steamapps/common/UmamusumePrettyDerby_Jpn/gemini_horses/localized_data/assets/story/data/50")
G04 = Path(r"G:/Games/steamapps/common/UmamusumePrettyDerby_Jpn/gemini_horses/localized_data/assets/story/data/04")
G09 = Path(r"G:/Games/steamapps/common/UmamusumePrettyDerby_Jpn/gemini_horses/localized_data/assets/story/data/09")

def wide_len(s):
    return sum(2 if unicodedata.east_asian_width(c) in ("W", "F") else 1 for c in s)

def norm_breaks(s):
    # collapse literal & real CR/LF variants to '\n'; also literal backslash-n
    s = s.replace("\\r", "").replace("\\n", "\n")  # two-char escapes first
    s = s.replace("\r", "")
    return s

def has_brk(s):
    return ("\n" in s or "\r" in s or "\\n" in s)

def visual_lines(s):
    return norm_breaks(s).split("\n")

def body_stats(texts, top=20):
    """texts: list of (source_jp_or_id, str)."""
    lens = [len(t) for _, t in texts]
    nonl = [(i, l, t) for i, (_, t) in enumerate(texts) for l in [len(t)] if not has_brk(t) and l > 40]
    nnl = [l for _, l, _ in nonl]
    bins = [0, 40, 60, 80, 100, 120, 10**9]
    names = ["0-40", "40-60", "60-80", "80-100", "100-120", "120+"]
    hist = []
    for a, b in zip(bins, bins[1:]):
        hist.append(sum(1 for L in lens if a <= L < b))
    print(f"  N={len(texts):>7}  avg={statistics.mean(lens):7.1f}  max={max(lens):5d}  no-\\n(>40)={len(nnl):>6}")
    print("    >60/80/100/120 chars WITHOUT a line break:", " ".join(
        f">{x}:{sum(1 for l in nnl if l > x)}" for x in (60, 80, 100, 120)))
    print("    hist (all entries, whole-string):",
          " ".join(f"{nm}={v}" for nm, v in zip(names, hist)))
    hi = sorted(((len(t), t) for _, t in texts), reverse=True)[:top]
    print(f"    top{top} longest entries (len):")
    print("      " + ", ".join(str(l) for l, _ in hi))
    return hi

def load_texts(fn, is_choice=False):
    return [s for s in json.load(io.open(RF / fn, encoding="utf-8"))]

print("=" * 70)
print("STEP 1: unique string corpora (whole-entry character counts)")
print("=" * 70)
djp = load_texts("unique_dialogues.json")
cjp = load_texts("unique_choices.json")
ck = json.load(io.open(RF / "career_checkpoint.json", encoding="utf-8"))
den = [ck[k] for k in djp if k in ck]
cen = [ck[k] for k in cjp if k in ck]

for label, texts in [("unique_dialogues.json (JP)", [(None, t) for t in djp]),
                     ("  + EN translation side   ", [(None, t) for t in den]),
                     ("unique_choices.json  (JP)", [(None, t) for t in cjp]),
                     ("  + EN translation side   ", [(None, t) for t in cen])]:
    print(f"\n[{label}]")
    hi = body_stats(texts)

print("\n3 longest-sample lines:")
for grp, texts in [("EN dialogue", [(None, t) for t in den]), ("EN choice", [(None, t) for t in cen])]:
    for _, t in sorted(texts, key=lambda x: -len(x[1]))[:3]:
        disp = norm_breaks(t)
        print(f"  [{grp}] len={len(t):4d} | {disp[:110]}{'…' if len(disp) > 110 else ''}")

# ---------------- merged file scan ----------------
print("\n" + "=" * 70)
print("STEP 2: merged files under 50/ vs upstream 04/ & 09/ (per visual line, split on \\n)")
print("=" * 70)

def iter_files(root):
    for p in sorted(Path(root).rglob("storytimeline_*.json")):
        yield p

def scan_dir(root, limit=None):
    files = list(iter_files(root))
    if limit:
        files = files[:limit]
    n_entries = 0
    total_chars = 0
    total_lines = 0
    total_wchars = 0
    line_lens = []
    entry_lens = []
    no_nl_entries = 0
    entries_w_nl = 0
    nl_segments = 0
    n_block = 0
    for p in files:
        try:
            d = json.load(io.open(p, encoding="utf-8"))
        except Exception:
            continue
        for blk in d.get("text_block_list", []):
            t = blk.get("text")
            if not t:
                continue
            n_block += 1
            n_entries += 1
            L = len(t)
            entry_lens.append(L)
            if has_brk(t):
                entries_w_nl += 1
            else:
                no_nl_entries += 1
            for ln in visual_lines(t):
                total_lines += 1
                ll = len(ln)
                total_chars += ll
                total_wchars += wide_len(ln)
                line_lens.append(ll)
    return {"files": len(files), "blocks": n_block, "entries": n_entries,
            "avg_entry_chars": total_chars / n_entries if n_entries else 0,
            "no_nl_pct": 100 * no_nl_entries / n_entries if n_entries else 0,
            "avg_line_chars": total_chars / total_lines if total_lines else 0,
            "avg_line_wcol": total_wchars / total_lines if total_lines else 0,
            "median_line": statistics.median(line_lens) if line_lens else 0,
            "p90_line": (lambda v: v[int(len(v) * 0.9)] if v else 0)(sorted(line_lens)),
            "max_line": max(line_lens) if line_lens else 0,
            "lines_over_50": sum(1 for l in line_lens if l > 50),
            "lines_over_60": sum(1 for l in line_lens if l > 60)}

# Sample 5 random merged files under 50/
files50 = sorted(iter_files(G50))
rnd = random.Random(50)
sample = rnd.sample(files50, 5)
print("\nSampled merged files (5 random, seed=50):")

def scan_single(p):
    res = {"files": 1, "blocks": 0, "entries": 0, "no_nl_pct": 0,
           "avg_entry_chars": 0, "avg_line_chars": 0, "avg_line_wcol": 0,
           "median_line": 0, "p90_line": 0, "max_line": 0, "lines_over_50": 0, "lines_over_60": 0}
    d = json.load(io.open(p, encoding="utf-8"))
    lens, llens, total_chars, total_lines, total_wcol, no_nl = [], [], 0, 0, 0, 0
    for blk in d.get("text_block_list", []):
        t = blk.get("text")
        if not t:
            continue
        res["blocks"] += 1
        res["entries"] += 1
        lens.append(len(t))
        if not has_brk(t):
            no_nl += 1
        for ln in visual_lines(t):
            total_lines += 1
            total_chars += len(ln)
            total_wcol += wide_len(ln)
            llens.append(len(ln))
    if lens:
        res["avg_entry_chars"] = total_chars / res["entries"]
        res["no_nl_pct"] = 100 * no_nl / res["entries"]
    if llens:
        res["avg_line_chars"] = total_chars / total_lines
        res["avg_line_wcol"] = total_wcol / total_lines
        res["median_line"] = statistics.median(llens)
        srt = sorted(llens)
        res["p90_line"] = srt[int(len(srt) * 0.9)]
        res["max_line"] = max(llens)
        res["lines_over_50"] = sum(1 for l in llens if l > 50)
        res["lines_over_60"] = sum(1 for l in llens if l > 60)
    return res

hdr = f"{'file':<34}{'blk':>4}{'no\\n%':>7}{'avgEnt':>7}{'avgLine':>8}{'med':>5}{'p90':>5}{'maxLn':>6}{'>50':>5}{'>60':>5}"
print(hdr)
print("-" * len(hdr))
for p in sample:
    s = scan_single(p)
    print(f"{p.stem:<34}{s['blocks']:>4}{s['no_nl_pct']:>7.0f}{s['avg_entry_chars']:>7.1f}"
          f"{s['avg_line_chars']:>8.1f}{s['median_line']:>5.0f}{s['p90_line']:>5.0f}"
          f"{s['max_line']:>6.0f}{s['lines_over_50']:>5}{s['lines_over_60']:>5}")

print("\nUpstream UmaTL (aggregate over EN files under 04/ and 09/):")
print(hdr)
print("-" * len(hdr))
for label, root in [("04", G04), ("09", G09)]:
    s = scan_dir(root)
    print(f"{label:<34}{s['blocks']:>4}{s['no_nl_pct']:>7.0f}{s['avg_entry_chars']:>7.1f}"
          f"{s['avg_line_chars']:>8.1f}{s['median_line']:>5.0f}{s['p90_line']:>5.0f}"
          f"{s['max_line']:>6.0f}{s['lines_over_50']:>5}{s['lines_over_60']:>5}")
    print(f"     files={s['files']} entries={s['entries']} avg-width/line={s['avg_line_wcol']:.1f} cols")

print("\nWhole-folder career 50/ (context):")
s = scan_dir(G50)
print(f"     files={s['files']} blocks={s['blocks']} entries={s['entries']}")
print(f"     no\\n entries={s['no_nl_pct']:.0f}%  avg entry={s['avg_entry_chars']:.1f} chars  "
      f"avg line={s['avg_line_chars']:.1f} chars / {s['avg_line_wcol']:.1f} cols  "
      f"median={s['median_line']:.0f}  p90={s['p90_line']:.0f}  max={s['max_line']}")

# ---------------- STEP 3 expansion ratio ----------------
print("\n" + "=" * 70)
print("STEP 3: JP vs EN expansion (aligned pairs, per visual line)")
print("=" * 70)

def corpus_line_stats(texts):
    chars = lines = wcols = 0
    for t in texts:
        for ln in visual_lines(t):
            lines += 1
            chars += len(ln)
            wcols += wide_len(ln)
    return (chars / lines if lines else 0, wcols / lines if lines else 0, lines)

jp_chars_l, jp_w, jp_lines = corpus_line_stats(djp)
en_chars_l, en_w, en_lines = corpus_line_stats(den)
print(f"JP dialogues : avg {jp_chars_l:5.1f} chars / visual line   (~{jp_w:5.1f} display cols, wide=2)")
print(f"EN dialogues : avg {en_chars_l:5.1f} chars / visual line   (~{en_w:5.1f} display cols)")
print(f"ratio raw chars per line EN/JP = {en_chars_l / jp_chars_l:.2f}x   "
      f"(claim: English is typically 1.5-2x longer)")
print(f"ratio display width per line EN/JP = {en_w / jp_w:.2f}x   <- apples-to-apples, cols fitted in box")

# whole-entry ratio
tot_e = sum(len(t) for t in den) / sum(len(t) for t in djp)
print(f"whole-entry raw-char expansion = {tot_e:.2f}x")
