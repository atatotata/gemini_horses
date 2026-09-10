#!/usr/bin/env python3
import os
import json
import pathlib

try:
    import blake3
    def hash_file(data: bytes) -> str:
        return blake3.blake3(data).hexdigest()
except ImportError:
    import hashlib
    def hash_file(data: bytes) -> str:
        return hashlib.sha256(data).hexdigest()

def main():
    repo_root = pathlib.Path(__file__).parent.resolve()
    dest_tl = repo_root / "localized_data"
    index_file = repo_root / "index.json"

    # Default URLs if not already set (zip_* required by Hachimi for full/fresh downloads, e.g. Android)
    base_url = "https://raw.githubusercontent.com/atatotata/gemini_horses/main/localized_data"
    zip_url = "https://codeload.github.com/atatotata/gemini_horses/zip/refs/heads/main"
    zip_dir = "gemini_horses-main/localized_data"
    if index_file.exists():
        try:
            with open(index_file, "r", encoding="utf-8") as f:
                old_idx = json.load(f)
                base_url = old_idx.get("base_url", base_url)
                zip_url = old_idx.get("zip_url", zip_url)
                zip_dir = old_idx.get("zip_dir", zip_dir)
        except Exception:
            pass

    file_entries = []

    # Font bundles: required by config.json (extra_asset_bundle -> replacement font).
    # Only these two non-JSON files are indexed; all other media stays out,
    # unless a `.full_media` sentinel exists in the repo root listing extra
    # allowed dirs (one per line, e.g. `assets/textures`). Sprite atlases broke
    # stat numbers and movies are huge: never indexed anywhere.
    FONT_BUNDLES = {"includes_win", "includes_android"}
    NEVER_INDEX_DIRS = {"atlas", "movies"}
    media_dirs = ()
    sentinel = repo_root / ".full_media"
    if sentinel.exists():
        media_dirs = tuple(
            line.strip().rstrip("/")
            for line in sentinel.read_text(encoding="utf-8").splitlines()
            if line.strip() and not line.strip().startswith("#")
        )

    def _allowed(rel_path: str, fname: str) -> bool:
        if fname.endswith(".json") or fname in FONT_BUNDLES:
            return True
        if not media_dirs:
            return False
        return any(rel_path == d or rel_path.startswith(d + "/") for d in media_dirs)

    for root, dirs, files in os.walk(dest_tl):
        dirs[:] = [d for d in dirs if d not in NEVER_INDEX_DIRS]
        for file in files:
            if ".bak" in file:
                continue
            rel_path = (pathlib.Path(root) / file).relative_to(dest_tl).as_posix()
            if not _allowed(rel_path, file):
                continue
            fpath = pathlib.Path(root) / file
            rel_path = fpath.relative_to(dest_tl).as_posix()
            data = fpath.read_bytes()
            f_hash = hash_file(data)
            f_size = len(data)
            file_entries.append({
                "path": rel_path,
                "hash": f_hash,
                "size": f_size
            })

    # Sort files deterministically by path
    file_entries.sort(key=lambda x: x["path"])

    manifest = {
        "base_url": base_url,
        "zip_url": zip_url,
        "zip_dir": zip_dir,
        "files": file_entries
    }

    with open(index_file, "w", encoding="utf-8", newline="\n") as f:
        json.dump(manifest, f, indent=2, ensure_ascii=False)

    print(f"Updated index.json: {len(file_entries)} files indexed (BLAKE3 format).")

if __name__ == "__main__":
    main()
