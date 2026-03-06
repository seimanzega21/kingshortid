#!/usr/bin/env python3
"""
DIRECT URL DOWNLOADER
=====================

If HAR export tidak available, paste URLs directly dan download.
"""

from pathlib import Path
import requests

# OUTPUT
OUTPUT_DIR = Path("downloaded_segments")
OUTPUT_DIR.mkdir(exist_ok=True)

# URLs - PASTE dari HTTP Toolkit (copy all .ts URLs)
URLS = """
# PASTE .ts URLs HERE
# One URL per line
# Example:
# https://v2-akm.goodreels.com/mts/books/.../720p_000001.ts
# https://v2-akm.goodreels.com/mts/books/.../720p_000002.ts
""".strip().split('\n')

def download_from_urls():
    """Download from URL list"""
    
    # Filter real URLs
    urls = [u.strip() for u in URLS if u.strip() and u.startswith('http')]
    
    if not urls:
        print("\n❌ No URLs found!")
        print("\nPLEASE:")
        print("  1. In HTTP Toolkit, select all .ts requests")
        print("  2. Copy URLs")
        print("  3. Paste in this script at URLS section")
        print("  4. Run again")
        return
    
    print(f"\n{'='*70}")
    print(f"DOWNLOADING {len(urls)} SEGMENTS")
    print(f"{'='*70}\n")
    
    session = requests.Session()
    session.headers.update({
        'User-Agent': 'GoodShort/2.5.1',
        'Accept': '*/*'
    })
    
    for i, url in enumerate(urls):
        filename = f"segment_{i:06d}.ts"
        output_path = OUTPUT_DIR / filename
        
        try:
            print(f"[{i+1}/{len(urls)}] {filename}...", end=' ')
            response = session.get(url, timeout=30)
            response.raise_for_status()
            
            with open(output_path, 'wb') as f:
                f.write(response.content)
            
            size_mb = len(response.content) / 1024 / 1024
            print(f"✅ ({size_mb:.2f} MB)")
            
        except Exception as e:
            print(f"❌ {e}")
    
    print(f"\n✅ Output: {OUTPUT_DIR}/")

if __name__ == "__main__":
    download_from_urls()
