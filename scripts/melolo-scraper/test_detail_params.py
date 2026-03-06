#!/usr/bin/env python3
"""Try different detail API params for microdrama to get episodes."""
import requests, sys, json
sys.stdout.reconfigure(encoding="utf-8")

DRAMA_ID = "2026565395272769537"  # Istri Dokter Masa Depan Pembawa Hoki

attempts = [
    f"https://vidrama.asia/api/microdrama?action=detail&id={DRAMA_ID}",
    f"https://vidrama.asia/api/microdrama?action=detail&id={DRAMA_ID}&lang=id",
    f"https://vidrama.asia/api/microdrama?action=episodes&id={DRAMA_ID}&lang=id",
    f"https://vidrama.asia/api/microdrama?action=stream&id={DRAMA_ID}&episode=1&lang=id",
    f"https://vidrama.asia/api/microdrama?action=detail&id={DRAMA_ID}&page=1",
]

for url in attempts:
    try:
        r = requests.get(url, timeout=15)
        data = r.json()
        label = url.split("?")[1][:60]
        if r.status_code == 200:
            drama = data.get("drama", data.get("data", {}))
            if isinstance(drama, dict):
                eps = drama.get("episodes", [])
                print(f"[OK] {label}")
                print(f"     episodes: {len(eps)}, keys: {list(drama.keys())[:8]}")
                if eps:
                    ep1 = eps[0]
                    vids = ep1.get("videos", [])
                    print(f"     ep1 videos: {len(vids)}")
                    for v in vids[:2]:
                        print(f"       {v.get('quality','?')}: {str(v.get('url','?'))[:80]}")
                    break
            else:
                print(f"[OK] {label} -> unexpected structure: {str(data)[:100]}")
        else:
            print(f"[{r.status_code}] {label} -> {str(data)[:100]}")
    except Exception as e:
        print(f"[ERR] -> {e}")
