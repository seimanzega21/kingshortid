#!/usr/bin/env python3
"""
Batch Scraper for StardustTV with Indonesian Subtitles
======================================================

Safely scrapes multiple dramas with proper delays and error handling.
"""

import json
import time
from pathlib import Path
from selenium_scraper import StardustTVSeleniumScraper

def scrape_batch(drama_list, output_dir="scraped_dramas_indonesian", max_dramas=None):
    """
    Scrape a batch of dramas
    
    Args:
        drama_list: List of drama objects from catalog
        output_dir: Directory to save results
        max_dramas: Maximum number of dramas to scrape (None = all)
    """
    output_path = Path(output_dir)
    output_path.mkdir(exist_ok=True, parents=True)
    
    # Limit number if specified
    if max_dramas:
        drama_list = drama_list[:max_dramas]
    
    print("="*70)
    print(f"StardustTV Batch Scraper - Indonesian Subtitles Only")
    print("="*70)
    print(f"\nTotal dramas to scrape: {len(drama_list)}")
    print(f"Output directory: {output_path}")
    print(f"\nSafety settings:")
    print("  - 3-6 second delays between actions")
    print("  - 10 second delays between dramas")
    print("  - Only Indonesian subtitles will be saved")
    print("\n" + "="*70)
    
    input("\nPress ENTER to start scraping...")
    
    # Initialize scraper
    scraper = StardustTVSeleniumScraper(headless=False)
    
    try:
        # Start browser
        if not scraper.start_browser():
            print("\n[-] Failed to start browser. Exiting.")
            return
        
        # Login once
        print("\n[*] Logging in with VIP account...")
        if not scraper.login():
            print("\n[!] Login failed. Continuing anyway (might be already logged in)...")
        
        # Set language
        scraper.set_language_indonesian()
        
        # Track results
        total_scraped = 0
        indonesian_count = 0
        english_count = 0
        failed = []
        
        # Scrape each drama
        for i, drama_info in enumerate(drama_list, 1):
            print("\n" + "="*70)
            print(f"[{i}/{len(drama_list)}] {drama_info['title']}")
            print("="*70)
            
            try:
                # Scrape first episode to get metadata and check language
                episode_url = drama_info['firstEpisodeUrl']
                episode_data = scraper.scrape_episode_page(episode_url)
                
                if not episode_data or not episode_data.get('videoUrl'):
                    print(f"[!] Skipping - no video URL found")
                    failed.append(drama_info['title'])
                    continue
                
                # Check if Indonesian
                language = episode_data.get('language', 'unknown')
                
                if language == 'indonesian':
                    print(f"[+] INDONESIAN SUBTITLE! Saving...")
                    indonesian_count += 1
                    
                    # Build drama object
                    drama = {
                        'id': drama_info['id'],
                        'title': drama_info['title'],
                        'slug': drama_info['slug'],
                        'description': episode_data.get('description', ''),
                        'coverUrl': episode_data.get('coverUrl', ''),
                        'source': 'stardusttv',
                        'language': 'indonesian',
                        'firstEpisodeVideoUrl': episode_data['videoUrl'],
                        'episodes': []  # Will need full episode list later
                    }
                    
                    # Save to file
                    filename = output_path / f"{drama_info['slug']}.json"
                    with open(filename, 'w', encoding='utf-8') as f:
                        json.dump(drama, f, indent=2, ensure_ascii=False)
                    
                    print(f"[+] Saved to: {filename.name}")
                    total_scraped += 1
                
                elif language == 'english':
                    print(f"[-] English subtitle - SKIPPING")
                    english_count += 1
                else:
                    print(f"[?] Unknown language - SKIPPING")
                    failed.append(drama_info['title'])
                
            except Exception as e:
                print(f"[-] Error scraping: {e}")
                failed.append(drama_info['title'])
            
            # Delay between dramas (safety)
            if i < len(drama_list):
                print(f"\n[*] Waiting 10 seconds before next drama...")
                time.sleep(10)
        
        # Summary
        print("\n" + "="*70)
        print("SCRAPING COMPLETE!")
        print("="*70)
        print(f"\nResults:")
        print(f"  Indonesian subtitles: {indonesian_count}")
        print(f"  English subtitles (skipped): {english_count}")
        print(f"  Failed/Unknown: {len(failed)}")
        print(f"\nTotal saved: {total_scraped}")
        print(f"Output directory: {output_path.absolute()}")
        
        if failed:
            print(f"\nFailed dramas:")
            for title in failed:
                print(f"  - {title}")
    
    finally:
        scraper.close()


def main():
    """Main entry point"""
    # Load catalog
    catalog_file = Path("stardusttv_catalog.json")
    
    if not catalog_file.exists():
        print("[-] Catalog file not found!")
        print("[*] Run catalog_scraper.py first to generate catalog")
        return
    
    with open(catalog_file, 'r', encoding='utf-8') as f:
        catalog = json.load(f)
    
    dramas = catalog['dramas']
    
    print(f"\n[*] Loaded {len(dramas)} dramas from catalog")
    print("\nChoose mode:")
    print("  1. Test mode (scrape first 3 dramas)")
    print("  2. Small batch (scrape first 10 dramas)")
    print("  3. Full catalog (scrape all 38 dramas)")
    
    choice = input("\nYour choice (1/2/3): ").strip()
    
    if choice == '1':
        print("\n[*] Test mode: scraping first 3 dramas")
        scrape_batch(dramas, max_dramas=3)
    elif choice == '2':
        print("\n[*] Small batch mode: scraping first 10 dramas")
        scrape_batch(dramas, max_dramas=10)
    elif choice == '3':
        print("\n[*] Full catalog mode: scraping all 38 dramas")
        print("[!] This will take approximately 10-15 minutes")
        confirm = input("\nAre you sure? (yes/no): ").strip().lower()
        if confirm == 'yes':
            scrape_batch(dramas, max_dramas=None)
        else:
            print("[*] Cancelled")
    else:
        print("[-] Invalid choice")


if __name__ == '__main__':
    main()
