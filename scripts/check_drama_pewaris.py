import requests

# Register Episode 1 which exists in R2
DRAMA_ID = "r63qbi2gnxtjvpsaiqgpyb10"
SLUG = "perjuangan-pewaris-sejati"
API_BASE = "https://api.shortlovers.id/api"
headers = {"Content-Type": "application/json"}

# Check if any file exists for episodes 2-5 for debugging
for i in range(1, 6):
    ep_str = f"{i:03d}"
    url = f"https://stream.shortlovers.id/netshortv2/{SLUG}/ep{ep_str}.mp4"
    try:
        r = requests.head(url, timeout=5)
        print(f"ep{ep_str}: HTTP {r.status_code}")
    except Exception as e:
        print(f"ep{ep_str}: FAIL {e}")

print("\n" + "="*60)
print("Only ep001 exists. Registering it now...")

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
    print(f"Status: {resp.status_code}")
    if resp.status_code in [200, 201]:
        print("Episode 1 registered successfully!")
    else:
        print(f"Error: {resp.text[:300]}")
except Exception as e:
    print(f"Request failed: {e}")

print("\n" + "="*60)
print("For episodes 2-64, the video files do NOT exist in R2 yet.")
print("You need to re-run the scraper (scripts/scrape_netshortv2.py)")
print("Drama ID: r63qbi2gnxtjvpsaiqgpyb10")
print("URL hint: https://vidrama.asia/movie/perjuangan-pewaris-sejati")
