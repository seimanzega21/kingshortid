"""
GoodShort Direct API Scraper
Fully automated scraping without emulator - calls API directly
"""

import json
import requests
import hashlib
import time
from pathlib import Path
from typing import Dict, List, Optional

class GoodShortAPI:
    def __init__(self, auth_token: str, device_id: str):
        self.base_url =  "https://api-akm.goodreels.com/hwycclientreels"
        self.auth_token = auth_token
        self.device_id = device_id
        self.session = requests.Session()
        
        # Default headers from HAR analysis
        self.headers = {
            "authorization": f"Bearer {self.auth_token}",
            "user-agent": "okhttp/4.10.0",
            "content-type": "application/json; charset=UTF-8",
        }
    
    def _generate_sign(self, url: str, body: Dict, timestamp: int) -> str:
        """
        Generate request signature
        TODO: Reverse engineer exact signing algorithm from HAR
        For now, using placeholder - need to analyze multiple requests
        """
        # This needs to be reverse engineered from the app
        # Likely involves: timestamp + body + secret_key
        return "TODO_IMPLEMENT_SIGNING"
    
    def _make_request(self, endpoint: str, body: Dict) -> Dict:
        """Make authenticated request to GoodShort API"""
        timestamp = int(time.time() * 1000)
        url = f"{self.base_url}{endpoint}"
        
        # Add timestamp
        url_with_timestamp = f"{url}?timestamp={timestamp}"
        
        # Generate signature
        sign = self._generate_sign(url, body, timestamp)
        
        headers = {
            **self.headers,
            "sign": sign
        }
        
        try:
            resp = self.session.post(url_with_timestamp, json=body, headers=headers, timeout=30)
            resp.raise_for_status()
            return resp.json()
        except Exception as e:
            print(f"Error calling {endpoint}: {e}")
            return None
    
    def get_home_dramas(self) -> List[Dict]:
        """Get drama list from home page"""
        endpoint = "/home/index"
        body = {}
        
        result = self._make_request(endpoint, body)
        if result and "data" in result:
            return result["data"].get("list", [])
        return []
    
    def get_chapter_list(self, book_id: str) -> List[Dict]:
        """Get all episodes for a drama"""
        endpoint = "/chapter/list"
        body = {
            "latestChapterId": 0,
            "chapterCount": 0,
            "needBookInfo": False,
            "bookId": book_id
        }
        
        result = self._make_request(endpoint, body)
        if result and "data" in result:
            return result["data"].get("list", [])
        return []
    
    def get_book_detail(self, book_id: str) -> Optional[Dict]:
        """Get drama metadata"""
        endpoint = "/book/quick/open"
        body = {"bookId": book_id}
        
        result = self._make_request(endpoint, body)
        if result and "data" in result:
            return result["data"]
        return None


def extract_auth_from_har(har_file: str) -> Dict[str, str]:
    """Extract auth token and device ID from HAR file"""
    with open(har_file, 'r', encoding='utf-8') as f:
        har = json.load(f)
    
    entries = har['log']['entries']
    
    # Find first goodreels API call with auth
    for entry in entries:
        if 'api-akm.goodreels' in entry['request']['url']:
            headers = entry['request']['headers']
            
            auth = None
            for h in headers:
                if h['name'].lower() == 'authorization':
                    # Extract token from "Bearer <token>"
                    auth = h['value'].replace('Bearer ', '')
                    break
            
            if auth:
                return {
                    "auth_token": auth,
                    "device_id": "extracted_device_id_here"  # Extract from HAR
                }
    
    return {}


if __name__ == "__main__":
    print("🔍 Extracting auth from HAR...")
    auth_data = extract_auth_from_har("fresh_capture.har")
    
    if not auth_data:
        print("❌ Could not extract auth from HAR")
        exit(1)
    
    print(f"✅ Auth token: {auth_data['auth_token'][:50]}...")
    
    api = GoodShortAPI(
        auth_token=auth_data['auth_token'],
        device_id=auth_data['device_id']
    )
    
    print("\n📚 Fetching drama list...")
    dramas = api.get_home_dramas()
    print(f"Found {len(dramas)} dramas")
    
    if dramas:
        # Test with first drama
        first_drama = dramas[0]
        book_id = first_drama.get('bookId') or first_drama.get('id')
        
        print(f"\n🎬 Fetching episodes for book {book_id}...")
        chapters = api.get_chapter_list(str(book_id))
        print(f"Found {len(chapters)} episodes")
        
        if chapters:
            print("\nFirst episode sample:")
            print(json.dumps(chapters[0], ensure_ascii=False, indent=2))
