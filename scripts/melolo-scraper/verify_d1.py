#!/usr/bin/env python3
"""Verify D1 drama count and schema."""
import requests, sys
sys.stdout.reconfigure(encoding="utf-8")

BACKEND = "https://api.shortlovers.id/api"

r = requests.get(f"{BACKEND}/dramas?limit=1000", timeout=15)
data = r.json()
items = data if isinstance(data, list) else data.get("dramas", data.get("data", []))
print(f"Total D1 dramas: {len(items)}")
if items:
    print(f"Schema keys: {list(items[0].keys())}")
    print()
    # Show last 25 dramas (most recently added)
    print(f"Last 25 dramas:")
    for d in items[-25:]:
        prov = d.get("provider", d.get("source", "?"))
        print(f"  [{prov}] {d.get('title','?')}")
