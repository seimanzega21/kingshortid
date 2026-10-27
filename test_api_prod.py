import requests

API_BASE = "https://api.shortlovers.id"
ADMIN_KEY = "00ca04e3e2702be565d7bf44e783255247708289bce9b2fb6187a2e117f87fd14"
ADMIN_HDR = {"x-admin-key": ADMIN_KEY, "Content-Type": "application/json"}

print("Testing https://api.shortlovers.id/api/dramas?limit=1...")
r = requests.get(f"{API_BASE}/api/dramas?limit=1", timeout=15)
print("status:", r.status_code)
d = r.json()
print("response:", list(d.keys()) if isinstance(d, dict) else len(d))

print("\nTesting drama creation endpoint with dry/invalid payload...")
r2 = requests.post(f"{API_BASE}/api/admin/dramas", headers=ADMIN_HDR, json={}, timeout=15)
print("admin/dramas status:", r2.status_code, r2.text)
