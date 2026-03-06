"""
Try to get drama data from vidrama.asia using Next.js RSC payload format.
"""
import requests, re, json

HEADERS = {
    "User-Agent": "Mozilla/5.0 Chrome/120.0.0.0",
    "Accept": "text/x-component",
    "Next-Router-State-Tree": "%5B%22%22%2C%7B%22children%22%3A%5B%22search%22%2C%7B%22children%22%3A%5B%22__PAGE__%22%2C%7B%7D%5D%7D%5D%7D%2Cnull%2Cnull%2Ctrue%5D",
    "RSC": "1",
    "Next-Url": "/search?q=Bertapa",
}

# Try 1: RSC request to search page
print("=== Try 1: RSC search ===\n")
r = requests.get("https://vidrama.asia/search?q=Bertapa", headers=HEADERS, timeout=15)
print(f"Status: {r.status_code}, Content-Type: {r.headers.get('content-type', '')}")
# Parse RSC payload for cover URLs
text = r.text
if 'cover' in text.lower() or 'image' in text.lower() or 'poster' in text.lower():
    print("Found cover/image references in RSC!")
    # Extract URLs
    urls = re.findall(r'https://[^"\\]+\.(?:jpg|jpeg|png|webp|gif)', text)
    for u in urls[:10]:
        print(f"  URL: {u}")

# Extract any data that looks like drama objects
# RSC format uses escaped JSON strings
cover_urls = re.findall(r'"cover_url"\s*:\s*"([^"]+)"', text)
title_matches = re.findall(r'"title"\s*:\s*"([^"]+)"', text)
img_matches = re.findall(r'"(?:image|poster|thumbnail|cover|img_url)"\s*:\s*"([^"]+)"', text)

if cover_urls:
    print(f"\nCover URLs: {cover_urls}")
if title_matches:
    print(f"\nTitles: {title_matches[:10]}")
if img_matches:
    print(f"\nImages: {img_matches[:10]}")

# Print raw RSC content (first 2000 chars)
print(f"\nRaw RSC ({len(text)} bytes):")
print(text[:2000])

# Try 2: RSC request to provider page
print("\n\n=== Try 2: RSC provider/melolo ===\n")
headers2 = {
    "User-Agent": "Mozilla/5.0 Chrome/120.0.0.0",
    "RSC": "1",
    "Next-Url": "/provider/melolo",
}
r2 = requests.get("https://vidrama.asia/provider/melolo", headers=headers2, timeout=15)
print(f"Status: {r2.status_code}, Content-Type: {r2.headers.get('content-type', '')}")
text2 = r2.text
# Find drama data
titles2 = re.findall(r'"title"\s*:\s*"([^"]+)"', text2)
covers2 = re.findall(r'"(?:cover_url|poster|thumbnail|image_url|cover)"\s*:\s*"([^"]+)"', text2)
slugs2 = re.findall(r'"slug"\s*:\s*"([^"]+)"', text2)

if titles2:
    print(f"\nTitles: {titles2[:20]}")
if covers2:
    print(f"\nCovers: {covers2[:10]}")
if slugs2:
    print(f"\nSlugs: {slugs2[:20]}")

# Print raw (first 2000 chars)
print(f"\nRaw RSC ({len(text2)} bytes):")
print(text2[:3000])

# Try 3: Direct drama page URLs
print("\n\n=== Try 3: Direct drama pages ===\n")
for search in ["setelah-bertapa", "membicarakan-kaisar", "sistem-perubah-nasib", "sistem-suami-sultan", "tahun-1977"]:
    for provider in ["melolo"]:
        url = f"https://vidrama.asia/drama/{search}"
        try:
            r3 = requests.get(url, headers={**HEADERS, "RSC": "1", "Next-Url": f"/drama/{search}"}, timeout=10)
            if r3.status_code == 200:
                covers3 = re.findall(r'https://[^"\\]+\.(?:jpg|jpeg|png|webp)', r3.text)
                titles3 = re.findall(r'"title"\s*:\s*"([^"]+)"', r3.text)
                if covers3 or titles3:
                    print(f"  ✅ {search}: titles={titles3[:3]}, covers={covers3[:3]}")
                else:
                    print(f"  {search}: {r3.status_code} ({len(r3.text)} bytes, no data)")
            else:
                print(f"  {search}: {r3.status_code}")
        except:
            pass
