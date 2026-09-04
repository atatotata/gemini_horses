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

    for root, dirs, files in os.walk(dest_tl):
        for file in files:
            if file.endswith(".bak") or ".bak" in file or file == ".gitignore":
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

    with open(index_file, "w", encoding="utf-8") as f:
        json.dump(manifest, f, indent=2, ensure_ascii=False)

    print(f"Updated index.json: {len(file_entries)} files indexed (BLAKE3 format).")

if __name__ == "__main__":
    main()
