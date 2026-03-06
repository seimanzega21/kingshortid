import requests

# Check EP1 (ep002) and EP2 (ep003) playlist content
for ep in ["ep002", "ep003"]:
    url = f"https://stream.shortlovers.id/melolo/ahli-pengobatan-sakti/{ep}/playlist.m3u8"
    r = requests.get(url, timeout=10)
    print(f"=== {ep} (HTTP {r.status_code}, {len(r.content)} bytes) ===")
    print(r.text)
    print()

# Check EP1 from Vidrama - get stream URL
r = requests.get("https://vidrama.asia/api/melolo?action=detail&id=7588815593659173941", timeout=15)
eps = r.json()["data"]["episodes"]
print("=== VIDRAMA EP1 ===")
print(f"  videoId: {eps[0]['videoId']}")
print(f"  duration: {eps[0]['duration']}s")
print()
print("=== VIDRAMA EP2 ===")
print(f"  videoId: {eps[1]['videoId']}")
print(f"  duration: {eps[1]['duration']}s")
