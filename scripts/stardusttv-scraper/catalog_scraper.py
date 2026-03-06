#!/usr/bin/env python3
"""
StardustTV Catalog Scraper
===========================

Scrape https://www.stardusttv.net/ homepage to build catalog of all available dramas.

Extracts:
- Drama IDs
- Titles (from episode URLs)
- First episode URLs
- Unique dramas only

Output: JSON file with drama catalog
"""

import requests
from bs4 import BeautifulSoup
import json
import re
from typing import List, Dict
from pathlib import Path

class StardustTVCatalog:
    """Scraper for StardustTV drama catalog"""
    
    def __init__(self):
        self.base_url = "https://www.stardusttv.net"
        self.headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        }
    
    def scrape_homepage(self) -> List[Dict]:
        """Scrape homepage for all drama links"""
        print("🌐 Fetching StardustTV homepage...")
        
        try:
            response = requests.get(self.base_url, headers=self.headers, timeout=10)
            response.raise_for_status()
        except Exception as e:
            print(f"❌ Failed to fetch homepage: {e}")
            return []
        
        soup = BeautifulSoup(response.text, 'html.parser')
        print("✅ Homepage loaded\n")
        
        # Find all episode links
        print("🔍 Extracting drama links...")
        episode_links = soup.find_all('a', href=re.compile(r'/episodes/'))
        
        print(f"   Found {len(episode_links)} episode links\n")
        
        # Parse and deduplicate
        dramas = {}
        
        for link in episode_links:
            href = link.get('href')
            if not href:
                continue
            
            # Parse URL: /episodes/01-drama-slug-12759
            try:
                path = href.split('/')[-1]  # Get last part
                parts = path.split('-')
                
                # Extract episode number
                episode_num = parts[0]
                
                # Only process episode 01 (first episode of each drama)
                if episode_num != '01':
                    continue
                
                # Extract drama ID (last part)
                drama_id = parts[-1]
                
                # Extract slug (everything between episode num and ID)
                slug = '-'.join(parts[1:-1])
                
                # Generate title from slug
                title = ' '.join(word.capitalize() for word in slug.split('-'))
                
                # Full URL
                full_url = href if href.startswith('http') else f"{self.base_url}{href}"
                
                # Store unique dramas by ID
                if drama_id not in dramas:
                    dramas[drama_id] = {
                        'id': drama_id,
                        'slug': slug,
                        'title': title,
                        'firstEpisodeUrl': full_url,
                        'source': 'stardusttv'
                    }
                    print(f"   ✅ {title} (ID: {drama_id})")
            
            except Exception as e:
                print(f"   ⚠️  Could not parse: {href} - {e}")
                continue
        
        catalog = list(dramas.values())
        print(f"\n📊 Total unique dramas found: {len(catalog)}")
        
        return catalog
    
    def save_catalog(self, catalog: List[Dict], output_file: str = "stardusttv_catalog.json"):
        """Save catalog to JSON file"""
        output_path = Path(output_file)
        
        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump({
                'source': 'stardusttv',
                'total_dramas': len(catalog),
                'dramas': catalog
            }, f, indent=2, ensure_ascii=False)
        
        print(f"\n💾 Catalog saved to: {output_path}")
        print(f"   File size: {output_path.stat().st_size:,} bytes")

def main():
    """Main entry point"""
    print("="*70)
    print("StardustTV Catalog Scraper")
    print("="*70)
    print()
    
    scraper = StardustTVCatalog()
    
    # Scrape catalog
    catalog = scraper.scrape_homepage()
    
    if not catalog:
        print("\n❌ No dramas found!")
        return
    
    # Save to file
    scraper.save_catalog(catalog)
    
    # Print summary
    print("\n" + "="*70)
    print("✅ CATALOG COMPLETE!")
    print("="*70)
    print(f"\nTotal dramas: {len(catalog)}")
    print(f"\nSample dramas:")
    for drama in catalog[:5]:
        print(f"  - {drama['title']} (ID: {drama['id']})")
    
    if len(catalog) > 5:
        print(f"  ... and {len(catalog) - 5} more")
    
    print("\nNext step: Run drama detail scraper to get episodes and metadata!")

if __name__ == '__main__':
    main()
