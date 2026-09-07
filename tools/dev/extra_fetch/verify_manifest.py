#!/usr/bin/env python3
"""Verify manifest."""
import json
with open(r'C:\TMP\extra_fetch\cdn_fetch_09.json', 'r', encoding='utf-8') as f:
    data = json.load(f)
print(f"total: {data['total']}")
print(f"extracted_ok: {data['extracted_ok']}")
print(f"extract_errors: {data['extract_errors']}")
print(f"not_found_404: {data['not_found_404']}")
print(f"download_failed: {data['download_failed']}")
print(f"total_blocks: {data['total_blocks']}")
print(f"total_choices: {data['total_choices']}")
print(f"seasonal_files: {data['seasonal_files']}")
print(f"event_09_files: {data['event_09_files']}")
print(f"combined_expected: {data['combined_expected']}")
statuses = set(t['status'] for t in data['tasks'])
print(f"unique statuses: {statuses}")
blocks = [t['blocks'] for t in data['tasks']]
print(f"blocks range: {min(blocks)}-{max(blocks)}, avg: {sum(blocks)/len(blocks):.1f}")
has_choices = [t for t in data['tasks'] if t['choices'] > 0]
print(f"tasks with choices: {len(has_choices)}")
for t in has_choices:
    print(f"  SID {t['sid']}: {t['choices']} choices")
