"""
Fetch covers from vidrama.asia using series_ids from local metadata.
URL pattern: /movie/{slug}--{series_id}?provider=melolo
Cover is in og:image meta tag.
"""
import requests, re, json, os

HEADERS = {"User-Agent": "Mozilla/5.0 Chrome/120.0.0.0"}
r2_dir = "d:/kingshortid/scripts/melolo-scraper/r2_ready/melolo"

# Target dramas - find their series_ids
targets = [
    "Setelah Bertapa, Kutaklukkan Dunia",
    "Siapa yang Sedang Membicarakan Kaisar",
    "Sistem Perubah Nasib",
    "Sistem Suami Sultan",
    "Tahun 1977 Penuh Peluang",
]

target_keywords = {
    "setelah-bertapa": "Setelah Bertapa, Kutaklukkan Dunia",
    "membicarakan-kaisar": "Siapa yang Sedang Membicarakan Kaisar",
    "perubah-nasib": "Sistem Perubah Nasib",
    "suami-sultan": "Sistem Suami Sultan",
    "1977-penuh": "Tahun 1977 Penuh Peluang",
}

# Step 1: Find series_ids from all metadata files
print("=== Finding series_ids ===\n")
drama_data = {}

for dirname in sorted(os.listdir(r2_dir)):
    meta_path = os.path.join(r2_dir, dirname, "metadata.json")
    if not os.path.exists(meta_path):
        continue
    with open(meta_path, 'r', encoding='utf-8') as f:
        meta = json.load(f)
    
    title = meta.get('title', dirname)
    
    # Check if this matches any target
    for kw, target_title in target_keywords.items():
        if kw in dirname.lower() or kw.replace('-', ' ') in title.lower():
            drama_data[target_title] = {
                'slug': meta.get('slug', dirname),
                'series_id': meta.get('series_id', ''),
                'title': title,
                'dirname': dirname,
            }
            print(f"✅ {target_title}")
            print(f"   slug: {drama_data[target_title]['slug']}")
            print(f"   series_id: {drama_data[target_title]['series_id']}")
            break

# Also check for 'sultan' specifically (Dari Miskin Jadi Sultan vs Sistem Suami Sultan)
for dirname in os.listdir(r2_dir):
    if 'sistem-suami' in dirname.lower() or 'suami-sultan' in dirname.lower():
        meta_path = os.path.join(r2_dir, dirname, "metadata.json")
        if os.path.exists(meta_path):
            with open(meta_path, 'r', encoding='utf-8') as f:
                meta = json.load(f)
            drama_data["Sistem Suami Sultan"] = {
                'slug': meta.get('slug', dirname),
                'series_id': meta.get('series_id', ''),
                'title': meta.get('title', dirname),
                'dirname': dirname,
            }
            print(f"✅ Sistem Suami Sultan (found via dirname)")
            print(f"   slug: {drama_data['Sistem Suami Sultan']['slug']}")
            print(f"   series_id: {drama_data['Sistem Suami Sultan']['series_id']}")

print(f"\nMatched: {len(drama_data)}/{len(targets)} dramas\n")

# For unmatched, list all dramas to find them
unmatched = [t for t in targets if t not in drama_data]
if unmatched:
    print(f"Unmatched: {unmatched}")
    print(f"\nAll drama dirs:")
    for dirname in sorted(os.listdir(r2_dir)):
        print(f"  {dirname}")

# Step 2: Fetch vidrama pages and extract og:image
print(f"\n\n=== Fetching covers from vidrama.asia ===\n")
covers = {}

for target_title, info in drama_data.items():
    slug = info['slug']
    sid = info['series_id']
    
    if sid:
        url = f"https://vidrama.asia/movie/{slug}--{sid}?provider=melolo"
    else:
        url = f"https://vidrama.asia/movie/{slug}?provider=melolo"
    
    print(f"Fetching: {target_title}")
    print(f"  URL: {url}")
    
    try:
        r = requests.get(url, headers=HEADERS, timeout=15)
        if r.status_code == 200:
            og = re.search(r'property="og:image"\s+content="([^"]+)"', r.text)
            og_title = re.search(r'property="og:title"\s+content="([^"]+)"', r.text)
            
            if og:
                cover_url = og.group(1).replace('&amp;', '&')
                page_title = og_title.group(1) if og_title else "N/A"
                
                if cover_url != "https://vidrama.asia/og-image.jpg":
                    covers[target_title] = cover_url
                    print(f"  ✅ Cover found! ({page_title})")
                    print(f"  {cover_url[:120]}")
                else:
                    print(f"  ⚠️ Generic og-image (page: {page_title})")
            else:
                print(f"  ❌ No og:image in response")
        else:
            print(f"  ❌ Status: {r.status_code}")
    except Exception as e:
        print(f"  ❌ Error: {e}")
    print()

# Step 3: Download covers
print(f"\n=== Downloading {len(covers)} covers ===\n")
os.makedirs("vidrama_covers", exist_ok=True)

downloaded = {}
for title, url in covers.items():
    try:
        r = requests.get(url, headers=HEADERS, timeout=15)
        if r.status_code == 200 and len(r.content) > 1000:
            ct = r.headers.get('content-type', 'image/webp')
            ext = 'webp' if 'webp' in ct else 'jpg' if 'jpeg' in ct else 'png' if 'png' in ct else 'webp'
            safe_name = re.sub(r'[^a-z0-9]', '_', title.lower())[:50]
            filepath = os.path.join("vidrama_covers", f"{safe_name}.{ext}")
            with open(filepath, 'wb') as f:
                f.write(r.content)
            downloaded[title] = filepath
            print(f"✅ {title}: {filepath} ({len(r.content):,} bytes)")
        else:
            print(f"❌ {title}: status={r.status_code}, size={len(r.content)}")
    except Exception as e:
        print(f"❌ {title}: {e}")

print(f"\n\n=== SUMMARY ===")
print(f"Covers downloaded: {len(downloaded)}/{len(targets)}")
for title, path in downloaded.items():
    print(f"  ✅ {title}: {path}")
for title in targets:
    if title not in downloaded:
        print(f"  ❌ {title}: MISSING")
