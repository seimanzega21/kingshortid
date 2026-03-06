"""
Download all new poster variants from latest capture
"""

import json
from pathlib import Path
import requests

def download_all_poster_variants():
    """Download all image variants for comparison"""
    
    har_file = "HTTPToolkit_2026-02-03_00-53.har"
    
    with open(har_file, 'r', encoding='utf-8') as f:
        har = json.load(f)
    
    target_ids = {
        '31001045572': 'Cinta_di_Waktu_yang_Tepat',
        '31001070612': 'Hidup_Kedua,_Cinta_Sejati_Menanti'
    }
    
    r2_ready = Path("r2_ready")
    
    for book_id, folder_name in target_ids.items():
        drama_folder = r2_ready / folder_name
        if not drama_folder.exists():
            print(f"⚠️  Folder not found: {folder_name}")
            continue
        
        # Find all image URLs for this book
        image_urls = []
        for entry in har['log']['entries']:
            url = entry['request']['url']
            
            if book_id not in url:
                continue
            
            if not any(ext in url.lower() for ext in ['.jpg', '.jpeg', '.png', '.webp']):
                continue
            
            if 'goodreels' not in url and 'goodshort' not in url:
                continue
            
            image_urls.append(url)
        
        unique_urls = list(set(image_urls))
        
        print(f"\n{'='*80}")
        print(f"📁 {folder_name}")
        print(f"{'='*80}")
        print(f"Found {len(unique_urls)} unique image URLs\n")
        
        # Download each variant
        for i, url in enumerate(unique_urls, 1):
            filename_from_url = url.split('/')[-1].split('?')[0]
            
            # Create descriptive filename
            if 'poster' in filename_from_url.lower():
                output_name = f'poster_variant_{i}.jpg'
            elif 'cover' in filename_from_url.lower():
                output_name = f'cover_variant_{i}.jpg'
            else:
                output_name = f'image_variant_{i}.jpg'
            
            output_path = drama_folder / output_name
            
            print(f"{i}. Downloading: {filename_from_url}")
            print(f"   URL: {url[:80]}...")
            
            try:
                resp = requests.get(url, timeout=15)
                resp.raise_for_status()
                
                with open(output_path, 'wb') as f:
                    f.write(resp.content)
                
                size_kb = len(resp.content) / 1024
                print(f"   ✅ Saved: {output_name} ({size_kb:.1f} KB)")
            except Exception as e:
                print(f"   ❌ Error: {e}")
            
            print()
        
        print(f"✅ Downloaded {len(unique_urls)} variants for {folder_name}\n")
    
    print("="*80)
    print("✅ ALL VARIANTS DOWNLOADED!")
    print("="*80)
    print("\nPlease check the drama folders and tell me which variant is correct!")


if __name__ == "__main__":
    download_all_poster_variants()
