import requests

BACKEND = "https://api.shortlovers.id/api"
DRAMA_ID = "cmleexll8004hhx5e4qx99qtv"
R2_PUBLIC = "https://stream.shortlovers.id"
SLUG = "ahli-pengobatan-sakti"

# Step 1: Shift all existing episodes +1
print("[1/2] Shifting all episodes +1...", end="", flush=True)
r = requests.post(f"{BACKEND}/episodes/shift", json={
    "dramaId": DRAMA_ID,
    "startFrom": 1,
    "shiftBy": 1,
}, timeout=30)

if r.status_code in [200, 201]:
    data = r.json()
    print(f" ✅ {data.get('message', '')}")
else:
    print(f" ❌ HTTP {r.status_code}: {r.text[:200]}")
    exit(1)

# Step 2: Insert new EP1
print("[2/2] Inserting EP1...", end="", flush=True)
ep1_url = f"{R2_PUBLIC}/melolo/{SLUG}/ep001/playlist.m3u8"
r = requests.post(f"{BACKEND}/episodes", json={
    "dramaId": DRAMA_ID,
    "episodeNumber": 1,
    "videoUrl": ep1_url,
    "duration": 62,
    "title": "Episode 1",
}, timeout=15)

if r.status_code in [200, 201]:
    print(f" ✅ EP1 inserted!")
    print(f"  URL: {ep1_url}")
else:
    print(f" ❌ HTTP {r.status_code}: {r.text[:200]}")

# Verify
print("\nVerifying...")
r = requests.get(f"{BACKEND}/dramas/{DRAMA_ID}/episodes", timeout=15)
eps = r.json()
eps.sort(key=lambda x: x.get("episodeNumber", 0))
print(f"  Total episodes: {len(eps)}")
for e in eps[:5]:
    print(f"  EP{e['episodeNumber']}: dur={e['duration']}s, url={e['videoUrl'][-40:]}")
