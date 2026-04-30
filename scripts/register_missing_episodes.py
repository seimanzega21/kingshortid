import requests
import json

API_BASE = "https://api.shortlovers.id/api"
DRAMA_ID = "ugg83k4tufn3vmqjtydijhy1"
SLUG = "manisnya-cinta-tak-sehangat-uang"

headers = {"Content-Type": "application/json"}

success = 0
failed = 0

for i in range(45, 71):
    ep_str = f"{i:03d}"
    payload = {
        "dramaId": DRAMA_ID,
        "episodeNumber": i,
        "title": f"Episode {i}",
        "videoUrl": f"https://stream.shortlovers.id/netshortv2/{SLUG}/ep{ep_str}.mp4",
        "videoUrl540p": f"https://stream.shortlovers.id/netshortv2/{SLUG}/ep{ep_str}_540p.mp4",
        "duration": 0
    }
    
    try:
        resp = requests.post(f"{API_BASE}/episodes", headers=headers, json=payload, timeout=30)
        if resp.status_code in [200, 201]:
            print(f"[OK] Episode {i} registered")
            success += 1
        else:
            print(f"[FAIL] Episode {i}: HTTP {resp.status_code} — {resp.text[:200]}")
            failed += 1
    except Exception as e:
        print(f"[ERROR] Episode {i}: {e}")
        failed += 1

print(f"\nDone! Success: {success}, Failed: {failed}")
