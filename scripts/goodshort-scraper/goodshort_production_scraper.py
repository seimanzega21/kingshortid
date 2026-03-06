"""
GoodShort Production Scraper
Processes HTTP Toolkit HAR file and downloads all content
"""

import json
import requests
import os
from pathlib import Path
from typing import Dict, List
from urllib.parse import urlparse
import time

class GoodShortProductionScraper:
    def __init__(self, har_file: str):
        self.har_file = har_file
        self.output_dir = Path("r2_ready")
        self.session = requests.Session()
        
        # Load token
        from token_manager import GoodShortTokenManager
        self.token_manager = GoodShortTokenManager()
        if not self.token_manager.load_tokens():
            self.token_manager.extract_from_har(har_file)
        
        self.headers = {
            "authorization": self.token_manager.get_auth_header(),
            "user-agent": "okhttp/4.10.0"
        }
        
    def load_har(self) -> Dict:
        """Load HAR file"""
        print(f"📂 Loading {self.har_file}...")
        with open(self.har_file, 'r', encoding='utf-8') as f:
            return json.load(f)
    
    def extract_dramas_from_har(self, har: Dict) -> List[Dict]:
        """Extract drama metadata from HAR"""
        print("🔍 Extracting drama metadata...")
        
        entries = har['log']['entries']
        dramas = {}
        
        for entry in entries:
            url = entry['request']['url']
            
            # Find chapter/list calls (has episode data)
            if '/chapter/list' in url:
                try:
                    resp_text = entry['response']['content'].get('text', '')
                    if not resp_text:
                        continue
                    
                    data = json.loads(resp_text)
                    if 'data' not in data or 'list' not in data['data']:
                        continue
                    
                    episodes = data['data']['list']
                    
                    # Get book ID from request
                    req_body = json.loads(entry['request']['postData']['text'])
                    book_id = req_body.get('bookId')
                    
                    if book_id and book_id not in dramas:
                        # Try to get book info
                        book_info = data['data'].get('bookInfo', {})
                        
                        dramas[book_id] = {
                            'bookId': book_id,
                            'title': book_info.get('bookName', f'Drama_{book_id}'),
                            'cover': book_info.get('coverImg', ''),
                            'description': book_info.get('introduction', ''),
                            'total_episodes': len(episodes),
                            'episodes': []
                        }
                    
                    if book_id:
                        # Add episodes
                        for ep in episodes:
                            episode_data = {
                                'id': ep.get('id'),
                                'chapterName': ep.get('chapterName'),
                                'index': ep.get('index', 0),
                                'playTime': ep.get('playTime', 0),
                                'cdnList': ep.get('cdnList', [])
                            }
                            
                            # Get video URL
                            if episode_data['cdnList']:
                                cdn = episode_data['cdnList'][0]
                                video_path = cdn.get('videoPath', '')
                                episode_data['video_url'] = video_path
                            
                            dramas[book_id]['episodes'].append(episode_data)
                        
                        # Sort episodes by index
                        dramas[book_id]['episodes'].sort(key=lambda x: x.get('index', 0))
                
                except Exception as e:
                    print(f"  Warning: Error parsing entry: {e}")
                    continue
        
        result = list(dramas.values())
        print(f"✅ Found {len(result)} dramas")
        for d in result:
            print(f"  📚 {d['title']}: {d['total_episodes']} episodes")
        
        return result
    
    def download_file(self, url: str, output_path: Path) -> bool:
        """Download file with progress"""
        try:
            output_path.parent.mkdir(parents=True, exist_ok=True)
            
            resp = self.session.get(url, stream=True, timeout=30)
            resp.raise_for_status()
            
            total_size = int(resp.headers.get('content-length', 0))
            
            with open(output_path, 'wb') as f:
                if total_size == 0:
                    f.write(resp.content)
                else:
                    downloaded = 0
                    for chunk in resp.iter_content(chunk_size=8192):
                        if chunk:
                            f.write(chunk)
                            downloaded += len(chunk)
                            
                            # Progress
                            percent = (downloaded / total_size) * 100
                            print(f"\r    {percent:.1f}% ({downloaded}/{total_size} bytes)", end='')
            
            print(f"\r    ✅ Downloaded: {output_path.name}")
            return True
            
        except Exception as e:
            print(f"\r    ❌ Error: {e}")
            return False
    
    def process_dramas(self, dramas: List[Dict]):
        """Download and organize all content"""
        print(f"\n📥 Processing {len(dramas)} dramas...")
        
        for drama in dramas:
            book_id = drama['bookId']
            title = drama['title']
            
            print(f"\n{'='*60}")
            print(f"📚 {title} ({book_id})")
            print(f"{'='*60}")
            
            # Create drama folder
            drama_dir = self.output_dir / book_id
            drama_dir.mkdir(parents=True, exist_ok=True)
            
            # Save metadata
            metadata_file = drama_dir / 'metadata.json'
            with open(metadata_file, 'w', encoding='utf-8') as f:
                json.dump(drama, f, ensure_ascii=False, indent=2)
            print(f"  ✅ Metadata saved")
            
            # Download cover
            if drama['cover']:
                cover_url = drama['cover']
                cover_ext = Path(urlparse(cover_url).path).suffix or '.jpg'
                cover_path = drama_dir / f'cover{cover_ext}'
                
                print(f"  📸 Downloading cover...")
                self.download_file(cover_url, cover_path)
            
            # Download episodes
            print(f"  🎬 Downloading {len(drama['episodes'])} episodes...")
            
            for ep in drama['episodes']:
                ep_index = ep.get('index', 0)
                ep_name = ep.get('chapterName', f'ep{ep_index}')
                video_url = ep.get('video_url', '')
                
                if not video_url:
                    print(f"    ⚠️  Episode {ep_index}: No video URL")
                    continue
                
                # Create episode folder
                ep_dir = drama_dir / f"episode_{ep_index:03d}"
                ep_dir.mkdir(parents=True, exist_ok=True)
                
                # Determine file extension
                video_ext = Path(urlparse(video_url).path).suffix or '.mp4'
                video_file = ep_dir / f"video{video_ext}"
                
                if video_file.exists():
                    print(f"    ⏭️  Episode {ep_index}: Already downloaded")
                    continue
                
                print(f"    📥 Episode {ep_index}: {ep_name}")
                self.download_file(video_url, video_file)
                
                # Rate limit
                time.sleep(0.5)
        
        print(f"\n{'='*60}")
        print(f"✅ ALL DOWNLOADS COMPLETE!")
        print(f"📁 Output: {self.output_dir.absolute()}")
        print(f"{'='*60}")


def main():
    har_file = "HTTPToolkit_2026-02-02_23-24.har"
    
    if not Path(har_file).exists():
        print(f"❌ HAR file not found: {har_file}")
        return
    
    scraper = GoodShortProductionScraper(har_file)
    
    # Load and process HAR
    har = scraper.load_har()
    dramas = scraper.extract_dramas_from_har(har)
    
    if not dramas:
        print("❌ No dramas found in HAR file!")
        return
    
    # Process and download
    scraper.process_dramas(dramas)


if __name__ == "__main__":
    main()
