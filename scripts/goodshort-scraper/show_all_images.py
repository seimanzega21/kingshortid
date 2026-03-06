"""
Show ALL image URLs for target dramas to identify the correct poster
"""

import json
from pathlib import Path
from collections import defaultdict

har_file = "HTTPToolkit_2026-02-03_00-02.har"

with open(har_file, 'r', encoding='utf-8') as f:
    har = json.load(f)

target_ids = ['31001045572', '31001070612']

# Collect ALL image URLs
images_by_book = defaultdict(list)

for entry in har['log']['entries']:
    url = entry['request']['url']
    
    # Images only
    if not any(ext in url.lower() for ext in ['.jpg', '.jpeg', '.png', '.webp']):
        continue
    
    # GoodReels only
    if 'goodreels' not in url:
        continue
    
    # Match book IDs
    for book_id in target_ids:
        if book_id in url:
            images_by_book[book_id].append(url)

print("📋 ALL IMAGE URLs PER DRAMA:\n")
print("="*80)

for book_id, urls in images_by_book.items():
    # Deduplicate
    unique_urls = list(set(urls))
    
    print(f"\n📚 {book_id} - {len(unique_urls)} unique image URLs:\n")
    
    for i, url in enumerate(sorted(unique_urls), 1):
        # Extract key parts
        filename = url.split('/')[-1].split('?')[0]
        print(f"{i}. {filename}")
        print(f"   {url}")
        print()
