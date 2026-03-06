#!/usr/bin/env python3
"""Audit: cek Accept-Ranges, ukuran file, dan estimasi bitrate beberapa episode."""
import requests, sys
sys.stdout.reconfigure(encoding="utf-8")

BASE = "https://stream.shortlovers.id/dramas/microdrama/legenda-naga-kembali"

# 1. Header check
url1 = f"{BASE}/ep001/video.mp4"
r = requests.head(url1, timeout=10)
print("=== CDN Headers Check (ep001 - legenda-naga-kembali) ===")
print(f"HTTP: {r.status_code}")
print(f"Accept-Ranges : {r.headers.get('Accept-Ranges', 'MISSING')}")
print(f"Content-Length: {int(r.headers.get('Content-Length', 0)) / 1024 / 1024:.2f} MB")
print(f"CF-Cache      : {r.headers.get('cf-cache-status', '?')}")
print(f"Content-Type  : {r.headers.get('Content-Type', '?')}")
print(f"Cache-Control : {r.headers.get('Cache-Control', '?')}")
print()

# 2. Sample sizes across episodes
print("=== Sample Episode Sizes & Est. Bitrate ===")
print(f"{'Ep':>4} | {'Size MB':>8} | {'Bitrate kbps':>12} | {'4G OK?':>6}")
print("-" * 40)
for ep in [1, 5, 10, 16, 20, 30, 34, 40, 50]:
    u = f"{BASE}/ep{ep:03d}/video.mp4"
    try:
        rr = requests.head(u, timeout=8)
        size = int(rr.headers.get("Content-Length", 0))
        if size > 0:
            bitrate = size * 8 / 1024 / 90   # assume 90s per episode
            ok = "YES" if bitrate < 1500 else "NO (too big)"
            print(f"{ep:>4} | {size/1024/1024:>8.2f} | {bitrate:>12.0f} | {ok:>6}")
        else:
            print(f"{ep:>4} | {'N/A':>8} | {'N/A':>12} | {'?':>6}")
    except Exception as e:
        print(f"{ep:>4} | ERROR: {str(e)[:30]}")

# 3. Test range request
print()
print("=== Range Request Test ===")
r2 = requests.get(url1, headers={"Range": "bytes=0-1023"}, timeout=10)
print(f"Range request HTTP: {r2.status_code}")
print(f"Content-Range: {r2.headers.get('Content-Range', 'MISSING')}")
if r2.status_code == 206:
    print("Range Request: OK (206 Partial Content) - player can seek!")
elif r2.status_code == 200:
    print("Range Request: NOT SUPPORTED (200) - player cannot seek efficiently!")
else:
    print(f"Range Request: unexpected {r2.status_code}")
