#!/usr/bin/env python3
"""Test UnityPy extraction on one lyrics bundle to understand structure."""
import os
import json
import UnityPy

DAT_DIR = r"G:\Games\steamapps\common\UmamusumePrettyDerby_Jpn\UmamusumePrettyDerby_Jpn_Data\Persistent\dat"

# Test on first missing lyrics: m1005, hash=YZDYNUGJ7H7JV2SKT7US4JMIGWRBITMQ
h = "YZDYNUGJ7H7JV2SKT7US4JMIGWRBITMQ"
bundle_path = os.path.join(DAT_DIR, h[:2].upper(), h)
print(f"Loading: {bundle_path}")
print(f"Exists: {os.path.exists(bundle_path)}")
print(f"Size: {os.path.getsize(bundle_path)} bytes")

env = UnityPy.load(bundle_path)

for obj in env.objects:
    print(f"  Object: type={obj.type.name} path_id={obj.path_id}")
    if obj.type.name == "MonoBehaviour":
        try:
            tree = obj.read_typetree()
            if tree:
                print(f"    Typetree keys: {list(tree.keys()) if isinstance(tree, dict) else type(tree)}")
                if isinstance(tree, dict):
                    for k, v in tree.items():
                        if isinstance(v, str):
                            print(f"      {k}: {v[:100]}")
                        elif isinstance(v, list):
                            print(f"      {k}: list of {len(v)} items")
                            if len(v) > 0:
                                print(f"        first: {v[0]}")
                        elif isinstance(v, dict):
                            print(f"      {k}: dict with keys {list(v.keys())[:10]}")
                        else:
                            print(f"      {k}: {type(v).__name__} = {v}")
        except Exception as e:
            print(f"    Error reading typetree: {e}")
    elif obj.type.name in ('AssetBundle', 'TextAsset'):
        try:
            data = obj.read()
            print(f"    name={getattr(data, 'name', '?')} path={getattr(data, 'path_id', '?')}")
        except Exception as e:
            print(f"    Error: {e}")
