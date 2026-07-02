import requests

url = "https://static-aka.cubetv.cc/env_prod/backend/episode/caption/2026052615180668668818.srt"
r = requests.get(url, verify=False, timeout=10)
if r.ok:
    print("SRT Content (first 300 chars):")
    print(r.text[:300])
else:
    print("Failed to download:", r.status_code)
