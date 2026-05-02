import requests

API_BASE = 'https://api.shortlovers.id'

# Test coins endpoint (no auth - should return 401 if exists)
r = requests.get(f"{API_BASE}/api/coins/status", timeout=10)
print(f"Coins Status: {r.status_code}")
if r.status_code == 401:
    print("Endpoint EXIST and requires auth - GOOD")
elif r.status_code == 404:
    print("Endpoint NOT FOUND - deployment failed or not yet complete")
else:
    print(f"Response: {r.text[:100]}")

# Test health
r2 = requests.get(f"{API_BASE}/health", timeout=10)
print(f"\nHealth: {r2.status_code}")
if r2.ok:
    print(f"Response: {r2.json()}")
