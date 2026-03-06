"""
Find cover from HOME FEED / DRAMA LIST
NOT from detail page
"""

import json
from pathlib import Path
import requests

def find_home_feed_covers():
    """Search for cover images from home/list APIs"""
    
    har_files = [
        "HTTPToolkit_2026-02-03_00-53.har",
        "HTTPToolkit_2026-02-03_00-02.har",
        "HTTPToolkit_2026-02-02_23-24.har",
        "fresh_capture.har"
    ]
    
    target_ids = ['31001045572', '31001070612']
    
    print("🔍 Searching HOME FEED / LIST APIs for covers...\n")
    print("="*80 + "\n")
    
    covers_found = {}
    
    for har_file in har_files:
        if not Path(har_file).exists():
            continue
        
        print(f"📂 Analyzing: {har_file}\n")
        
        with open(har_file, 'r', encoding='utf-8') as f:
            har = json.load(f)
        
        # Look for home/list/recommend APIs
        for entry in har['log']['entries']:
            url = entry['request']['url']
            
            # Check if it's a list/home/recommend API
            is_list_api = any(keyword in url.lower() for keyword in [
                '/home/', '/list', '/recommend', '/channel', '/category',
                '/feed', '/index', '/banner'
            ])
            
            if not is_list_api:
                continue
            
            # Get response
            try:
                resp_text = entry['response']['content'].get('text', '')
                if not resp_text:
                    continue
                
                data = json.loads(resp_text)
                
                # Search for our book IDs in response
                data_str = json.dumps(data)
                
                for book_id in target_ids:
                    if book_id not in data_str:
                        continue
                    
                    # Found! Now extract the book data
                    def find_book_data(obj, book_id):
                        """Recursively find book object"""
                        if isinstance(obj, dict):
                            if str(obj.get('bookId')) == book_id or str(obj.get('id')) == book_id:
                                return obj
                            for v in obj.values():
                                result = find_book_data(v, book_id)
                                if result:
                                    return result
                        elif isinstance(obj, list):
                            for item in obj:
                                result = find_book_data(item, book_id)
                                if result:
                                    return result
                        return None
                    
                    book_data = find_book_data(data, book_id)
                    
                    if book_data:
                        cover_url = book_data.get('coverImg', '') or book_data.get('cover', '')
                        
                        if cover_url and book_id not in covers_found:
                            covers_found[book_id] = cover_url
                            print(f"  ✅ Found {book_id} in API: {url.split('?')[0]}")
                            print(f"     Cover URL: {cover_url}")
                            print()
            
            except Exception as e:
                continue
    
    print("="*80)
    print("📊 RESULTS:")
    print("="*80 + "\n")
    
    for book_id in target_ids:
        if book_id in covers_found:
            print(f"✅ {book_id}: {covers_found[book_id]}")
        else:
            print(f"❌ {book_id}: NOT FOUND in home feed")
    
    return covers_found


def download_home_feed_covers():
    """Download cover from home feed"""
    
    covers = find_home_feed_covers()
    
    if not covers:
        print("\n⚠️  No covers found in home feed!")
        print("Please browse to HOME page in app and capture new HAR")
        return
    
    print("\n" + "="*80)
    print("📥 DOWNLOADING HOME FEED COVERS:")
    print("="*80 + "\n")
    
    r2_ready = Path("r2_ready")
    
    mapping = {  
        '31001045572': 'Cinta_di_Waktu_yang_Tepat',
        '31001070612': 'Hidup_Kedua,_Cinta_Sejati_Menanti'
    }
    
    for book_id, cover_url in covers.items():
        folder_name = mapping.get(book_id)
        if not folder_name:
            continue
        
        drama_folder = r2_ready / folder_name
        if not drama_folder.exists():
            continue
        
        print(f"📁 {folder_name}")
        print(f"   URL: {cover_url[:80]}...")
        
        # Download
        poster_path = drama_folder / 'poster_home_feed.jpg'
        
        try:
            resp = requests.get(cover_url, timeout=15)
            resp.raise_for_status()
            
            with open(poster_path, 'wb') as f:
                f.write(resp.content)
            
            size_kb = len(resp.content) / 1024
            print(f"   ✅ Downloaded: {size_kb:.1f} KB → poster_home_feed.jpg")
            
            # Also save as poster.jpg
            final_poster = drama_folder / 'poster.jpg'
            with open(final_poster, 'wb') as f:
                f.write(resp.content)
            print(f"   ✅ Saved as: poster.jpg (FINAL)")
        
        except Exception as e:
            print(f"   ❌ Error: {e}")
        
        print()


if __name__ == "__main__":
    download_home_feed_covers()
