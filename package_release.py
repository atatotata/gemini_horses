#!/usr/bin/env python3
"""Build manual-install release zips with a primed Hachimi repo cache.

Why: Hachimi treats a hand-extracted localized_data_N folder as a brand-new
repo (empty .tl_repo_cache_N) and re-downloads everything on the next update
check. Shipping a primed cache (hashes copied from the branch's own
index.json) makes the first check a no-op: zero downloads, plug-and-play.

Each zip contains:
  localized_data/...        exact branch content (via git archive)
  .tl_repo_cache_TEMPLATE   rename to .tl_repo_cache_{id} (match your .tl_repos id)
  INSTALL.txt               3-step manual install

Usage:
  python package_release.py --branch main [--tag v5] [--force]

Writes to releases/ (gitignored). Upload with:
  gh release upload <tag> releases/*.zip
"""
import argparse
import io
import json
import subprocess
import sys
import zipfile
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent
RELEASES = REPO_ROOT / "releases"

INSTALL_TXT = """MANUAL INSTALL - no big download, works on old Hachimi too
=====================================================
You need: this zip + your Hachimi folder (next to the game exe).

1. Pick a number N for this repo and add it to hachimi\\.tl_repos
   (make N up if the file doesn't exist yet):
     {{"repos": [{{"id": N, "index": "{index_url}"}}]}}

2. Extract this zip's localized_data\\* into hachimi\\localized_data_N\\

3. Copy .tl_repo_cache_TEMPLATE to hachimi\\.tl_repo_cache_N
   (same N as step 1 - the name must match!)

Launch the game. The first update check finds nothing to do.
Later updates arrive as small incrementals, as usual.
"""


def sh(*args) -> bytes:
    return subprocess.check_output(args, cwd=REPO_ROOT)


def build(branch: str, tag: str, force: bool) -> Path:
    RELEASES.mkdir(exist_ok=True)
    out = RELEASES / f"hachimi-tl-gemini-horses_{branch}_{tag}.zip"
    if out.exists() and not force:
        print(f"  skip {out.name} (exists, use --force)")
        return out

    index = json.loads(sh("git", "show", f"origin/{branch}:index.json").decode())
    files = {f["path"]: f["hash"] for f in index["files"]}
    cache = {"base_url": index["base_url"], "files": files}

    base = io.BytesIO(sh("git", "archive", "--format=zip", branch, "--", "localized_data"))
    with zipfile.ZipFile(io.BytesIO(base.getvalue())) as zin:
        names = zin.namelist()
        with zipfile.ZipFile(out, "w", zipfile.ZIP_DEFLATED, compresslevel=6) as zout:
            for n in names:
                zout.writestr(n, zin.read(n))
            zout.writestr(
                ".tl_repo_cache_TEMPLATE", json.dumps(cache, ensure_ascii=False))
            zout.writestr(
                "INSTALL.txt",
                INSTALL_TXT.format(index_url=index["base_url"].replace(
                    "/localized_data", "/index.json")))

    # Self-check: simulate Hachimi's diff (cache vs index).
    with zipfile.ZipFile(out) as z:
        got_cache = json.loads(z.read(".tl_repo_cache_TEMPLATE").decode())
    assert got_cache["base_url"] == index["base_url"], "base_url mismatch"
    diffs = [p for p, h in got_cache["files"].items()
             if index and h != {f["path"]: f["hash"] for f in index["files"]}.get(p)]
    assert not diffs, f"{len(diffs)} diffs would still download!"
    print(f"  built {out.name} "
          f"({out.stat().st_size / 1024 / 1024:.1f} MB, "
          f"{len(files)} files, 0 diffs)")
    return out


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--branch", action="append", default=[],
                    help="branch to package (repeatable)")
    ap.add_argument("--tag", default="v5")
    ap.add_argument("--force", action="store_true")
    args = ap.parse_args()
    branches = args.branch or ["main", "community", "lore", "full-slim"]
    for b in branches:
        build(b, args.tag, args.force)
    return 0


if __name__ == "__main__":
    sys.exit(main())
