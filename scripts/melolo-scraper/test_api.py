import requests

BACKEND = "http://localhost:3001/api"
DID = "cmleexl990000hx5e4pycn1o5"  # 800 Ribu Beli Dunia Kultivasi

# Test POST to /api/dramas/[id]/episodes
payload = {
    "episodeNumber": 999,
    "title": "Test Episode",
    "videoUrl": "https://stream.shortlovers.id/test.mp4",
    "duration": 0,
    "isVip": False,
    "coinPrice": 0,
}
print(f"POST /api/dramas/{DID}/episodes")
r = requests.post(f"{BACKEND}/dramas/{DID}/episodes", json=payload, timeout=10)
print(f"Status: {r.status_code}")
print(f"Response: {r.text[:200]}")

# If created, delete it
if r.status_code in [200, 201]:
    ep_id = r.json().get("id")
    print(f"\nCreated! ID: {ep_id}")
    # Clean up via direct prisma would be ideal, but let's leave it for now
    print("NOTE: Test episode created - will need manual cleanup")
