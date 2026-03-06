#!/usr/bin/env python3
"""Check episode count for Ciuman Pengakuan Manis from Vidrama API."""
import requests, json

VIDRAMA_ID = "7562087033263361029"
API_URL = "https://vidrama.asia/api/melolo"

print("=== Checking Vidrama API ===")
r = requests.get(f"{API_URL}?action=detail&id={VIDRAMA_ID}", timeout=15)
data = r.json().get("data", {})
episodes = data.get("episodes", [])
print(f"Title: {data.get('title', 'N/A')}")
print(f"Total episodes from Vidrama: {len(episodes)}")
for ep in episodes:
    print(f"  Ep {ep.get('episodeNumber', 0)}: duration={ep.get('duration', 0)}")

# Also check our backend (Cloudflare Worker)
print("\n=== Checking Backend API ===")
WORKER_URL = "https://kingshort-api.seimanzega21.workers.dev/api"
try:
    r2 = requests.get(f"{WORKER_URL}/dramas?limit=500", timeout=10)
    if r2.status_code == 200:
        resp = r2.json()
        dramas = resp if isinstance(resp, list) else resp.get("dramas", [])
        found = [d for d in dramas if "Ciuman Pengakuan" in d.get("title", "")]
        if found:
            drama = found[0]
            print(f"Found in DB: {drama['title']} (ID: {drama.get('id', 'N/A')})")
            print(f"Total episodes in DB: {drama.get('totalEpisodes', 'N/A')}")
            # Get episodes
            drama_id = drama.get("id")
            if drama_id:
                r3 = requests.get(f"{WORKER_URL}/dramas/{drama_id}/episodes", timeout=10)
                if r3.status_code == 200:
                    db_eps = r3.json()
                    if isinstance(db_eps, dict):
                        db_eps = db_eps.get("episodes", [])
                    print(f"Episodes in DB: {len(db_eps)}")
                    for ep in db_eps:
                        print(f"  Ep {ep.get('episodeNumber', 'N/A')}: {ep.get('videoUrl', 'N/A')[:80]}")
        else:
            print("NOT found in DB!")
            # Search with different terms
            for d in dramas:
                if "ciuman" in d.get("title", "").lower():
                    print(f"  Similar: {d['title']} (ID: {d.get('id', 'N/A')})")
    else:
        print(f"Backend error: {r2.status_code}")
except Exception as e:
    print(f"Backend error: {e}")
