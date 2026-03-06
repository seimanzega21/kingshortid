#!/usr/bin/env python3
"""Test the Next.js Server Action to get episode video URLs."""
import requests, sys, json, re
sys.stdout.reconfigure(encoding="utf-8")

DRAMA_ID = "2026565395272769537"  # Istri Dokter Masa Depan Pembawa Hoki
DRAMA_SLUG = "istri-dokter-masa-depan-pembawa-hoki"
NEXT_ACTION = "40c1405810e1d492d36c686b19fdd772f47beba84f"

url = f"https://vidrama.asia/watch/{DRAMA_SLUG}--{DRAMA_ID}/1?provider=microdrama"

headers = {
    "next-action": NEXT_ACTION,
    "accept": "text/x-component",
    "content-type": "text/plain;charset=UTF-8",
    "origin": "https://vidrama.asia",
    "referer": url,
    "user-agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36",
}
body = json.dumps([DRAMA_ID])

print(f"POST {url}")
r = requests.post(url, headers=headers, data=body.encode("utf-8"), timeout=20)
print(f"Status: {r.status_code}")
print(f"Content-Type: {r.headers.get('content-type','?')}")

# The RSC format embeds JSON - extract it
text = r.text
print(f"Response length: {len(text)}")
print(f"First 500 chars: {text[:500]}")

# Try to extract episode data
# RSC format: 0:{"a":"$@1","f":"","b":"development"}\n1:["...episode data..."]
eps_match = re.search(r'"episodes"\s*:\s*(\[[\s\S]+?\])\s*[,}]', text)
if eps_match:
    try:
        episodes = json.loads(eps_match.group(1))
        print(f"\nEpisodes found: {len(episodes)}")
        if episodes:
            ep1 = episodes[0]
            print(f"Ep1 keys: {list(ep1.keys())}")
            vids = ep1.get("videos", [])
            print(f"Ep1 videos: {len(vids)}")
            for v in vids[:3]:
                print(f"  {v.get('quality')}: {str(v.get('url',''))[:80]}")
    except:
        print("Could not parse episodes")
else:
    print("\nNo 'episodes' pattern found in response")
    # Save raw for inspection
    with open("server_action_raw.txt", "w", encoding="utf-8") as f:
        f.write(text[:5000])
    print("Saved first 5000 chars to server_action_raw.txt")
