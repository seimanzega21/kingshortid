#!/usr/bin/env python3
"""Save full detail API response to examine structure."""
import requests, sys, json
sys.stdout.reconfigure(encoding="utf-8")

DRAMA_ID = "2026565395272769537"  # Istri Dokter Masa Depan Pembawa Hoki

# Try detail without lang first (worked with English drama earlier returning episodes)
r = requests.get(f"https://vidrama.asia/api/microdrama?action=detail&id={DRAMA_ID}", timeout=15)
data = r.json()
with open("detail_id_drama.json", "w", encoding="utf-8") as f:
    json.dump(data, f, indent=2, ensure_ascii=False)

drama = data.get("drama", {})
print(f"Keys: {list(drama.keys())}")
print(f"total_episodes: {drama.get('total_episodes', '?')}")
eps = drama.get("episodes", [])
print(f"episodes[] count: {len(eps)}")

# Print first episode if any
if eps:
    print(f"Episode 1: {json.dumps(eps[0], indent=2)[:300]}")
else:
    # Check any nested keys
    for k, v in drama.items():
        if isinstance(v, list) and len(v) > 0:
            print(f"  List field '{k}': {len(v)} items")
            print(f"    First item keys: {list(v[0].keys()) if isinstance(v[0], dict) else type(v[0])}")
