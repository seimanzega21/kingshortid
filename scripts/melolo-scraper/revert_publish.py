import requests
import datetime
import time

API_URL = "https://api.shortlovers.id/api"

# Get new dramas (recently activated ones have their createdAt bumped)
print("Fetching recently activated dramas...")
r = requests.get(f"{API_URL}/dramas/new?limit=100")
data = r.json()

if not isinstance(data, list):
    print("Failed to fetch data:", data)
    exit(1)

# Filter for dramas updated today
now = datetime.datetime.utcnow()
reverted_count = 0

for drama in data:
    # If it was created/updated in the last 12 hours, it's highly likely part of the bulk publish
    # Let's just look at createdAt timestamp (which was bumped to new Date())
    created_at_iso = drama.get("createdAt")
    if not created_at_iso:
        continue
        
    try:
        # Assuming ISO format like '2026-04-26T12:00:00.000Z'
        created_dt = datetime.datetime.fromisoformat(created_at_iso.replace('Z', '+00:00')).replace(tzinfo=None)
        time_diff = now - created_dt
        
        # If created/activated in the last 2 hours
        if time_diff.total_seconds() < 7200:
            print(f"Reverting: {drama.get('title')}")
            # Patch to set isActive = False
            patch_url = f"{API_URL}/dramas/{drama['id']}"
            resp = requests.patch(patch_url, json={"isActive": False})
            if resp.status_code == 200:
                print(f"  -> SUCCESS")
                reverted_count += 1
            else:
                print(f"  -> FAILED: {resp.status_code}")
                
            time.sleep(0.1) # tiny delay
    except Exception as e:
        print(f"Error parsing date for {drama.get('title')}: {e}")

print(f"\nDone! Reverted {reverted_count} dramas back to pending.")
