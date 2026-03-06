#!/usr/bin/env python3
"""
Probe Netshort / TikTok drama API patterns.
The drama ID 7021836588775127693 comes from TikTok/Netshort's short drama platform.
"""
import requests, json

DRAMA_ID = "7021836588775127693"

# These are common TikTok/Bytedance drama API patterns
endpoints = [
    # Vidrama internal API (Next.js API routes)
    f"https://vidrama.asia/api/drama/{DRAMA_ID}?provider=netshort",
    f"https://vidrama.asia/api/provider/netshort/detail/{DRAMA_ID}",
    f"https://vidrama.asia/api/netshort/detail?id={DRAMA_ID}",
    
    # Direct Netshort API patterns  
    f"https://api.netshort.id/api/drama/{DRAMA_ID}",
    f"https://netshort.id/api/drama/{DRAMA_ID}",
    
    # TikTok drama API patterns
    f"https://api16-normal-useast5.us.tiktokv.com/api/drama/detail/?drama_id={DRAMA_ID}",
    f"https://api.tiktok.com/aweme/v1/drama/detail/?drama_id={DRAMA_ID}",
    
    # Vidrama RSC payload fetch  
    f"https://vidrama.asia/movie/kabut-dendam-sang-pendekar--{DRAMA_ID}?_rsc=true",
]

headers = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
    "Accept": "application/json, text/plain, */*",
    "Referer": "https://vidrama.asia/",
}

for url in endpoints:
    print(f"\n--- {url[:80]}...")
    try:
        r = requests.get(url, headers=headers, timeout=10, allow_redirects=True)
        print(f"  Status: {r.status_code}")
        ct = r.headers.get("content-type", "")
        print(f"  Content-Type: {ct}")
        if r.status_code == 200:
            text = r.text[:500]
            if "json" in ct:
                try:
                    data = r.json()
                    print(f"  Keys: {list(data.keys()) if isinstance(data, dict) else 'array'}")
                    print(f"  JSON (500c): {json.dumps(data, indent=2)[:500]}")
                except:
                    print(f"  Raw: {text}")
            else:
                print(f"  Text: {text[:300]}")
        elif r.status_code in [301, 302]:
            print(f"  Redirect: {r.headers.get('location', 'N/A')}")
    except Exception as e:
        print(f"  Error: {str(e)[:80]}")

# Also try the RSC flight data format
print("\n\n=== Trying Next.js RSC Flight Data ===")
rsc_headers = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
    "Accept": "text/x-component",
    "Next-Router-State-Tree": "%5B%22%22%2C%7B%22children%22%3A%5B%22movie%22%2C%7B%22children%22%3A%5B%5B%22slug%22%2C%22kabut-dendam-sang-pendekar--7021836588775127693%22%2C%22d%22%5D%2C%7B%22children%22%3A%5B%22__PAGE__%22%2C%7B%7D%5D%7D%5D%7D%5D%7D%5D",
    "RSC": "1",
    "Next-URL": "/movie/kabut-dendam-sang-pendekar--7021836588775127693?provider=netshort",
    "Referer": "https://vidrama.asia/",
}
url = "https://vidrama.asia/movie/kabut-dendam-sang-pendekar--7021836588775127693?provider=netshort"
try:
    r = requests.get(url, headers=rsc_headers, timeout=10)
    print(f"  Status: {r.status_code}")
    print(f"  Content-Type: {r.headers.get('content-type', 'N/A')}")
    # Look for drama data in the RSC payload
    text = r.text
    if "Kabut" in text or "kabut" in text:
        # Find the relevant parts
        for line in text.split("\n"):
            if "kabut" in line.lower() or "episode" in line.lower() or "genre" in line.lower():
                print(f"  FOUND: {line[:200]}")
    else:
        print(f"  Text (500c): {text[:500]}")
except Exception as e:
    print(f"  Error: {e}")

# Try Vidrama's internal Next.js API patterns
print("\n\n=== Trying Vidrama Internal Server Actions ===")
for action in ["detail", "episodes", "stream"]:
    url = f"https://vidrama.asia/api/netshort?action={action}&id={DRAMA_ID}"
    try:
        r = requests.get(url, headers=headers, timeout=10)
        print(f"\n  action={action}: Status={r.status_code}")
        if r.status_code == 200:
            print(f"  Response: {r.text[:300]}")
    except Exception as e:
        print(f"  Error: {e}")
