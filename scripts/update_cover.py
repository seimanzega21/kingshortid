import requests

# Update drama cover to R2 URL
DRAMA_ID = "ugg83k4tufn3vmqjtydijhy1"
NEW_COVER = "https://stream.shortlovers.id/netshortv2/manisnya-cinta-tak-sehangat-uang/cover.webp"

API_BASE = "https://api.shortlovers.id/api"
ADMIN_KEY = "00ca04e3e2702be565d7bf44e783255247708289bce9b2fb6187a2e117f87fd14"

resp = requests.patch(
    f"{API_BASE}/dramas/{DRAMA_ID}",
    headers={"Content-Type": "application/json", "X-Admin-Key": ADMIN_KEY},
    json={"cover": NEW_COVER}
)
print(f"Status: {resp.status_code}")
if resp.status_code >= 400:
    print(f"Error: {resp.text}")
else:
    print("Cover updated successfully!")
