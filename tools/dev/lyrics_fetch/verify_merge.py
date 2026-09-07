#!/usr/bin/env python3
"""Verify translated files are actually translated and repos identical."""
import json, sys, os
sys.stdout.reconfigure(encoding='utf-8')

lyrics_dir = r'G:\Games\steamapps\common\UmamusumePrettyDerby_Jpn\gemini_horses\localized_data\assets\lyrics'
sr_dir = r'G:\Games\steamapps\common\UmamusumePrettyDerby_Jpn\gemini_horses\localized_data\assets\race\storyrace\text'
h_lyrics_dir = r'G:\Games\steamapps\common\UmamusumePrettyDerby_Jpn\hachimi\localized_data_1\assets\lyrics'
h_sr_dir = r'G:\Games\steamapps\common\UmamusumePrettyDerby_Jpn\hachimi\localized_data_1\assets\race\storyrace\text'

def has_jp(text):
    return any(0x3040 <= ord(c) <= 0x9fff for c in text)

# New files to check
new_lyrics = ['m1005_lyrics.json', 'm1007_lyrics.json', 'm1010_lyrics.json', 'm1156_lyrics.json', 'm1193_lyrics.json', 'm3193_lyrics.json']
print("=== NEW LYRICS SAMPLES ===")
for f in new_lyrics:
    path = os.path.join(lyrics_dir, f)
    data = json.load(open(path, 'r', encoding='utf-8'))
    vals = list(data.values())
    non_empty = [v for v in vals if v.strip()]
    jp = sum(1 for v in non_empty if has_jp(v))
    en = len(non_empty) - jp
    sample = vals[1][:80] if len(vals) > 1 else "empty"
    print(f"  {f}: {len(vals)} entries, {en} EN / {jp} JP | {sample}")
    # Verify hachimi identical
    h_path = os.path.join(h_lyrics_dir, f)
    with open(path, 'rb') as gf, open(h_path, 'rb') as hf:
        identical = gf.read() == hf.read()
    print(f"    gemini==hachimi: {identical}")

print("\n=== STORYRACE ===")
sr_path = os.path.join(sr_dir, 'storyrace_020290011.json')
data = json.load(open(sr_path, 'r', encoding='utf-8'))
jp = sum(1 for v in data if has_jp(v))
en = len(data) - jp
print(f"  storyrace_020290011: {len(data)} entries, {en} EN / {jp} JP")
for i, line in enumerate(data):
    print(f"    [{i}]: {line[:100]}")
h_path = os.path.join(h_sr_dir, 'storyrace_020290011.json')
with open(sr_path, 'rb') as gf, open(h_path, 'rb') as hf:
    print(f"  gemini==hachimi: {gf.read() == hf.read()}")

print("\n=== FINAL COUNTS ===")
g_lyrics = len([f for f in os.listdir(lyrics_dir) if f.endswith('.json')])
h_lyrics = len([f for f in os.listdir(h_lyrics_dir) if f.endswith('.json')])
g_sr = len([f for f in os.listdir(sr_dir) if f.endswith('.json')])
h_sr = len([f for f in os.listdir(h_sr_dir) if f.endswith('.json')])
print(f"  Lyrics: gemini={g_lyrics} hachimi={h_lyrics}")
print(f"  Storyrace: gemini={g_sr} hachimi={h_sr}")

# File-level identity check
g_lyrics_set = set(f for f in os.listdir(lyrics_dir) if f.endswith('.json'))
h_lyrics_set = set(f for f in os.listdir(h_lyrics_dir) if f.endswith('.json'))
only_g = g_lyrics_set - h_lyrics_set
only_h = h_lyrics_set - g_lyrics_set
print(f"  Lyrics only in gemini: {only_g or 'none'}")
print(f"  Lyrics only in hachimi: {only_h or 'none'}")

g_sr_set = set(f for f in os.listdir(sr_dir) if f.endswith('.json'))
h_sr_set = set(f for f in os.listdir(h_sr_dir) if f.endswith('.json'))
only_g_sr = g_sr_set - h_sr_set
only_h_sr = h_sr_set - g_sr_set
print(f"  Storyrace only in gemini: {only_g_sr or 'none'}")
print(f"  Storyrace only in hachimi: {only_h_sr or 'none'}")

# Content identity for new files
print("\n=== CONTENT IDENTITY (new files only) ===")
all_new = new_lyrics + ['storyrace_020290011.json']
for f in all_new:
    if '_lyrics' in f:
        gp = os.path.join(lyrics_dir, f)
        hp = os.path.join(h_lyrics_dir, f)
    else:
        gp = os.path.join(sr_dir, f)
        hp = os.path.join(h_sr_dir, f)
    with open(gp, 'rb') as gf, open(hp, 'rb') as hf:
        match = gf.read() == hf.read()
    print(f"  {f}: {'IDENTICAL' if match else 'MISMATCH!'}")

# Checkpoint stats
ckpt = json.load(open(r'C:\TMP\lyrics_fetch\lyrics_translation_checkpoint.json', 'r', encoding='utf-8'))
print(f"\n=== CHECKPOINT: {len(ckpt)} entries ===")
