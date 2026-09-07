#!/usr/bin/env python3
"""Decrypt and query the meta DB for lyrics and storyrace entries."""
import os
import sys
import apsw
import struct

# Add umamusu-utils scripts to path
UTLS = r"G:\Games\steamapps\common\UmamusumePrettyDerby_Jpn\gemini_horses\tools\umamusu-utils\scripts"
sys.path.insert(0, UTLS)

from utils import DB_KEY, DB_BASE_KEY, _derive_decryption_key

META_PATH = r"G:\Games\steamapps\common\UmamusumePrettyDerby_Jpn\UmamusumePrettyDerby_Jpn_Data\Persistent\meta"
DAT_DIR = r"G:\Games\steamapps\common\UmamusumePrettyDerby_Jpn\UmamusumePrettyDerby_Jpn_Data\Persistent\dat"

conn = apsw.Connection(META_PATH)
final_key = _derive_decryption_key(DB_KEY, DB_BASE_KEY)
conn.pragma("cipher", "chacha20")
conn.pragma("hexkey", final_key.hex())
next(conn.cursor().execute("PRAGMA quick_check"))

# Query lyrics
print("=== LYRICS (live/musicscores/*_lyrics%) ===")
lyrics_rows = []
for row in conn.cursor().execute("SELECT n, h, e FROM a WHERE n LIKE 'live/musicscores/%_lyrics%'"):
    lyrics_rows.append(row)
print(f"Total lyrics entries: {len(lyrics_rows)}")
for r in lyrics_rows[:5]:
    print(f"  {r}")

# Query storyrace
print("\n=== STORYRACE (race/storyrace/text/storyrace_%) ===")
storyrace_rows = []
for row in conn.cursor().execute("SELECT n, h, e FROM a WHERE n LIKE 'race/storyrace/text/storyrace_%'"):
    storyrace_rows.append(row)
print(f"Total storyrace entries: {len(storyrace_rows)}")
for r in storyrace_rows[:5]:
    print(f"  {r}")

# Check for ast_ruby variants
print("\n=== AST_RUBY variants ===")
for row in conn.cursor().execute("SELECT n, h, e FROM a WHERE n LIKE 'race/storyrace/text/%' AND n LIKE '%ast_ruby%'"):
    print(f"  {row}")

conn.close()

# Now check which ones exist locally
LOCAL_LYRICS_DIR = r"G:\Games\steamapps\common\UmamusumePrettyDerby_Jpn\gemini_horses\localized_data\assets\lyrics"
LOCAL_STORYRACE_DIR = r"G:\Games\steamapps\common\UmamusumePrettyDerby_Jpn\gemini_horses\localized_data\assets\race\storyrace\text"

local_lyrics = set()
for f in os.listdir(LOCAL_LYRICS_DIR):
    if f.endswith('.json'):
        local_lyrics.add(f)

local_storyrace = set()
for f in os.listdir(LOCAL_STORYRACE_DIR):
    if f.endswith('.json'):
        local_storyrace.add(f)

print(f"\nLocal lyrics count: {len(local_lyrics)}")
print(f"Local storyrace count: {len(local_storyrace)}")

# Map meta n to local filename
# meta: live/musicscores/m1001_lyrics -> local: m1001_lyrics.json
missing_lyrics = []
for n, h, e in lyrics_rows:
    # Extract the music_id name from path like 'live/musicscores/m1001_lyrics'
    parts = n.split('/')
    fname = parts[-1] + '.json'  # m1001_lyrics.json
    if fname not in local_lyrics:
        missing_lyrics.append((n, h, e, fname))

missing_storyrace = []
for n, h, e in storyrace_rows:
    parts = n.split('/')
    fname = parts[-1] + '.json'
    if fname not in local_storyrace:
        missing_storyrace.append((n, h, e, fname))

print(f"\n=== MISSING LYRICS: {len(missing_lyrics)} ===")
for n, h, e, fname in missing_lyrics:
    print(f"  {n}  -> {fname}  hash={h[:16]}...")

print(f"\n=== MISSING STORYRACE: {len(missing_storyrace)} ===")
for n, h, e, fname in missing_storyrace:
    print(f"  {n}  -> {fname}  hash={h[:16]}...")

# Verify dat/{h[:2]}/{h} exists for each
print("\n=== DAT VERIFICATION ===")
all_missing = missing_lyrics + missing_storyrace
dat_found = 0
dat_missing = 0
for n, h, e, fname in all_missing:
    hprefix = h[:2].upper()
    hpath = os.path.join(DAT_DIR, hprefix, h)
    exists = os.path.exists(hpath)
    if exists:
        dat_found += 1
    else:
        dat_missing += 1
        print(f"  MISSING DAT: {hpath} for {fname}")

print(f"Dat found: {dat_found}, Dat missing: {dat_missing}")
