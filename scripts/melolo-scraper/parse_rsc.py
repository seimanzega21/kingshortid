#!/usr/bin/env python3
"""Parse RSC response and extract episode video URLs."""
import requests, sys, json, re
sys.stdout.reconfigure(encoding="utf-8")

DRAMA_ID = "2026565395272769537"
DRAMA_SLUG = "istri-dokter-masa-depan-pembawa-hoki"
NEXT_ACTION = "40c1405810e1d492d36c686b19fdd772f47beba84f"

url = f"https://vidrama.asia/watch/{DRAMA_SLUG}--{DRAMA_ID}/1?provider=microdrama"
headers = {
    "next-action": NEXT_ACTION,
    "accept": "text/x-component",
    "content-type": "text/plain;charset=UTF-8",
    "origin": "https://vidrama.asia",
    "referer": url,
    "user-agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
}

r = requests.post(url, headers=headers, data=json.dumps([DRAMA_ID]).encode(), timeout=20)
text = r.text

# RSC format: chunks like "0:{...}\n1:[...]\n2:{...}\n"
# Find all JSON objects/arrays on each line
chunks = {}
for line in text.split("\n"):
    if ":" not in line:
        continue
    idx, _, rest = line.partition(":")
    if idx.isdigit() and rest:
        try:
            chunks[int(idx)] = json.loads(rest)
        except:
            pass

print(f"RSC chunks parsed: {len(chunks)}")

# Find the chunk containing episode data
for k, v in sorted(chunks.items()):
    if isinstance(v, dict):
        if "episodes" in v:
            eps = v["episodes"]
            print(f"Found episodes in chunk {k}: {len(eps)} episodes")
            if eps:
                ep1 = eps[0]
                print(f"Ep1 keys: {list(ep1.keys())}")
                vids = ep1.get("videos", [])
                for vid in vids[:3]:
                    print(f"  {vid.get('quality')}: {str(vid.get('url',''))[:100]}")
            break
        elif "title" in v:
            print(f"Chunk {k} (drama info): title={v.get('title','?')[:50]}, keys={list(v.keys())[:6]}")
    elif isinstance(v, list) and len(v) > 0:
        if isinstance(v[0], dict) and "videos" in v[0]:
            print(f"Found episode list in chunk {k}: {len(v)} episodes")
            ep1 = v[0]
            vids = ep1.get("videos", [])
            for vid in vids[:3]:
                print(f"  {vid.get('quality')}: {str(vid.get('url',''))[:100]}")
            break

# Brute-force: find all "reeltv" URLs in the text
reel_urls = re.findall(r'https://reeltv\.janzhoutec\.com/[^\s"\\]+', text)
print(f"\nReelTV URLs found: {len(reel_urls)}")
for u in reel_urls[:5]:
    print(f"  {u[:100]}")
