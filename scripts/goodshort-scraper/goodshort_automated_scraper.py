"""
Full automation API client - ready for when we crack signing
This will be the final automated scraper
"""

import requests
import json
import time
from pathlib import Path
from typing import Optional, Dict, List

class GoodShortSigner:
    """
    Request signer - will be implemented after Frida hooking
    """
    
    def __init__(self):
        # Will contain RSA key or signing logic
        self.signing_key = None
        
    def sign_request(self, method: str, path: str, timestamp: str, body: str = "") -> str:
        """
        Generate signature for request
        To be implemented after reverse engineering
        """
        # Placeholder - will implement actual signing logic
        raise NotImplementedError("Signing not yet implemented - run Frida hook first")


class TokenManager:
    """
    Auto token refresh from HAR or API
    """
    
    def __init__(self):
        self.token = None
        self.expires_at = 0
        self.load_token()
    
    def load_token(self):
        """Load token from latest HAR file"""
        har_files = sorted(Path('.').glob('HTTPToolkit_*.har'), key=lambda x: x.stat().st_mtime, reverse=True)
        
        if not har_files:
            print("⚠️  No HAR files found")
            return
        
        latest_har = har_files[0]
        print(f"📥 Loading token from: {latest_har.name}")
        
        with open(latest_har, 'r', encoding='utf-8') as f:
            har = json.load(f)
        
        for entry in har['log']['entries']:
            for header in entry['request']['headers']:
                if header['name'].lower() == 'authorization':
                    self.token = header['value']
                    self.expires_at = time.time() + 3600  # 1 hour
                    print(f"✅ Token loaded: {self.token[:50]}...")
                    return
        
        print("❌ No token found in HAR")
    
    def get_token(self) -> str:
        """Get valid token, refresh if needed"""
        if time.time() > self.expires_at - 300:  # 5 min buffer
            print("⚠️  Token expired, refreshing...")
            self.load_token()
        
        return self.token


class GoodShortAPI:
    """
    Full API client with auto-signing and token refresh
    """
    
    def __init__(self):
        self.base_url = "https://api-akm.goodreels.com"
        self.signer = GoodShortSigner()
        self.token_manager = TokenManager()
        self.session = requests.Session()
        self.session.headers.update({
            'user-agent': 'okhttp/4.10.0',
            'content-type': 'application/json; charset=UTF-8'
        })
    
    def _make_request(self, method: str, endpoint: str, data: Optional[Dict] = None) -> Dict:
        """
        Make authenticated and signed request
        """
        timestamp = str(int(time.time() * 1000))
        url = f"{self.base_url}{endpoint}"
        
        # Get auth token
        auth_token = self.token_manager.get_token()
        
        # Prepare request
        headers = {
            'authorization': auth_token,
        }
        
        # Sign request
        body_str = json.dumps(data) if data else ""
        try:
            signature = self.signer.sign_request(method, endpoint, timestamp, body_str)
            headers['sign'] = signature
        except NotImplementedError:
            print("⚠️  Signing not implemented yet")
            # Will fail on endpoints that require signing
        
        # Make request
        params = {'timestamp': timestamp}
        
        if method == 'GET':
            resp = self.session.get(url, headers=headers, params=params)
        else:
            resp = self.session.post(url, headers=headers, params=params, json=data)
        
        resp.raise_for_status()
        return resp.json()
    
    def get_home_feed(self) -> List[Dict]:
        """Get drama list from home feed"""
        result = self._make_request('POST', '/hwycclientreels/channel/home', {})
        dramas = result.get('data', {}).get('list', [])
        return dramas
    
    def get_drama_detail(self, book_id: str) -> Dict:
        """Get full drama details"""
        result = self._make_request('POST', '/hwycclientreels/book/detail', {'bookId': book_id})
        return result.get('data', {})
    
    def get_chapter_list(self, book_id: str) -> List[Dict]:
        """Get chapter/episode list"""
        result = self._make_request('POST', '/hwycclientreels/chapter/list', {'bookId': book_id})
        chapters = result.get('data', {}).get('chapters', [])
        return chapters
    
    def get_reader_init(self, book_id: str, chapter_id: int) -> Dict:
        """Get video URLs for chapter"""
        data = {
            'bookId': book_id,
            'chapterId': chapter_id
        }
        result = self._make_request('POST', '/hwycclientreels/reader/init', data)
        return result.get('data', {})


class AutomatedScraper:
    """
    Fully automated scraper - no manual browsing needed
    """
    
    def __init__(self):
        self.api = GoodShortAPI()
        self.output_dir = Path('r2_ready_auto')
        self.output_dir.mkdir(exist_ok=True)
    
    def scrape_all(self, limit: int = 300):
        """Scrape specified number of dramas"""
        
        print("="*80)
        print(f"🚀 AUTOMATED SCRAPING - TARGET: {limit} DRAMAS")
        print("="*80 + "\n")
        
        # Get home feed
        print("📥 Fetching home feed...")
        dramas = self.api.get_home_feed()
        print(f"✅ Found {len(dramas)} dramas in feed\n")
        
        # Scrape each
        for i, drama in enumerate(dramas[:limit], 1):
            book_id = drama.get('bookId') or drama.get('id')
            title = drama.get('title', f'Drama_{book_id}')
            
            print(f"\n[{i}/{limit}] {title} (ID: {book_id})")
            print("-" * 60)
            
            try:
                # Get details
                details = self.api.get_drama_detail(book_id)
                
                # Get chapters
                chapters = self.api.get_chapter_list(book_id)
                print(f"  📺 {len(chapters)} episodes")
                
                # Create folder
                folder = self.output_dir / book_id
                folder.mkdir(exist_ok=True)
                
                # Save metadata
                metadata = {
                    'bookId': book_id,
                    'title': title,
                    'description': details.get('description', ''),
                    'cover': drama.get('coverImg', ''),
                    'episodeCount': len(chapters),
                    'chapters': chapters
                }
                
                with open(folder / 'metadata.json', 'w', encoding='utf-8') as f:
                    json.dump(metadata, f, indent=2, ensure_ascii=False)
                
                print(f"  ✅ Metadata saved")
                
                # Download videos (first episode only for now)
                if chapters:
                    chapter = chapters[0]
                    chapter_id = chapter.get('chapterId')
                    
                    print(f"  📥 Downloading episode 1...")
                    reader_data = self.api.get_reader_init(book_id, chapter_id)
                    
                    video_url = reader_data.get('content', {}).get('url', '')
                    if video_url:
                        print(f"    Video URL: {video_url[:60]}...")
                    
                time.sleep(1)  # Rate limiting
                
            except Exception as e:
                print(f"  ❌ Error: {e}")
                continue
        
        print("\n" + "="*80)
        print(f"✅ SCRAPING COMPLETE: {limit} dramas")
        print("="*80)


if __name__ == "__main__":
    print("\n🤖 GOODSHORT AUTOMATED SCRAPER\n")
    print("Status: Waiting for signing implementation...")
    print("Next: Run Frida hook to capture signing logic\n")
    
    # Test token loading
    token_mgr = TokenManager()
    
    if token_mgr.token:
        print("\n✅ Token loaded successfully!")
        print(f"Token expires in: {int((token_mgr.expires_at - time.time()) / 60)} minutes")
        
        # Try API call
        print("\n🧪 Testing API (without signing)...")
        try:
            api = GoodShortAPI()
            # This might fail if signing is required
            # dramas = api.get_home_feed()
            # print(f"✅ Got {len(dramas)} dramas")
        except Exception as e:
            print(f"⚠️  API test skipped: {e}")
    
    print("\n📝 Next steps:")
    print("1. Run Frida hook to capture signing")
    print("2. Implement GoodShortSigner.sign_request()")
    print("3. Run: python goodshort_automated_scraper.py")
