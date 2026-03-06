"""
Analyze new HAR capture to find correct poster URLs
"""

import json
from pathlib import Path
from collections import defaultdict

def analyze_new_capture():
    """Analyze HTTPToolkit_2026-02-03_00-53.har for posters"""
    
    har_file = "HTTPToolkit_2026-02-03_00-53.har"
    
    if not Path(har_file).exists():
        print(f"❌ {har_file} not found!")
        return
    
    print(f"📂 Analyzing: {har_file}")
    print("="*80 + "\n")
    
    with open(har_file, 'r', encoding='utf-8') as f:
        har = json.load(f)
    
    entries = har['log']['entries']
    
    target_ids = ['31001045572', '31001070612']
    
    # Collect ALL image URLs
    all_images = defaultdict(list)
    
    for entry in entries:
        url = entry['request']['url']
        
        # Images only
        if not any(ext in url.lower() for ext in ['.jpg', '.jpeg', '.png', '.webp']):
            continue
        
        # GoodReels only
        if 'goodreels' not in url and 'goodshort' not in url:
            continue
        
        # Check for book IDs
        for book_id in target_ids:
            if book_id in url:
                all_images[book_id].append(url)
    
    print(f"📊 FOUND {sum(len(urls) for urls in all_images.values())} image requests\n")
    
    # Show unique URLs per book
    for book_id, urls in all_images.items():
        unique_urls = list(set(urls))
        
        print(f"\n{'='*80}")
        print(f"📚 Book ID: {book_id}")
        print(f"{'='*80}")
        print(f"Total requests: {len(urls)} | Unique URLs: {len(unique_urls)}\n")
        
        # Categorize by filename pattern
        categories = defaultdict(list)
        
        for url in unique_urls:
            filename = url.split('/')[-1].split('?')[0]
            
            if 'poster' in filename.lower():
                categories['POSTER'].append(url)
            elif 'cover' in filename.lower():
                categories['COVER'].append(url)
            elif 'thumb' in filename.lower():
                categories['THUMBNAIL'].append(url)
            elif 'banner' in filename.lower():
                categories['BANNER'].append(url)
            else:
                # Check path segments
                path_parts = url.lower().split('/')
                if 'poster' in ' '.join(path_parts):
                    categories['POSTER (path)'].append(url)
                elif 'cover' in ' '.join(path_parts):
                    categories['COVER (path)'].append(url)
                else:
                    categories['OTHER'].append(url)
        
        # Display categories
        for category in sorted(categories.keys()):
            urls_list = categories[category]
            print(f"\n  📁 {category}: {len(urls_list)} URL(s)")
            for url in urls_list[:5]:  # Show first 5
                print(f"     • {url}")
    
    return all_images


def compare_with_old_capture():
    """Compare new capture with old to find differences"""
    
    print("\n\n" + "="*80)
    print("🔍 COMPARING WITH OLD CAPTURE")
    print("="*80 + "\n")
    
    old_har = "HTTPToolkit_2026-02-03_00-02.har"
    new_har = "HTTPToolkit_2026-02-03_00-53.har"
    
    if not Path(old_har).exists() or not Path(new_har).exists():
        print("⚠️  Old or new HAR not found")
        return
    
    target_ids = ['31001045572', '31001070612']
    
    def get_image_urls(har_path):
        with open(har_path, 'r', encoding='utf-8') as f:
            har = json.load(f)
        
        images = defaultdict(set)
        for entry in har['log']['entries']:
            url = entry['request']['url']
            if any(ext in url.lower() for ext in ['.jpg', '.jpeg', '.png', '.webp']):
                if 'goodreels' in url or 'goodshort' in url:
                    for book_id in target_ids:
                        if book_id in url:
                            images[book_id].add(url)
        return images
    
    old_images = get_image_urls(old_har)
    new_images = get_image_urls(new_har)
    
    for book_id in target_ids:
        old_urls = old_images.get(book_id, set())
        new_urls = new_images.get(book_id, set())
        
        only_in_new = new_urls - old_urls
        only_in_old = old_urls - new_urls
        common = old_urls & new_urls
        
        print(f"\n📚 {book_id}:")
        print(f"  Old capture: {len(old_urls)} unique URLs")
        print(f"  New capture: {len(new_urls)} unique URLs")
        print(f"  Common: {len(common)}")
        print(f"  🆕 Only in NEW: {len(only_in_new)}")
        
        if only_in_new:
            print(f"\n  🎯 NEW URLs (likely the correct poster!):")
            for url in only_in_new:
                print(f"     • {url}")


if __name__ == "__main__":
    all_images = analyze_new_capture()
    compare_with_old_capture()
