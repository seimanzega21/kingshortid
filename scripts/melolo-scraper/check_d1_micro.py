#!/usr/bin/env python3
"""Check D1 microdrama registration status."""
import requests, sys
sys.stdout.reconfigure(encoding="utf-8")

BACKEND = "https://api.shortlovers.id/api"

r = requests.get(f"{BACKEND}/dramas?limit=1000", timeout=15)
data = r.json()
items = data if isinstance(data, list) else data.get("dramas", data.get("data", []))
d1_micro = [d for d in items if d.get("provider") == "microdrama"]
print(f"D1 microdrama dramas: {len(d1_micro)}")
for d in d1_micro:
    print(f"  - {d['title']} (id={d.get('id','?')})")
