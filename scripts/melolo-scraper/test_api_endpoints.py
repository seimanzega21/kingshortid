#!/usr/bin/env python3
"""Test different Vidrama API endpoints for microdrama provider"""
import requests, sys
sys.stdout.reconfigure(encoding="utf-8")

apis = [
    ("microdrama search", "https://vidrama.asia/api/microdrama?action=search&keyword=dokter&limit=5"),
    ("microdrama list", "https://vidrama.asia/api/microdrama?action=list&limit=5"),
    ("melolo search jenius", "https://vidrama.asia/api/melolo?action=search&keyword=Sang+Dokter+Jenius&limit=5"),
    ("melolo detail by microdrama id", "https://vidrama.asia/api/melolo?action=detail&id=2013523549009674"),
    ("melolo search naga", "https://vidrama.asia/api/melolo?action=search&keyword=Naga+Terjatuh&limit=5"),
    ("melolo all-trending", "https://vidrama.asia/api/melolo?action=all-trending&limit=20"),
    ("melolo list page1", "https://vidrama.asia/api/melolo?action=list&limit=50&offset=0"),
    ("melolo discover", "https://vidrama.asia/api/melolo?action=discover&limit=50"),
]

for name, url in apis:
    try:
        r = requests.get(url, timeout=10)
        print(f"[{r.status_code}] {name}")
        if r.status_code == 200:
            data = r.json()
            if "data" in data:
                items = data["data"]
                if isinstance(items, list):
                    print(f"    {len(items)} results")
                    for d in items[:3]:
                        t = d.get("title", "?")
                        print(f"    - {t}")
                elif isinstance(items, dict):
                    t = items.get("title", "?")
                    eps = items.get("episodes", [])
                    print(f"    title: {t}, episodes: {len(eps)}")
            else:
                print(f"    {str(data)[:200]}")
        else:
            print(f"    body: {r.text[:200]}")
    except Exception as e:
        print(f"[ERR] {name} -> {e}")
    print()
