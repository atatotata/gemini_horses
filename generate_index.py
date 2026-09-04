import os
import hashlib
import json
import pathlib
import sys

def main():
    repo_root = pathlib.Path(__file__).parent.resolve()
    dest_tl = repo_root / "localized_data"
    index_file = repo_root / "index.json"

    # Read existing base_url if present
    base_url = "https://raw.githubusercontent.com/Otattemita/gemini_horses/main/localized_data"
    if index_file.exists():
        try:
            with open(index_file, "r", encoding="utf-8") as f:
                old_idx = json.load(f)
                base_url = old_idx.get("base_url", base_url)
        except Exception:
            pass

    manifest = {
        "base_url": base_url,
        "files": {}
    }

    for root, dirs, files in os.walk(dest_tl):
        for file in files:
            if file.endswith(".bak") or ".bak" in file:
                continue
            fpath = pathlib.Path(root) / file
            rel_path = fpath.relative_to(dest_tl).as_posix()
            sha256 = hashlib.sha256(fpath.read_bytes()).hexdigest()
            manifest["files"][rel_path] = sha256

    with open(index_file, "w", encoding="utf-8") as f:
        json.dump(manifest, f, indent=2, ensure_ascii=False)

    print(f"Updated index.json: {len(manifest['files'])} files indexed.")

if __name__ == "__main__":
    main()
