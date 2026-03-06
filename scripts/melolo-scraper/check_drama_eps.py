#!/usr/bin/env python3
"""Check episode count in DB for a specific drama."""
import requests

DRAMA_ID = "cmlm8nqu003hnszsa33yv6r0h"
API = "http://localhost:3001/api"

# Get drama detail with episodes
r = requests.get(f"{API}/dramas/{DRAMA_ID}")
d = r.json()

print(f"Title: {d.get('title')}")
print(f"totalEpisodes field: {d.get('totalEpisodes')}")
print(f"Status: {d.get('status')}")

eps = d.get("episodes", [])
print(f"Episodes in DB: {len(eps)}")

if eps:
    for e in sorted(eps, key=lambda x: x.get("episodeNumber", 0)):
        num = e.get("episodeNumber", "?")
        url = e.get("videoUrl", "")
        print(f"  EP{num:3d} → {url[:60]}...")
