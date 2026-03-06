#!/usr/bin/env python3
"""
QUICK TEST - Download from known URL
"""

import requests
from pathlib import Path

# Test URL from HTTP Toolkit
URL = "https://v2-akm.goodreels.com/mts/books/260/31000762260/325922/tglgtffgcf/720p/sawpvri3km_720p_000000.ts"

HEADERS = {
    'User-Agent': 'com.newreading.goodreels/2.7.8.2078 (Linux;Android 11) ExoPlayerLib/2.18.2',
    'Accept-Encoding': 'identity',
    'Connection': 'Keep-Alive'
}

OUTPUT_DIR = Path("quick_test_download")
OUTPUT_DIR.mkdir(exist_ok=True)

print("\n" + "="*70)
print("QUICK TEST - Single Segment Download")
print("="*70)
print()

print(f"URL: {URL[:80]}...")
print(f"Output: {OUTPUT_DIR}/")
print()

session = requests.Session()
session.headers.update(HEADERS)

try:
    print("Downloading...")
    response = session.get(URL, timeout=30)
    response.raise_for_status()
    
    output_file = OUTPUT_DIR / "test_segment.ts"
    with open(output_file, 'wb') as f:
        f.write(response.content)
    
    size_mb = len(response.content) / 1024 / 1024
    
    print()
    print("="*70)
    print("✅ SUCCESS!")
    print("="*70)
    print(f"Status: {response.status_code}")
    print(f"Size: {size_mb:.2f} MB ({len(response.content):,} bytes)")
    print(f"File: {output_file}")
    print()
    print("Test successful! Headers are working correctly!")
    print()
    
except Exception as e:
    print()
    print("="*70)
    print("❌ FAILED!")
    print("="*70)
    print(f"Error: {e}")
    print()
