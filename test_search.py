import requests

API_BASE = "https://api.shortlovers.id"
r = requests.get(f"{API_BASE}/api/dramas?search=bajak+laut&limit=10", timeout=15)
print("status:", r.status_code)
d = r.json()
print("total:", d.get("total"))
for drama in d.get("dramas", []):
    print(" -", drama.get("id"), drama.get("title"), drama.get("totalEpisodes"), drama.get("status"), drama.get("isActive"))
