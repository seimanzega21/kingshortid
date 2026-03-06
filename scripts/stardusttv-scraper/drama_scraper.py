#!/usr/bin/env python3
"""
StardustTV Drama Scraper
=========================

Scrape drama details including metadata, episodes, and video URLs.

For each drama:
- Extract title, description, cover image
- Build episode list
- Extract M3U8 video URLs

Input: stardusttv_catalog.json
Output: Individual drama JSON files with complete data
"""

import requests
from bs4 import BeautifulSoup
import json
import re
import time
from pathlib import Path
from typing import Dict, List, Optional

class StardustTVDramaScraper:
    """Scraper for individual drama details"""
    
    def __init__(self):
        self.base_url = "https://www.stardusttv.net"
        self.headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        }
    
    def scrape_episode_page(self, url: str) -> Dict:
        """Scrape single episode page for metadata and video URL"""
        try:
            response = requests.get(url, headers=self.headers, timeout=10)
            response.raise_for_status()
        except Exception as e:
            print(f"      ❌ Failed to fetch: {e}")
            return {}
        
        soup = BeautifulSoup(response.text, 'html.parser')
        html_content = response.text
        
        data = {}
        
        # Extract title
        h1 = soup.find('h1')
        if h1:
            title_text = h1.text.strip()
            # Format: "Drama Title Episode 1"
            data['fullTitle'] = title_text
        
        # Extract description
        # Look for paragraph after title
        paragraphs = soup.find_all('p')
        for p in paragraphs:
            text = p.text.strip()
            if text and len(text) > 50:  # Description is usually longer
                data['description'] = text
                break
        
        # Extract M3U8 video URL
        # Pattern 1: Direct .m3u8 URL in HTML
        m3u8_match = re.search(r'https?://[^\s"\'<>]+\.m3u8[^\s"\'<>]*', html_content)
        if m3u8_match:
            data['videoUrl'] = m3u8_match.group(0)
        
        # Pattern 2: Look for video source in script tags
        if 'videoUrl' not in data:
            scripts = soup.find_all('script')
            for script in scripts:
                script_text = script.string if script.string else ''
                m3u8_match = re.search(r'https?://[^\s"\'<>]+\.m3u8[^\s"\'<>]*', script_text)
                if m3u8_match:
                    data['videoUrl'] = m3u8_match.group(0)
                    break
        
        # Extract cover image
        # Look for main image (usually largest or first img)
        img = soup.find('img')
        if img and img.get('src'):
            src = img['src']
            if src.startswith('http'):
                data['coverUrl'] = src
            elif src.startswith('/'):
                data['coverUrl'] = f"{self.base_url}{src}"
        
        return data
    
    def scrape_drama(self, drama_info: Dict, max_episodes: int = 100) -> Dict:
        """Scrape complete drama with all episodes"""
        print(f"\n{'='*70}")
        print(f"📺 {drama_info['title']}")
        print(f"{'='*70}")
        
        drama_id = drama_info['id']
        slug = drama_info['slug']
        
        # Scrape first episode for metadata
        print("   Fetching episode 1...")
        first_ep_data = self.scrape_episode_page(drama_info['firstEpisodeUrl'])
        
        if not first_ep_data:
            print("   ❌ Failed to get episode 1 data")
            return None
        
        # Build drama object
        drama = {
            'id': drama_id,
            'title': drama_info['title'],
            'slug': slug,
            'description': first_ep_data.get('description', ''),
            'coverUrl': first_ep_data.get('coverUrl', ''),
            'source': 'stardusttv',
            'episodes': []
        }
        
        print(f"   ✅ Got metadata")
        if drama['description']:
            print(f"      Description: {drama['description'][:60]}...")
        if drama['coverUrl']:
            print(f"      Cover: {drama['coverUrl'][:50]}...")
        
        # Try to detect total episodes by testing sequential episode URLs
        print(f"\n   Discovering episodes...")
        episode_count = 0
        
        for ep_num in range(1, max_episodes + 1):
            # Build episode URL
            ep_url = f"{self.base_url}/episodes/{ep_num:02d}-{slug}-{drama_id}"
            
            try:
                # Quick HEAD request to check if episode exists
                response = requests.head(ep_url, headers=self.headers, timeout=5, allow_redirects=True)
                
                if response.status_code == 200:
                    episode_count += 1
                    episode = {
                        'episodeNumber': ep_num,
                        'title': f"Episode {ep_num}",
                        'url': ep_url,
                        'videoUrl': None  # Will be filled if needed
                    }
                    
                    # Get video URL from first episode
                    if ep_num == 1 and first_ep_data.get('videoUrl'):
                        episode['videoUrl'] = first_ep_data['videoUrl']
                    
                    drama['episodes'].append(episode)
                    
                    if ep_num % 10 == 0:
                        print(f"      Episode {ep_num}...")
                
                else:
                    # Assume no more episodes after first 404
                    break
                
                # Rate limiting
                time.sleep(0.5)
            
            except Exception as e:
                break
        
        drama['totalEpisodes'] = episode_count
        print(f"\n   ✅ Found {episode_count} episodes")
        
        if first_ep_data.get('videoUrl'):
            print(f"   ✅ Video URL: {first_ep_data['videoUrl'][:60]}...")
        else:
            print(f"   ⚠️  No video URL found (may need JS rendering)")
        
        return drama
    
    def save_drama(self, drama: Dict, output_dir: Path):
        """Save drama to JSON file"""
        if not drama:
            return
        
        # Create output directory
        output_dir.mkdir(exist_ok=True, parents=True)
        
        # Sanitize filename
        safe_title = re.sub(r'[<>:"/\\|?*]', '_', drama['title'])
        filename = f"{safe_title}.json"
        
        output_file = output_dir / filename
        
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(drama, f, indent=2, ensure_ascii=False)
        
        print(f"\n   💾 Saved to: {output_file.name}")

def main():
    """Main entry point"""
    print("="*70)
    print("StardustTV Drama Scraper")
    print("="*70)
    print()
    
    # Load catalog
    catalog_file = Path("stardusttv_catalog.json")
    if not catalog_file.exists():
        print("❌ Catalog file not found! Run catalog_scraper.py first.")
        return
    
    with open(catalog_file, 'r', encoding='utf-8') as f:
        catalog_data = json.load(f)
    
    dramas = catalog_data['dramas']
    print(f"📁 Loaded {len(dramas)} dramas from catalog\n")
    
    # Test mode: scrape first 5 dramas
    test_mode = input("Test mode? (scrape first 5 dramas only) [Y/n]: ").strip().lower()
    if test_mode != 'n':
        dramas = dramas[:5]
        print(f"🧪 Test mode: scraping {len(dramas)} dramas\n")
    
    # Create output directory
    output_dir = Path("scraped_dramas")
    output_dir.mkdir(exist_ok=True)
    
    # Scrape each drama
    scraper = StardustTVDramaScraper()
    successful = 0
    
    for i, drama_info in enumerate(dramas, 1):
        print(f"\n[{i}/{len(dramas)}]")
        
        drama = scraper.scrape_drama(drama_info)
        
        if drama:
            scraper.save_drama(drama, output_dir)
            successful += 1
        
        # Rate limiting between dramas
        if i < len(dramas):
            time.sleep(2)
    
    # Summary
    print("\n" + "="*70)
    print("✅ SCRAPING COMPLETE!")
    print("="*70)
    print(f"\nTotal dramas processed: {len(dramas)}")
    print(f"Successful: {successful}")
    print(f"Failed: {len(dramas) - successful}")
    print(f"\nOutput directory: {output_dir.absolute()}")
    
    print("\nNext: Import to database!")

if __name__ == '__main__':
    main()
