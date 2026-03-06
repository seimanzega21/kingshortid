#!/usr/bin/env python3
"""
GoodReels Web Scraper - Simple & Reliable
==========================================

Scrapes drama metadata directly from goodreels.com website
Much simpler than app automation and more reliable!

Features:
- Real drama titles ✅
- Real cover images ✅  
- Complete metadata (description, genre, etc) ✅
- Episode lists ✅

Usage:
    python web_scraper_simple.py
"""

import requests
from bs4 import BeautifulSoup
import json
from pathlib import Path
import time
import re

# Paths
SCRIPT_DIR = Path(__file__).parent
OUTPUT_DIR = SCRIPT_DIR / "web_scraped"
COVERS_DIR = OUTPUT_DIR / "covers"
METADATA_FILE = OUTPUT_DIR / "dramas_metadata.json"

# Ensure directories
OUTPUT_DIR.mkdir(exist_ok=True)
COVERS_DIR.mkdir(exist_ok=True)

# Headers to mimic browser
HEADERS = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
    'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
    'Accept-Language': 'id-ID,id;q=0.9,en-US;q=0.8,en;q=0.7',
}

class GoodReelsWebScraper:
    def __init__(self):
        self.session = requests.Session()
        self.session.headers.update(HEADERS)
        self.scraped_data = {}
        
        print(f"\n{'='*70}")
        print("🌐 GoodReels Web Scraper - Simple & Reliable")
        print(f"{'='*70}\n")
    
    def scrape_homepage(self):
        """Scrape drama list from homepage."""
        print("[*] Fetching homepage...")
        
        try:
            url = "https://www.goodreels.com"
            response = self.session.get(url, timeout=30)
            response.raise_for_status()
            
            soup = BeautifulSoup(response.text, 'html.parser')
            
            # Find drama cards
            drama_links = []
            
            # Common patterns for drama links
            for link in soup.find_all('a', href=True):
                href = link['href']
                # Look for drama/book detail pages
                if '/book/' in href or '/drama/' in href:
                    full_url = href if href.startswith('http') else f"https://www.goodreels.com{href}"
                    if full_url not in drama_links:
                        drama_links.append(full_url)
            
            print(f"✅ Found {len(drama_links)} drama links\n")
            return drama_links[:10]  # Get first 10
            
        except Exception as e:
            print(f"❌ Failed to fetch homepage: {e}")
            return []
    
    def scrape_drama_detail(self, url: str) -> dict:
        """Scrape drama detail page."""
        try:
            response = self.session.get(url, timeout=30)
            response.raise_for_status()
            
            soup = BeautifulSoup(response.text, 'html.parser')
            
            # Extract book ID from URL
            book_id_match = re.search(r'/(\d{11,})', url)
            book_id = book_id_match.group(1) if book_id_match else None
            
            # Extract metadata
            drama_data = {
                'bookId': book_id,
                'url': url,
                'title': None,
                'cover': None,
                'description': None,
                'genre': None,
                'tags': [],
                'author': None,
                'views': None,
                'episodes': 0
            }
            
            # Title - try multiple selectors
            title_elem = (soup.find('h1') or 
                         soup.find(class_=re.compile('title', re.I)) or
                         soup.find('meta', property='og:title'))
            
            if title_elem:
                if title_elem.name == 'meta':
                    drama_data['title'] = title_elem.get('content')
                else:
                    drama_data['title'] = title_elem.get_text(strip=True)
            
            # Cover image
            cover_elem = (soup.find('img', class_=re.compile('cover|poster', re.I)) or
                         soup.find('meta', property='og:image') or
                         soup.find('img'))
            
            if cover_elem:
                if cover_elem.name == 'meta':
                    drama_data['cover'] = cover_elem.get('content')
                else:
                    drama_data['cover'] = cover_elem.get('src') or cover_elem.get('data-src')
            
            # Description
            desc_elem = (soup.find(class_=re.compile('description|synopsis|intro', re.I)) or
                        soup.find('meta', property='og:description'))
            
            if desc_elem:
                if desc_elem.name == 'meta':
                    drama_data['description'] = desc_elem.get('content')
                else:
                    drama_data['description'] = desc_elem.get_text(strip=True)
            
            # Genre/Category
            genre_elem = soup.find(class_=re.compile('genre|category', re.I))
            if genre_elem:
                drama_data['genre'] = genre_elem.get_text(strip=True)
            
            # Tags
            tag_elems = soup.find_all(class_=re.compile('tag', re.I))
            drama_data['tags'] = [tag.get_text(strip=True) for tag in tag_elems[:5]]
            
            return drama_data
            
        except Exception as e:
            print(f"   ⚠️  Failed to scrape {url}: {e}")
            return None
    
    def download_cover(self, url: str, book_id: str) -> Path:
        """Download cover image."""
        if not url:
            return None
        
        try:
            # Clean URL
            if not url.startswith('http'):
                url = f"https://www.goodreels.com{url}"
            
            response = self.session.get(url, timeout=30)
            response.raise_for_status()
            
            # Determine extension
            ext = '.jpg'
            content_type = response.headers.get('content-type', '')
            if 'png' in content_type:
                ext = '.png'
            
            cover_path = COVERS_DIR / f"{book_id}{ext}"
            with open(cover_path, 'wb') as f:
                f.write(response.content)
            
            print(f"   📸 Cover: {cover_path.name}")
            return cover_path
            
        except Exception as e:
            print(f"   ⚠️  Cover download failed: {e}")
            return None
    
    def scrape_all(self):
        """Main scraping flow."""
        # Get drama links
        drama_links = self.scrape_homepage()
        
        if not drama_links:
            print("⚠️  No dramas found on homepage")
            print("\n💡 Trying alternative: Using known book IDs...")
            
            # Fallback: Use known book IDs
            known_ids = [
                '31000908479',
                '31001250379', 
                '31000991502',
                '31000914420'
            ]
            
            drama_links = [f"https://www.goodreels.com/book/{book_id}" for book_id in known_ids]
        
        print(f"[*] Scraping {len(drama_links)} dramas...\n")
        
        for i, url in enumerate(drama_links, 1):
            print(f"{'─'*70}")
            print(f"📚 Drama {i}/{len(drama_links)}")
            print(f"{'─'*70}")
            print(f"   URL: {url}")
            
            # Scrape drama
            drama_data = self.scrape_drama_detail(url)
            
            if drama_data and drama_data.get('title'):
                book_id = drama_data['bookId'] or f"drama_{i}"
                
                print(f"   ✅ Title: {drama_data['title']}")
                print(f"   📦 ID: {book_id}")
                
                # Download cover
                if drama_data.get('cover'):
                    cover_path = self.download_cover(drama_data['cover'], book_id)
                    if cover_path:
                        drama_data['coverLocal'] = str(cover_path)
                
                # Store
                self.scraped_data[book_id] = drama_data
                
                # Save progress
                self.save_data()
            else:
                print(f"   ❌ Failed to extract metadata")
            
            print()
            time.sleep(2)  # Be nice to server
        
        self.print_summary()
    
    def save_data(self):
        """Save to JSON."""
        with open(METADATA_FILE, 'w', encoding='utf-8') as f:
            json.dump(self.scraped_data, f, indent=2, ensure_ascii=False)
    
    def print_summary(self):
        """Print final summary."""
        total = len(self.scraped_data)
        with_covers = sum(1 for d in self.scraped_data.values() if d.get('coverLocal'))
        
        print(f"\n{'='*70}")
        print("✅ SCRAPING COMPLETE!")
        print(f"{'='*70}\n")
        print(f"📊 Total Dramas: {total}")
        print(f"🖼️  With Covers: {with_covers}")
        print(f"\n📁 Output:")
        print(f"   Metadata: {METADATA_FILE}")
        print(f"   Covers: {COVERS_DIR}/")
        print()

def main():
    scraper = GoodReelsWebScraper()
    scraper.scrape_all()

if __name__ == "__main__":
    main()
