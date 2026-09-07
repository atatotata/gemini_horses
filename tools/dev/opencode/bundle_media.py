#!/usr/bin/env python3
"""
Bundle upstream UmaTL media assets into gemini_horses repo.
- Copies matching-hash files from local game assets
- Downloads missing/mismatched files from upstream
- Verifies blake3 hashes for all files
- Updates .upstream_cache.json for freshly downloaded files only
"""
import json
import os
import shutil
import sys
import time
import urllib.request
import urllib.error
import blake3

REPO_ROOT = r"G:\Games\steamapps\common\UmamusumePrettyDerby_Jpn\gemini_horses"
GAME_ASSETS = r"G:\Games\steamapps\common\UmamusumePrettyDerby_Jpn\hachimi\localized_data_1\assets"
UPSTREAM_INDEX_PATH = r"C:\Users\Ota\.local\share\opencode\tool-output\tool_06a440d0400115LbYB98F8zCZl"
CACHE_FILE = os.path.join(REPO_ROOT, ".upstream_cache.json")

def hash_file(data: bytes) -> str:
    return blake3.blake3(data).hexdigest()

def fetch_url(url: str, timeout: int = 60) -> bytes:
    req = urllib.request.Request(
        url,
        headers={"User-Agent": "gemini-horses-sync/1.0 (https://github.com/atatotata/gemini_horses)"}
    )
    with urllib.request.urlopen(req, timeout=timeout) as resp:
        return resp.read()

def get_game_path(upstream_path: str) -> str:
    """Map upstream path to local game asset path."""
    if upstream_path.startswith("assets/"):
        return os.path.join(GAME_ASSETS, upstream_path)
    else:
        # includes_android, includes_win etc. are at localized_data_1 root
        return os.path.join(os.path.dirname(GAME_ASSETS), upstream_path)

def main():
    print("=" * 70)
    print("BUNDLE UPSTREAM MEDIA ASSETS INTO gemini_horses")
    print("=" * 70)

    # 1. Load upstream index
    print("\n[1] Loading upstream index...")
    with open(UPSTREAM_INDEX_PATH, "r", encoding="utf-8") as f:
        upstream_data = json.load(f)
    base_url = upstream_data["base_url"].rstrip("/")
    all_files = upstream_data["files"]

    # Filter to non-json media files
    media_files = [f for f in all_files if not f["path"].endswith(".json")]
    print("  Total upstream files: %d" % len(all_files))
    print("  Non-json media files: %d" % len(media_files))
    total_bytes = sum(f["size"] for f in media_files)
    print("  Total media bytes: %d (%.1f MB)" % (total_bytes, total_bytes / 1024 / 1024))

    # 2. Check USM size
    usm_files = [f for f in media_files if f["path"].endswith(".usm")]
    for u in usm_files:
        print("  USM: %s = %d bytes (%.1f MB)" % (u["path"], u["size"], u["size"] / 1024 / 1024))
        if u["size"] >= 100 * 1024 * 1024:
            print("  *** STOP: USM file >= 100MB (GitHub per-file limit). Aborting. ***")
            sys.exit(2)
    if usm_files:
        print("  USM size OK (< 100MB), continuing.")

    # 3. Load existing cache
    cache = {}
    if os.path.exists(CACHE_FILE):
        with open(CACHE_FILE, "r", encoding="utf-8") as f:
            cache = json.load(f)
    print("\n[2] Cache has %d entries." % len(cache))

    # 4. Process each media file
    copied = 0
    downloaded = 0
    failed = 0
    skipped = 0
    total_added_bytes = 0
    failures = []
    newly_downloaded = {}  # path -> hash for cache update

    print("\n[3] Processing %d media files..." % len(media_files))
    t0 = time.time()

    for i, entry in enumerate(media_files):
        rel_path = entry["path"]
        expected_hash = entry["hash"]
        expected_size = entry["size"]
        target_path = os.path.join(REPO_ROOT, "localized_data", rel_path)
        game_path = get_game_path(rel_path)

        # Ensure target directory exists
        target_dir = os.path.dirname(target_path)
        os.makedirs(target_dir, exist_ok=True)

        # Check if file already exists in target with correct hash
        if os.path.exists(target_path):
            with open(target_path, "rb") as f:
                existing_data = f.read()
            existing_hash = blake3.blake3(existing_data).hexdigest()
            if existing_hash == expected_hash:
                skipped += 1
                continue

        # Try to copy from local game assets
        copied_successfully = False
        if os.path.exists(game_path):
            with open(game_path, "rb") as f:
                game_data = f.read()
            game_hash = blake3.blake3(game_data).hexdigest()
            if game_hash == expected_hash:
                with open(target_path, "wb") as f:
                    f.write(game_data)
                copied += 1
                total_added_bytes += len(game_data)
                copied_successfully = True
            else:
                # Hash mismatch - game asset differs from upstream
                pass

        if not copied_successfully:
            # Download from upstream
            download_url = base_url + "/" + rel_path
            try:
                dl_data = fetch_url(download_url)
                dl_hash = blake3.blake3(dl_data).hexdigest()
                if dl_hash != expected_hash:
                    raise ValueError("Hash mismatch: expected %s, got %s" % (expected_hash, dl_hash))
                with open(target_path, "wb") as f:
                    f.write(dl_data)
                downloaded += 1
                total_added_bytes += len(dl_data)
                newly_downloaded[rel_path] = expected_hash
                if (downloaded % 50) == 0:
                    print("  Downloaded %d files so far..." % downloaded)
            except Exception as e:
                failed += 1
                failures.append((rel_path, str(e)))

        if (i + 1) % 200 == 0:
            elapsed = time.time() - t0
            print("  Progress: %d/%d files (%.0fs elapsed, copied=%d downloaded=%d failed=%d)" % (
                i + 1, len(media_files), elapsed, copied, downloaded, failed))

    elapsed = time.time() - t0
    print("\n  Done processing in %.0f seconds." % elapsed)

    # 5. Summary
    print("\n" + "=" * 70)
    print("RESULTS:")
    print("  Files already in target (skipped): %d" % skipped)
    print("  Files copied from game assets:     %d" % copied)
    print("  Files downloaded from upstream:    %d" % downloaded)
    print("  Total bytes added:                 %d (%.1f MB)" % (total_added_bytes, total_added_bytes / 1024 / 1024))
    print("  Failures:                          %d" % failed)
    if failures:
        print("\n  FAILED FILES:")
        for path, reason in failures[:20]:
            print("    %s: %s" % (path, reason))
        if len(failures) > 20:
            print("    ... and %d more" % (len(failures) - 20))

    # 6. Update .upstream_cache.json for freshly downloaded files only
    if newly_downloaded:
        print("\n[4] Updating .upstream_cache.json for %d newly downloaded files..." % len(newly_downloaded))
        for path, h in newly_downloaded.items():
            cache[path] = h
        with open(CACHE_FILE, "w", encoding="utf-8") as f:
            json.dump(cache, f, indent=2)
        print("  Cache now has %d entries." % len(cache))
    else:
        print("\n[4] No newly downloaded files; cache unchanged.")

    # Write results to a summary file
    summary = {
        "skipped": skipped,
        "copied": copied,
        "downloaded": downloaded,
        "total_added_bytes": total_added_bytes,
        "failures": failures,
        "newly_downloaded_count": len(newly_downloaded),
    }
    with open(os.path.join(REPO_ROOT, "_bundle_summary.json"), "w") as f:
        json.dump(summary, f, indent=2)

    print("\nDone. Exit code: %d" % (1 if failures else 0))
    return 0 if not failures else 1

if __name__ == "__main__":
    sys.exit(main())
