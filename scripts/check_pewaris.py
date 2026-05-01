import requests

DRAMA_ID = "r63qbi2gnxtjvpsaiqgpyb10"
SLUG = "perjuangan-pewaris-sejati"
API_BASE = "https://api.shortlovers.id/api"

# Check drama detail
resp = requests.get(f"{API_BASE}/dramas/{DRAMA_ID}", timeout=30)
if resp.status_code == 200:
    drama = resp.json()
    print(f"Title: {drama.get('title')}")
    print(f"Cover: {drama.get('cover', 'N/A')[:100]}")
    print(f"Total Episodes: {drama.get('totalEpisodes')}")
    print(f"Episodes count in DB: {len(drama.get('episodes', []))}")
    print(f"isActive: {drama.get('isActive')}")
    
    # Check if episodes are empty
    if not drama.get('episodes'):
        print("\nNo episodes in database.")
        print(f"Checking R2 for ep001...")
        r2_resp = requests.head(f"https://stream.shortlovers.id/netshortv2/{SLUG}/ep001.mp4", timeout=10)
        print(f"ep001 R2 status: {r2_resp.status_code}")
        if r2_resp.status_code == 200:
            print("ep001 exists in R2 but not in DB.")
            print("\n" + "="*60)
            print("SOLUTION: Need to redeploy backend so episode registration works")
            print("OR: Register episodes via admin dashboard manually")
else:
    print(f"Failed to fetch drama: {resp.status_code}")
