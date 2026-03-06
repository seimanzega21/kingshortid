#!/usr/bin/env python3
"""Quick test of backend API payload format."""
import requests, sys
sys.stdout.reconfigure(encoding="utf-8")

BACKEND = "https://api.shortlovers.id/api"

# 1. Check existing dramas and their schema
r = requests.get(f"{BACKEND}/dramas?limit=3&offset=0", timeout=10)
print(f"GET /dramas: {r.status_code}")
data = r.json()
items = data if isinstance(data, list) else data.get("dramas", data.get("data", []))
if items:
    d = items[0]
    keys = list(d.keys())
    print(f"Drama keys: {keys}")
    print(f"Provider sample: {d.get('provider','?')}")
    print(f"Cover sample: {d.get('cover','?')[:60]}")
print()

# 2. Check POST schema accepted
payload = {
    "title": "TES REGISTRASI",
    "description": "Drama test",
    "cover": "https://stream.shortlovers.id/microdrama/test/cover.webp",
    "provider": "microdrama",
    "totalEpisodes": 5,
    "isActive": True,
}
r2 = requests.post(f"{BACKEND}/dramas", json=payload, timeout=10)
print(f"POST /dramas: {r2.status_code}")
print(f"Response: {r2.text[:200]}")

if r2.status_code in [200, 201]:
    drama_id = r2.json().get("id")
    print(f"Created drama id: {drama_id}")

    # Test episode
    r3 = requests.post(f"{BACKEND}/episodes", json={
        "dramaId": drama_id,
        "episodeNumber": 1,
        "videoUrl": "https://stream.shortlovers.id/microdrama/test/ep001.mp4",
        "duration": 0,
    }, timeout=10)
    print(f"POST /episodes: {r3.status_code}")
    print(f"Response: {r3.text[:100]}")

    # Cleanup - delete test drama
    rd = requests.delete(f"{BACKEND}/dramas/{drama_id}", timeout=10)
    print(f"DELETE test drama: {rd.status_code}")
