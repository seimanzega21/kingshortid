"""
Auto Video URL Fetcher for GoodShort Dramas
Fetches video URLs on-demand from GoodShort API and updates metadata
"""

import json
import requests
import time
from pathlib import Path
from typing import Dict, List

class VideoURLFetcher:
    def __init__(self):
        self.base_url = "https://api-akm.goodreels.com"
        self.headers = {
            'User-Agent': 'okhttp/4.9.1',
            'Content-Type': 'application/json'
        }
        
    def fetch_video_url(self, book_id: str, chapter_id: str) -> str:
        """Fetch video URL for specific chapter"""
        # Try chapter/load endpoint
        load_url = f"{self.base_url}/hwycclientreels/chapter/load"
        
        payload = {
            "bookId": book_id,
            "chapterId": chapter_id
        }
        
        try:
            response = requests.post(load_url, json=payload, headers=self.headers, timeout=10)
            
            if response.status_code == 200:
                data = response.json()
                chapter_data = data.get('data', {})
                
                # Try multiple video URL fields
                video_url = chapter_data.get('videoUrl', '')
                if not video_url:
                    video_url = chapter_data.get('videoLink', '')
                if not video_url and 'cdnList' in chapter_data:
                    cdn_list = chapter_data.get('cdnList', [])
                    if cdn_list:
                        video_url = cdn_list[0].get('videoPath', '')
                
                return video_url
        except Exception as e:
            print(f"  ⚠️  Error fetching video URL: {e}")
        
        return ""
    
    def update_drama_videos(self, drama_path: Path, max_episodes: int = 5) -> Dict:
        """Update video URLs for a drama (fetch first N episodes)"""
        metadata_file = drama_path / "metadata.json"
        
        if not metadata_file.exists():
            return {"success": False, "error": "metadata.json not found"}
        
        with open(metadata_file, 'r', encoding='utf-8') as f:
            metadata = json.load(f)
        
        book_id = metadata.get('bookId', '')
        episodes = metadata.get('episodes', [])
        
        if not book_id or not episodes:
            return {"success": False, "error": "Missing bookId or episodes"}
        
        print(f"\n🎬 {metadata['title']}")
        print(f"   Book ID: {book_id}")
        print(f"   Total episodes: {len(episodes)}")
        print(f"   Fetching video URLs (first {max_episodes} episodes)...")
        
        updated_count = 0
        failed_count = 0
        
        for i, episode in enumerate(episodes[:max_episodes]):
            chapter_id = str(episode.get('chapterId', ''))
            chapter_name = episode.get('chapterName', f"Episode {i+1}")
            
            if not chapter_id:
                continue
            
            # Check if already has video URL
            if episode.get('video_url') and len(episode.get('video_url', '')) > 0:
                print(f"   ✓ {chapter_name}: Already has video URL")
                continue
            
            print(f"   ⏳ {chapter_name}: Fetching...", end='', flush=True)
            video_url = self.fetch_video_url(book_id, chapter_id)
            
            if video_url:
                episode['video_url'] = video_url
                updated_count += 1
                print(f" ✅")
            else:
                failed_count += 1
                print(f" ❌ Failed")
            
            # Delay to avoid rate limiting
            time.sleep(0.5)
        
        # Save updated metadata
        with open(metadata_file, 'w', encoding='utf-8') as f:
            json.dump(metadata, f, indent=2, ensure_ascii=False)
        
        return {
            "success": True,
            "drama": metadata['title'],
            "updated": updated_count,
            "failed": failed_count,
            "total_checked": min(max_episodes, len(episodes))
        }

def main():
    """Auto-fetch video URLs for all dramas in r2_ready"""
    r2_ready = Path("r2_ready")
    
    if not r2_ready.exists():
        print("❌ r2_ready directory not found!")
        return
    
    fetcher = VideoURLFetcher()
    
    # Get all drama directories
    drama_dirs = [d for d in r2_ready.iterdir() if d.is_dir()]
    
    print(f"{'='*70}")
    print(f"🎯 AUTO VIDEO URL FETCHER")
    print(f"{'='*70}")
    print(f"Found {len(drama_dirs)} dramas in r2_ready/")
    print(f"Will fetch first 5 episodes per drama for testing...")
    print()
    
    results = []
    
    for drama_dir in drama_dirs:
        try:
            result = fetcher.update_drama_videos(drama_dir, max_episodes=5)
            results.append(result)
            
            if not result['success']:
                print(f"   ❌ {drama_dir.name}: {result.get('error', 'Unknown error')}")
        except Exception as e:
            print(f"   ❌ {drama_dir.name}: Error - {e}")
            results.append({"success": False, "drama": drama_dir.name, "error": str(e)})
    
    # Summary
    print(f"\n{'='*70}")
    print(f"📊 SUMMARY")
    print(f"{'='*70}")
    
    successful = [r for r in results if r.get('success', False)]
    total_updated = sum(r.get('updated', 0) for r in successful)
    total_failed = sum(r.get('failed', 0) for r in successful)
    
    print(f"  Dramas processed: {len(results)}")
    print(f"  Successful: {len(successful)}")
    print(f"  Video URLs fetched: {total_updated}")
    print(f"  Failed: {total_failed}")
    print()
    
    if total_updated > 0:
        print("✅ Video URLs updated! Ready to re-import to database.")
    else:
        print("⚠️  No video URLs fetched. Check API access or authentication.")

if __name__ == "__main__":
    main()
