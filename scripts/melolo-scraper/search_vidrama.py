"""
Search vidrama.asia for 5 dramas and extract cover image URLs from the HTML/RSC payload.
"""
import requests, re, json, urllib.parse

TARGET_DRAMAS = [
    "Setelah Bertapa, Kutaklukkan Dunia",
    "Siapa yang Sedang Membicarakan Kaisar",
    "Sistem Perubah Nasib",
    "Sistem Suami Sultan",
    "Tahun 1977 Penuh Peluang",
]

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 Chrome/120.0.0.0 Safari/537.36",
}

found_covers = {}

for title in TARGET_DRAMAS:
    # Use short search terms
    search_term = title.split(',')[0].strip()[:25]
    encoded = urllib.parse.quote(search_term)
    
    print(f"\n{'='*60}")
    print(f"Searching: {title}")
    print(f"  Term: {search_term}")
    
    url = f"https://vidrama.asia/search?q={encoded}"
    try:
        r = requests.get(url, headers=HEADERS, timeout=15)
        html = r.text
        
        # Extract image URLs from the response
        # Look for cover image patterns
        img_urls = re.findall(r'(https?://[^"\\]+\.(?:jpg|jpeg|png|webp))', html)
        
        # Filter for likely cover images  
        cover_candidates = [u for u in img_urls if any(kw in u.lower() for kw in ['cover', 'poster', 'thumb', 'novel', 'novel-sign', 'p16-novel', 'image'])]
        
        if cover_candidates:
            print(f"  Found {len(cover_candidates)} cover candidates:")
            for c in cover_candidates[:5]:
                print(f"    {c[:120]}")
            found_covers[title] = cover_candidates[0]
        else:
            # Try all images
            non_static = [u for u in img_urls if '/_next/' not in u and 'favicon' not in u]
            print(f"  No covers but {len(non_static)} images:")
            for u in non_static[:5]:
                print(f"    {u[:120]}")
            if non_static:
                found_covers[title] = non_static[0]
        
        # Also look for JSON data in the RSC payload
        json_matches = re.findall(r'"cover_url"\s*:\s*"([^"]+)"', html)
        if json_matches:
            print(f"  JSON cover_url: {json_matches}")
            found_covers[title] = json_matches[0]
        
        # Try another pattern: img src in the page
        img_src = re.findall(r'src="(https://[^"]+)"', html)
        drama_imgs = [s for s in img_src if 'novel' in s.lower() or 'p16' in s.lower() or 'cover' in s.lower()]
        if drama_imgs:
            print(f"  Page img src:")
            for i in drama_imgs[:3]:
                print(f"    {i[:120]}")
        
    except Exception as e:
        print(f"  Error: {e}")

print(f"\n\n{'='*60}")
print(f"Found covers for {len(found_covers)}/{len(TARGET_DRAMAS)} dramas:")
for title, url in found_covers.items():
    print(f"  {title}: {url[:100]}")
