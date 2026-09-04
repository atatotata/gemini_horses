#!/usr/bin/env python3
"""
sync_umatl.py

Gracefully synchronizes and overlays curated human translations from upstream
UmaTL (hachimi-tl-en-sd) on top of the gemini_horses base repository.

Precedence hierarchy:
  1. Upstream UmaTL human translations (curated, highest priority - overwrites MT)
  2. Local Gemini 3.7 Flash Voice-Aware MT (covers 33K+ master strings & 1,167 support stories)
  3. Original Japanese text

Workflow:
  - Fetches upstream UmaTL index.json (list of {path, hash, size})
  - Checks for updated files using cached upstream BLAKE3 hashes
  - Deep-merges dictionary tables (text_data_dict, character_system_text_dict, localize_dict, etc.)
  - Directly replaces story / home timelines and texture diffs that UmaTL has curated
  - Leaves our machine-translated support card stories & master strings untouched if UmaTL lacks them
  - Automatically regenerates index.json manifest in official Hachimi BLAKE3 schema
"""

import os
import sys
import json
import pathlib
import argparse
import urllib.request
import urllib.error

try:
    import blake3
    def hash_file(data: bytes) -> str:
        return blake3.blake3(data).hexdigest()
except ImportError:
    import hashlib
    def hash_file(data: bytes) -> str:
        return hashlib.sha256(data).hexdigest()

DEFAULT_UPSTREAM_INDEX = "https://raw.githubusercontent.com/UmaTL/hachimi-tl-en-sd/release/index.json"
CACHE_FILE = ".upstream_cache.json"

DICT_FILES = {
    "text_data_dict.json",
    "character_system_text_dict.json",
    "localize_dict.json",
    "hashed_dict.json",
    "race_jikkyo_comment_dict.json",
    "race_jikkyo_message_dict.json",
}

def fetch_url(url: str, timeout: int = 45) -> bytes:
    req = urllib.request.Request(
        url,
        headers={"User-Agent": "gemini-horses-sync/1.0 (https://github.com/Otattemita/gemini_horses)"}
    )
    with urllib.request.urlopen(req, timeout=timeout) as resp:
        return resp.read()

def merge_text_data_dict(local_data: dict, upstream_data: dict) -> tuple[int, int]:
    """Overwrites local text_data_dict with upstream curated entries."""
    updated = 0
    added = 0
    for cat, entries in upstream_data.items():
        cat_str = str(cat)
        if cat_str not in local_data:
            local_data[cat_str] = {}
        for idx, text in entries.items():
            idx_str = str(idx)
            if text and str(text).strip():
                if idx_str in local_data[cat_str]:
                    if local_data[cat_str][idx_str] != text:
                        local_data[cat_str][idx_str] = text
                        updated += 1
                else:
                    local_data[cat_str][idx_str] = text
                    added += 1
    return updated, added

def merge_cst_dict(local_data: dict, upstream_data: dict) -> tuple[int, int]:
    """Overwrites local character_system_text_dict with upstream curated entries."""
    updated = 0
    added = 0
    for char_id, voice_entries in upstream_data.items():
        char_str = str(char_id)
        if char_str not in local_data:
            local_data[char_str] = {}
        for voice_id, text in voice_entries.items():
            v_str = str(voice_id)
            if text and str(text).strip():
                if v_str in local_data[char_str]:
                    if local_data[char_str][v_str] != text:
                        local_data[char_str][v_str] = text
                        updated += 1
                else:
                    local_data[char_str][v_str] = text
                    added += 1
    return updated, added

def merge_flat_dict(local_data: dict, upstream_data: dict) -> tuple[int, int]:
    """Overwrites flat string dictionaries."""
    updated = 0
    added = 0
    for k, v in upstream_data.items():
        if v and str(v).strip():
            if k in local_data:
                if local_data[k] != v:
                    local_data[k] = v
                    updated += 1
            else:
                local_data[k] = v
                added += 1
    return updated, added

def update_index_manifest(dest_tl: pathlib.Path, index_file: pathlib.Path) -> int:
    """Regenerates index.json using the official Hachimi list schema."""
    base_url = "https://raw.githubusercontent.com/Otattemita/gemini_horses/main/localized_data"
    if index_file.exists():
        try:
            with open(index_file, "r", encoding="utf-8") as f:
                old_idx = json.load(f)
                base_url = old_idx.get("base_url", base_url)
        except Exception:
            pass

    file_entries = []
    for root, _, files in os.walk(dest_tl):
        for file in files:
            if file.endswith(".bak") or ".bak" in file or file == ".gitignore":
                continue
            fpath = pathlib.Path(root) / file
            rel_path = fpath.relative_to(dest_tl).as_posix()
            data = fpath.read_bytes()
            file_entries.append({
                "path": rel_path,
                "hash": hash_file(data),
                "size": len(data)
            })

    file_entries.sort(key=lambda x: x["path"])

    manifest = {
        "base_url": base_url,
        "files": file_entries
    }

    with open(index_file, "w", encoding="utf-8") as f:
        json.dump(manifest, f, indent=2, ensure_ascii=False)
    return len(file_entries)

def parse_upstream_files(raw_files) -> dict[str, str]:
    """Normalizes upstream files list-or-dict to {path: hash}."""
    res = {}
    if isinstance(raw_files, list):
        for item in raw_files:
            if isinstance(item, dict) and "path" in item and "hash" in item:
                res[item["path"]] = item["hash"]
    elif isinstance(raw_files, dict):
        for k, v in raw_files.items():
            if isinstance(v, dict) and "hash" in v:
                res[k] = v["hash"]
            else:
                res[k] = str(v)
    return res

def main():
    parser = argparse.ArgumentParser(description="Sync and overlay UmaTL upstream translations onto gemini_horses.")
    parser.add_argument("--upstream-url", default=DEFAULT_UPSTREAM_INDEX, help="URL to upstream index.json")
    parser.add_argument("--force", action="store_true", help="Force check and download of all files regardless of cache")
    parser.add_argument("--dry-run", action="store_true", help="Report potential changes without writing to disk")
    args = parser.parse_args()

    repo_root = pathlib.Path(__file__).parent.resolve()
    dest_tl = repo_root / "localized_data"
    index_file = repo_root / "index.json"
    cache_path = repo_root / CACHE_FILE

    print("=" * 60)
    print("UmaTL Upstream Synchronization & Overlay")
    print(f"Target repo root: {repo_root}")
    print(f"Upstream index:   {args.upstream_url}")
    print("=" * 60)

    # 1. Load upstream index
    try:
        print("Fetching upstream index.json...")
        raw_idx = fetch_url(args.upstream_url)
        upstream_index = json.loads(raw_idx.decode("utf-8"))
    except Exception as e:
        print(f"Error fetching upstream index: {e}", file=sys.stderr)
        sys.exit(1)

    upstream_base_url = upstream_index.get("base_url", "").rstrip("/")
    raw_files = upstream_index.get("files", [])
    upstream_file_map = parse_upstream_files(raw_files)
    print(f"Upstream reports {len(upstream_file_map)} files at {upstream_base_url}")

    # 2. Load cache
    cache = {}
    if not args.force and cache_path.exists():
        try:
            with open(cache_path, "r", encoding="utf-8") as f:
                cache = json.load(f)
        except Exception:
            cache = {}

    # 3. Detect changes
    changed_files = []
    for rel_path, up_hash in upstream_file_map.items():
        if args.force or cache.get(rel_path) != up_hash:
            changed_files.append((rel_path, up_hash))

    if not changed_files:
        print("\nAll upstream files are already up-to-date with local overlay. No changes needed.")
        return

    print(f"\nDetected {len(changed_files)} upstream files with updates or new additions.")
    if args.dry_run:
        print("[Dry Run] Sample of files to be updated:")
        for rel_path, _ in changed_files[:20]:
            print(f"  - {rel_path}")
        if len(changed_files) > 20:
            print(f"  ... and {len(changed_files) - 20} more.")
        return

    # 4. Process files
    dict_stats = {}
    timelines_updated = 0
    other_assets_updated = 0
    errors = 0

    for i, (rel_path, up_hash) in enumerate(changed_files, 1):
        file_url = f"{upstream_base_url}/{rel_path}"
        target_path = dest_tl / rel_path

        try:
            content_bytes = fetch_url(file_url)
        except Exception as e:
            print(f"  [{i}/{len(changed_files)}] Failed to fetch {rel_path}: {e}")
            errors += 1
            continue

        target_path.parent.mkdir(parents=True, exist_ok=True)

        if rel_path in DICT_FILES:
            # Deep merge dictionary
            try:
                up_json = json.loads(content_bytes.decode("utf-8"))
                local_json = {}
                if target_path.exists():
                    with open(target_path, "r", encoding="utf-8") as f:
                        local_json = json.load(f)

                if rel_path == "text_data_dict.json":
                    upd, add = merge_text_data_dict(local_json, up_json)
                elif rel_path == "character_system_text_dict.json":
                    upd, add = merge_cst_dict(local_json, up_json)
                else:
                    upd, add = merge_flat_dict(local_json, up_json)

                dict_stats[rel_path] = (upd, add)
                with open(target_path, "w", encoding="utf-8") as f:
                    json.dump(local_json, f, ensure_ascii=False, indent=2)

                print(f"  [{i}/{len(changed_files)}] Merged {rel_path}: {upd} updated, {add} added")
                cache[rel_path] = up_hash
            except Exception as e:
                print(f"  [{i}/{len(changed_files)}] Error merging dict {rel_path}: {e}")
                errors += 1
        else:
            # Directly overwrite asset / timeline with upstream curated version
            try:
                target_path.write_bytes(content_bytes)
                if "storytimeline_" in rel_path or "hometimeline_" in rel_path:
                    timelines_updated += 1
                else:
                    other_assets_updated += 1
                cache[rel_path] = up_hash
            except Exception as e:
                print(f"  [{i}/{len(changed_files)}] Error writing {rel_path}: {e}")
                errors += 1

        if i % 100 == 0 or i == len(changed_files):
            print(f"  Progress: {i}/{len(changed_files)} files processed...")

    # 5. Save updated cache
    with open(cache_path, "w", encoding="utf-8") as f:
        json.dump(cache, f, indent=2)

    # 6. Rebuild index.json manifest
    print("\nRegenerating index.json manifest...")
    total_indexed = update_index_manifest(dest_tl, index_file)

    print("\n" + "=" * 60)
    print("Sync Summary:")
    for dname, (upd, add) in dict_stats.items():
        print(f"  - {dname}: {upd} keys replaced, {add} new keys added")
    print(f"  - Timelines updated: {timelines_updated}")
    print(f"  - Other assets (textures, etc.) updated: {other_assets_updated}")
    print(f"  - Total files currently in index.json: {total_indexed}")
    if errors:
        print(f"  - Warnings/Errors: {errors}")
    print("=" * 60)

if __name__ == "__main__":
    main()
