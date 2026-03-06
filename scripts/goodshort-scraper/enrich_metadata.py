"""
Fetch complete metadata from GoodShort API
Using valid auth token
"""

import json
import requests
from pathlib import Path
from token_manager import GoodShortTokenManager

def fetch_book_metadata(book_id: str, session: requests.Session, headers: dict) -> dict:
    """Fetch complete metadata for a book"""
    
    # Try different API endpoints
    endpoints = [
        {
            'url': 'https://api-akm.goodreels.com/api/book/info',
            'method': 'POST',
            'body': {'bookId': book_id}
        },
        {
            'url': 'https://api-akm.goodreels.com/api/chapter/list',
            'method': 'POST',
            'body': {'bookId': book_id, 'pageNo': 1, 'pageSize': 10}
        }
    ]
    
    for endpoint in endpoints:
        try:
            if endpoint['method'] == 'POST':
                resp = session.post(
                    endpoint['url'],
                    json=endpoint['body'],
                    headers=headers,
                    timeout=10
                )
            else:
                resp = session.get(endpoint['url'], headers=headers, timeout=10)
            
            if resp.status_code == 200:
                data = resp.json()
                
                # Check for bookInfo
                if 'data' in data:
                    book_info = data['data'].get('bookInfo', {})
                    if book_info:
                        return {
                            'title': book_info.get('bookName', ''),
                            'cover': book_info.get('coverImg', ''),
                            'description': book_info.get('introduction', ''),
                            'author': book_info.get('author', ''),
                            'category': book_info.get('category', ''),
                            'tags': book_info.get('tags', []),
                            'total_episodes': book_info.get('chapterNum', 0),
                            'playCount': book_info.get('playCount', 0),
                            'score': book_info.get('score', 0)
                        }
        except Exception as e:
            print(f"    ⚠️  API error: {e}")
            continue
    
    return {}


def enrich_metadata():
    """Enrich existing metadata with API data"""
    
    # Load token
    print("🔑 Loading auth token...")
    token_mgr = GoodShortTokenManager()
    if not token_mgr.load_tokens():
        print(" ❌ No token found!")
        return
    
    headers = {
        'authorization': token_mgr.get_auth_header(),
        'content-type': 'application/json',
        'user-agent': 'okhttp/4.10.0'
    }
    
    session = requests.Session()
    
    # Find all metadata files
    r2_ready = Path("r2_ready")
    metadata_files = list(r2_ready.glob("*/metadata.json"))
    
    print(f"📋 Found {len(metadata_files)} dramas to enrich\n")
    
    for metadata_file in metadata_files:
        # Load existing
        with open(metadata_file, 'r', encoding='utf-8') as f:
            existing = json.load(f)
        
        book_id = existing['bookId']
        current_title = existing.get('title', '')
        
        print(f"📚 {current_title or book_id}...")
        
        # Check if already has metadata
        if existing.get('cover') and existing.get('description'):
            print(f"    ✅ Already complete")
            continue
        
        # Fetch from API
        print(f"    🌐 Fetching from API...")
        api_metadata = fetch_book_metadata(book_id, session, headers)
        
        if api_metadata:
            # Merge
            existing['title'] = api_metadata['title'] or current_title
            existing['cover'] = api_metadata['cover']
            existing['description'] = api_metadata['description']
            existing['author'] = api_metadata.get('author', '')
            existing['category'] = api_metadata.get('category', '')
            existing['tags'] = api_metadata.get('tags', [])
            existing['playCount'] = api_metadata.get('playCount', 0)
            existing['score'] = api_metadata.get('score', 0)
            
            # Save
            with open(metadata_file, 'w', encoding='utf-8') as f:
                json.dump(existing, f, ensure_ascii=False, indent=2)
            
            print(f"    ✅ Title: {existing['title']}")
            print(f"    ✅ Cover: {existing['cover'][:50]}..." if existing['cover'] else "    ⚠️  No cover")
            print(f"    ✅ Description: {existing['description'][:60]}..." if existing['description'] else "    ⚠️  No description")
        else:
            print(f"    ❌ API returned no metadata")
        
        print()
    
    print("="*60)
    print("✅ Metadata enrichment complete!")
    print("="*60)


if __name__ == "__main__":
    enrich_metadata()
