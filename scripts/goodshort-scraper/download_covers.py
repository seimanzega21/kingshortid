"""
Download Covers - Phase 4 Step 1
Downloads all cover images for the 3 dramas
"""

import json
import requests
from pathlib import Path
import time

# Load drama data
with open('extracted_data_complete/dramas.json', 'r', encoding='utf-8') as f:
    dramas = json.load(f)

# Create output directory
output_dir = Path("downloaded_media/covers")
output_dir.mkdir(parents=True, exist_ok=True)

print("=" * 70)
print("DOWNLOADING COVER IMAGES")
print("=" * 70)

covers_downloaded = {}

for drama_id, drama in dramas.items():
    title = drama['title']
    cover_url = drama['cover_url']
    
    if not cover_url:
        print(f"\n❌ {title}: No cover URL")
        continue
    
    print(f"\n📥 Downloading: {title}")
    print(f"   URL: {cover_url}")
    
    # Create safe filename
    safe_title = title.replace(' ', '_').replace(',', '').replace(':', '')
    filename = f"{drama_id}_{safe_title}.jpg"
    filepath = output_dir / filename
    
    try:
        # Download with proper headers
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
            'Accept': 'image/webp,image/apng,image/*,*/*;q=0.8',
            'Accept-Encoding': 'identity',  # Important for GoodShort CDN
            'Referer': 'https://www.goodreels.com/'
        }
        
        response = requests.get(cover_url, headers=headers, timeout=30)
        response.raise_for_status()
        
        # Save image
        with open(filepath, 'wb') as f:
            f.write(response.content)
        
        file_size = len(response.content) / 1024  # KB
        covers_downloaded[drama_id] = {
            'title': title,
            'filename': filename,
            'path': str(filepath),
            'url': cover_url,
            'size_kb': file_size
        }
        
        print(f"   ✅ Saved: {filename} ({file_size:.1f} KB)")
        
        # Small delay to be respectful
        time.sleep(0.5)
        
    except Exception as e:
        print(f"   ❌ Error: {e}")

print("\n" + "=" * 70)
print("DOWNLOAD SUMMARY")
print("=" * 70)
print(f"\nTotal Covers: {len(dramas)}")
print(f"Downloaded: {len(covers_downloaded)}")
print(f"Failed: {len(dramas) - len(covers_downloaded)}")

# Save manifest
manifest_file = output_dir / "covers_manifest.json"
with open(manifest_file, 'w', encoding='utf-8') as f:
    json.dump(covers_downloaded, f, indent=2, ensure_ascii=False)

print(f"\n✅ Manifest saved: {manifest_file}")
print(f"📁 Covers saved to: {output_dir}/")
