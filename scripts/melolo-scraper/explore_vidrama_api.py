#!/usr/bin/env python3
"""Explore vidrama.asia Melolo API to get full drama catalog with video URLs."""
import requests, json, time

base = "https://vidrama.asia/api/melolo"

# Step 1: Get a full search to see response shape
print("=== SEARCH RESPONSE SHAPE ===")
r = requests.get(f"{base}?action=search&keyword=a&limit=5&offset=0", timeout=10)
search_data = r.json()
print(json.dumps(search_data, indent=2, ensure_ascii=False)[:3000])

# Step 2: Try detail action with a drama ID
if search_data.get("data"):
    drama_id = search_data["data"][0].get("id")
    print(f"\n\n=== DETAIL for ID={drama_id} ===")
    r2 = requests.get(f"{base}?action=detail&id={drama_id}", timeout=10)
    print(f"Status: {r2.status_code}")
    if r2.status_code == 200:
        detail = r2.json()
        print(json.dumps(detail, indent=2, ensure_ascii=False)[:3000])
    else:
        print(r2.text[:500])
    
    # Step 3: Try stream action
    print(f"\n\n=== STREAM for ID={drama_id} ===")
    r3 = requests.get(f"{base}?action=stream&id={drama_id}", timeout=10)
    print(f"Status: {r3.status_code}")
    if r3.status_code == 200:
        stream = r3.json()
        print(json.dumps(stream, indent=2, ensure_ascii=False)[:3000])
    else:
        print(r3.text[:500])

# Step 4: Get ALL dramas by paginating search
print("\n\n=== GETTING ALL DRAMAS ===")
all_dramas = {}
# Try different keywords to maximize coverage  
for keyword in ["a", "e", "i", "o", "u", "s", "k", "p", "d", "m", "b", "c", "j", "r", "n", "t", "l", "g", "h"]:
    offset = 0
    while True:
        r = requests.get(f"{base}?action=search&keyword={keyword}&limit=50&offset={offset}", timeout=10)
        if r.status_code != 200:
            break
        data = r.json()
        items = data.get("data", [])
        if not items:
            break
        for item in items:
            did = item.get("id", "")
            if did not in all_dramas:
                all_dramas[did] = item
        offset += 50
        if len(items) < 50:
            break
        time.sleep(0.3)
    print(f"  keyword '{keyword}': total unique = {len(all_dramas)}")

print(f"\n  Total unique dramas: {len(all_dramas)}")

# Save full list
with open("vidrama_all_dramas.json", "w", encoding="utf-8") as f:
    json.dump(list(all_dramas.values()), f, indent=2, ensure_ascii=False)
print("  Saved: vidrama_all_dramas.json")

# Print titles
for d in sorted(all_dramas.values(), key=lambda x: x.get("title", "")):
    ep_count = d.get("total_episodes", d.get("episode_count", "?"))
    print(f"  [{d['id']}] {d['title']} ({ep_count} eps)")
