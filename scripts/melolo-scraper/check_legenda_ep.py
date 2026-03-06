#!/usr/bin/env python3
"""Cek episode data Legenda Naga Kembali ep 16 & 17"""
import requests, json, sys
sys.stdout.reconfigure(encoding="utf-8")

DRAMA_ID   = "2010948201357684738"
DRAMA_SLUG = "legenda-naga-kembali"
NEXT_ACTION = "40c1405810e1d492d36c686b19fdd772f47beba84f"
TARGET_EPS = [16, 17]

print("=" * 60)
print("  CHECK: Legenda Naga Kembali - Ep 16 & 17")
print("=" * 60)

# Method 1: Direct API
print("\n[A] Direct API (microdrama detail)...")
try:
    url = f"https://vidrama.asia/api/microdrama?action=detail&id={DRAMA_ID}&lang=id"
    resp = requests.get(url, timeout=20)
    print(f"    Status: {resp.status_code}")
    if resp.status_code == 200:
        data = resp.json()
        eps = data.get("episodes", [])
        print(f"    Total episodes: {len(eps)}")
        for ep in eps:
            idx = ep.get("index", 0)
            if idx in TARGET_EPS:
                videos = ep.get("videos", [])
                print(f"\n    === Episode {idx} ===")
                print(f"    Videos count: {len(videos)}")
                for v in videos:
                    print(f"      quality: {v.get('quality', '?')}")
                    print(f"      url: {v.get('url', 'NONE')[:100]}")
    else:
        print(f"    Response: {resp.text[:300]}")
except Exception as e:
    print(f"    Error: {e}")

# Method 2: Watch page (RSC)
print("\n[B] Watch page RSC method...")
try:
    watch_url = f"https://vidrama.asia/watch/{DRAMA_SLUG}--{DRAMA_ID}/16?provider=microdrama"
    headers = {
        "next-action": NEXT_ACTION,
        "accept": "text/x-component",
        "content-type": "text/plain;charset=UTF-8",
        "origin": "https://vidrama.asia",
        "referer": watch_url,
        "user-agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
    }
    resp = requests.post(
        watch_url,
        headers=headers,
        data=json.dumps([DRAMA_ID]).encode("utf-8"),
        timeout=30
    )
    print(f"    Status: {resp.status_code}")
    if resp.status_code == 200:
        found_eps = []
        for line in resp.text.split("\n"):
            if ":" not in line:
                continue
            idx, _, rest = line.partition(":")
            if not idx.strip().isdigit() or not rest:
                continue
            try:
                chunk = json.loads(rest)
                if isinstance(chunk, dict) and "episodes" in chunk:
                    found_eps = chunk["episodes"]
                    break
                if isinstance(chunk, list) and chunk and isinstance(chunk[0], dict) and "videos" in chunk[0]:
                    found_eps = chunk
                    break
            except:
                pass
        
        print(f"    Total episodes found: {len(found_eps)}")
        for ep in found_eps:
            ep_idx = ep.get("index", 0)
            if ep_idx in TARGET_EPS:
                videos = ep.get("videos", [])
                print(f"\n    === Episode {ep_idx} ===")
                print(f"    Videos count: {len(videos)}")
                for v in videos:
                    print(f"      quality: {v.get('quality', '?')}")
                    print(f"      url: {v.get('url', 'NONE')[:100]}")
    else:
        print(f"    Response: {resp.text[:300]}")
except Exception as e:
    print(f"    Error: {e}")

print("\n" + "=" * 60)
