#!/usr/bin/env python3
"""Verify lang=id API and check detail response."""
import requests, sys, json
sys.stdout.reconfigure(encoding="utf-8")

# Verify Indonesian list
r = requests.get("https://vidrama.asia/api/microdrama?action=list&lang=id&limit=10", timeout=15)
print(f"List lang=id status: {r.status_code}")
data = r.json()
print(f"Total: {data.get('total', '?')}")
dramas = data.get("dramas", [])
for i, d in enumerate(dramas[:5], 1):
    print(f"  {i}. {d['title']} ({d.get('episodes','?')} eps)")

# Check detail for a drama with episode video URLs
if dramas:
    did = dramas[0]["id"]
    r2 = requests.get(f"https://vidrama.asia/api/microdrama?action=detail&id={did}&lang=id", timeout=15)
    print(f"\nDetail status: {r2.status_code}")
    detail = r2.json().get("drama", {})
    eps = detail.get("episodes", [])
    print(f"Episodes in detail: {len(eps)}")
    if eps:
        ep1 = eps[0]
        print(f"Episode 1 keys: {list(ep1.keys())}")
        vids = ep1.get("videos", [])
        print(f"Videos count: {len(vids)}")
        for v in vids[:3]:
            print(f"  {v.get('quality','?')}: {v.get('url','?')[:80]}")
