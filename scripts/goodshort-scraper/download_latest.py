#!/usr/bin/env python3
"""
Download Specific Captured Covers
From latest Frida capture session
"""

import requests
from pathlib import Path
from PIL import Image

SCRIPT_DIR = Path(__file__).parent
OUTPUT_DIR = SCRIPT_DIR / "latest_covers"
OUTPUT_DIR.mkdir(exist_ok=True)

HEADERS = {
    'User-Agent': 'Dalvik/2.1.0 (Linux; U; Android 11; sdk_gphone_x86_64 Build/RSR1.240422.006)',
    'Host': 'acf.goodreels.com',
    'Connection': 'Keep-Alive',
    'Accept-Encoding': 'gzip'
}

# URLs from latest Frida capture
URLS = [
    'https://acf.goodreels.com/videobook/202508/cover-j0xXGvSlXe.jpg',
    'https://acf.goodreels.com/videobook/202508/cover-OCshVaWn.jpg',
    'https://acf.goodreels.com/videobook/202405/cover-xPEPIVJaGC.jpg',
    'https://acf.goodreels.com/videobook/31000860396/202509/cover-nrSb55zugf.jpg',
]

print(f"\n{'='*70}")
print("🎯 Download Latest Captured Covers")
print(f"{'='*70}\n")

for i, url in enumerate(URLS, 1):
    print(f"{'─'*70}")
    print(f"📥 [{i}/{len(URLS)}] {url.split('/')[-1]}")
    
    try:
        response = requests.get(url, headers=HEADERS, timeout=30)
        response.raise_for_status()
        
        filename = url.split('/')[-1]
        filepath = OUTPUT_DIR / filename
        
        with open(filepath, 'wb') as f:
            f.write(response.content)
        
        # Check dimensions
        img = Image.open(filepath)
        width, height = img.size
        aspect = height / width if width > 0 else 0
        
        is_portrait = height > width
        
        print(f"   ✅ Downloaded: {len(response.content):,} bytes")
        print(f"   📐 Size: {width}x{height}")
        print(f"   📊 Aspect: {aspect:.2f}")
        
        if is_portrait:
            print(f"   🎯 PORTRAIT POSTER! ✅✅✅")
        else:
            print(f"   ⏺️  Not portrait")
            
    except Exception as e:
        print(f"   ❌ Failed: {e}")
    
    print()

print(f"{'='*70}")
print(f"✅ Check: {OUTPUT_DIR}/")
print(f"{'='*70}\n")
