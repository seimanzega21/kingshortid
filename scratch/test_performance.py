import requests
import time

API_BASE = 'https://api.shortlovers.id'
# Let's test the local server if we want, or the production server.
# Wait, since the production server needs to be deployed first, let's see if we can check the production server response.
# But wait, did we deploy the backend to production yet?
# Let's check how deploy works.

def test_api():
    print("Testing API endpoints...")
    
    # 1. Test Feed endpoint
    start = time.time()
    r = requests.get(f"{API_BASE}/api/dramas/feed?page=1&limit=15", timeout=20)
    duration = time.time() - start
    print(f"Feed Response Status: {r.status_code} | Time taken: {duration:.2f}s")
    if r.ok:
        data = r.json()
        print(f"  Total dramas in feed: {data.get('total', 0)}")
        
    # 2. Test Detail endpoint for Sulijh Suara (62 episodes)
    drama_id = '61746218-8a47-4b2a-85cd-e52a44165db9'
    start = time.time()
    r = requests.get(f"{API_BASE}/api/dramas/{drama_id}", timeout=20)
    duration = time.time() - start
    print(f"Detail Response Status: {r.status_code} | Time taken: {duration:.2f}s")
    if r.ok:
        data = r.json()
        print(f"  Drama Title: {data.get('title')} | Episodes: {len(data.get('episodes', []))}")

if __name__ == "__main__":
    test_api()
