import requests

DRAMA_ID = "r63qbi2gnxtjvpsaigqpybl0"
SLUG = "perjuangan-pewaris-sejati"
API_BASE = "https://api.shortlovers.id/api"
headers = {"Content-Type": "application/json"}

# Register Episode 1
payload = {
    "dramaId": DRAMA_ID,
    "episodeNumber": 1,
    "title": "Episode 1",
    "videoUrl": f"https://stream.shortlovers.id/netshortv2/{SLUG}/ep001.mp4",
    "videoUrl540p": f"https://stream.shortlovers.id/netshortv2/{SLUG}/ep001_540p.mp4",
    "duration": 0
}

try:
    resp = requests.post(f"{API_BASE}/episodes", headers=headers, json=payload, timeout=30)
    print(f"Register ep001: HTTP {resp.status_code}")
    if resp.status_code in [200, 201]:
        print("Successfully registered!")
    else:
        print(f"Error: {resp.text[:300]}")
except Exception as e:
    print(f"Exception: {e}")

# Update cover to R2
ADMIN_KEY = "00ca04e3e2702be565d7bf44e783255247708289bce9b2fb6187a2e117f87fd14"
NEW_COVER = f"https://stream.shortlovers.id/netshortv2/{SLUG}/cover.webp"

try:
    resp = requests.patch(
        f"{API_BASE}/dramas/{DRAMA_ID}",
        headers={"Content-Type": "application/json", "X-Admin-Key": ADMIN_KEY},
        json={"cover": NEW_COVER}
    )
    print(f"Update cover: HTTP {resp.status_code}")
    if resp.status_code == 200:
        print("Cover updated to R2 successfully!")
    else:
        print(f"Error: {resp.text[:300]}")
except Exception as e:
    print(f"Exception: {e}")
