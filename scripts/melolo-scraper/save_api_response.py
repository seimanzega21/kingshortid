#!/usr/bin/env python3
"""Save full API responses to file for analysis."""
import requests, json

base = "https://vidrama.asia/api/melolo"
out = {}

# 1) Search - first drama
r = requests.get(f"{base}?action=search&keyword=a&limit=2&offset=0", timeout=15)
out["search"] = r.json()

drama = out["search"]["data"][0]
drama_id = drama["id"]

# 2) Detail
r2 = requests.get(f"{base}?action=detail&id={drama_id}", timeout=15)
out["detail"] = r2.json() if r2.status_code == 200 else {"error": r2.text[:500]}

# 3) Stream ep1
r3 = requests.get(f"{base}?action=stream&id={drama_id}&episode=1", timeout=15)
out["stream_ep1"] = r3.json() if r3.status_code == 200 else {"error": r3.text[:500]}

# 4) Also try search-all
r4 = requests.get(f"{base}?action=search-all&limit=100", timeout=15)
out["search_all"] = r4.json() if r4.status_code == 200 else {"error": str(r4.status_code) + " " + r4.text[:200]}

# 5) Try all-trending
r5 = requests.get(f"{base}?action=all-trending&limit=100", timeout=15)
out["all_trending"] = r5.json() if r5.status_code == 200 else {"error": str(r5.status_code) + " " + r5.text[:200]}

with open("vidrama_api_full.json", "w", encoding="utf-8") as f:
    json.dump(out, f, indent=2, ensure_ascii=False)

print("Saved vidrama_api_full.json")
print(f"Search items: {len(out['search'].get('data', []))}")
print(f"Detail keys: {list(out['detail'].keys()) if isinstance(out['detail'], dict) else 'error'}")
print(f"Stream keys: {list(out['stream_ep1'].keys()) if isinstance(out['stream_ep1'], dict) else 'error'}")
print(f"Search-all: {type(out['search_all'])}")
print(f"All-trending: {type(out['all_trending'])}")
