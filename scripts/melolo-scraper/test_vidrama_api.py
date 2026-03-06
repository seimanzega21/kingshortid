#!/usr/bin/env python3
"""Focused API test: search + detail + stream on vidrama.asia."""
import requests, json, sys

base = "https://vidrama.asia/api/melolo"

# 1) Search - get first 5 dramas and full response shape
print("=== SEARCH (keyword='a', limit=3) ===\n")
r = requests.get(f"{base}?action=search&keyword=a&limit=3&offset=0", timeout=15)
search = r.json()
print(json.dumps(search, indent=2, ensure_ascii=False))

if not search.get("data"):
    print("No data!")
    sys.exit()

drama = search["data"][0]
drama_id = drama["id"]
print(f"\n\n=== DETAIL for drama ID: {drama_id} ===\n")

# 2) Detail
r2 = requests.get(f"{base}?action=detail&id={drama_id}", timeout=15)
print(f"Status: {r2.status_code}")
detail = r2.json() if r2.status_code == 200 else r2.text
print(json.dumps(detail, indent=2, ensure_ascii=False) if isinstance(detail, dict) else detail)

# 3) Stream - try with episode number
# First, check what episode data looks like
episodes = drama.get("episodes", [])
if episodes:
    ep = episodes[0]
    ep_id = ep.get("id", ep.get("episode_id", ""))
    ep_num = ep.get("episode", ep.get("number", 1))
    print(f"\n\n=== STREAM (id={drama_id}, episode={ep_num}) ===\n")
    r3 = requests.get(f"{base}?action=stream&id={drama_id}&episode={ep_num}", timeout=15)
    print(f"Status: {r3.status_code}")
    stream = r3.json() if r3.status_code == 200 else r3.text
    print(json.dumps(stream, indent=2, ensure_ascii=False) if isinstance(stream, dict) else stream)
    
    # Also try with episode ID if available
    if ep_id:
        print(f"\n\n=== STREAM (id={drama_id}, episode={ep_id}) ===\n")
        r4 = requests.get(f"{base}?action=stream&id={drama_id}&episode={ep_id}", timeout=15)
        print(f"Status: {r4.status_code}")
        s4 = r4.json() if r4.status_code == 200 else r4.text
        print(json.dumps(s4, indent=2, ensure_ascii=False) if isinstance(s4, dict) else s4[:500])
else:
    # No episodes in search response, try stream with episode=1
    print(f"\n\n=== STREAM (id={drama_id}, episode=1) ===\n")
    r3 = requests.get(f"{base}?action=stream&id={drama_id}&episode=1", timeout=15)
    print(f"Status: {r3.status_code}")
    stream = r3.json() if r3.status_code == 200 else r3.text
    print(json.dumps(stream, indent=2, ensure_ascii=False) if isinstance(stream, dict) else stream[:500])

# 4) Multi-search to get more
print(f"\n\n=== MULTI-SEARCH ===\n")
r5 = requests.get(f"{base}?action=multi-search&keyword=pewaris&limit=5", timeout=15)
print(f"Status: {r5.status_code}")
if r5.status_code == 200:
    ms = r5.json()
    print(json.dumps(ms, indent=2, ensure_ascii=False)[:2000])
else:
    print(r5.text[:500])
