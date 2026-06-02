import requests

API_BASE = 'https://api.shortlovers.id/api'
ADMIN_KEY = '00ca04e3e2702be565d7bf44e783255247708289bce9b2fb6187a2e117f87fd14'
ADMIN_HDR = {'x-admin-key': ADMIN_KEY, 'Content-Type': 'application/json'}

print("Fetching dramas from Supabase...")
r = requests.get(f"{API_BASE}/dramas?limit=1000&includeInactive=true", headers=ADMIN_HDR, timeout=20)
if not r.ok:
    print(f"Failed to fetch dramas: {r.status_code}")
    exit(1)

dramas = r.json()
if isinstance(dramas, dict):
    dramas = dramas.get('dramas', [])

print(f"Total dramas in DB: {len(dramas)}")

# Filter microdrama dramas using cover path as a heuristic
micro_dramas = [d for d in dramas if d.get("cover") and "/microdrama/" in d.get("cover")]
print(f"Total Microdrama dramas (detected via cover path): {len(micro_dramas)}")

empty_dramas = []

for i, d in enumerate(micro_dramas, 1):
    did = d["id"]
    title = d["title"]
    
    # Get drama details to see registered episodes count
    r_detail = requests.get(f"{API_BASE}/dramas/{did}?includeInactive=true", headers=ADMIN_HDR, timeout=15)
    if r_detail.ok:
        detail_data = r_detail.json()
        eps = detail_data.get("episodes", [])
        actual_eps_count = len(eps)
        expected_eps_count = d.get("totalEpisodes", 0)
        is_active = d.get("isActive", False)
        
        if actual_eps_count == 0:
            empty_dramas.append({
                "id": did,
                "title": title,
                "expected": expected_eps_count,
                "isActive": is_active
            })
            print(f"  [{i}/{len(micro_dramas)}] EMPTY: '{title}' (ID: {did}) | Expected: {expected_eps_count} | isActive: {is_active}")
    else:
        print(f"  [{i}/{len(micro_dramas)}] Failed to get details for '{title}'")

print("\n" + "=" * 60)
print(f"Total empty Microdrama dramas found: {len(empty_dramas)}")
for ed in empty_dramas:
    print(f"- {ed['title']} (ID: {ed['id']}) | Expected: {ed['expected']} | isActive: {ed['isActive']}")
print("=" * 60)
