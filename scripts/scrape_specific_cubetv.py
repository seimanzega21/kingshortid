#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
KingShort Scraper for Specific CubeTV Dramas
============================================
Scrapes a list of 5 requested CubeTV dramas sequentially.
"""
import sys
import time
from pathlib import Path

# Force UTF-8 output
sys.stdout.reconfigure(encoding='utf-8')

# Add scripts directory to path to import scrape_cubetv_provider
scripts_dir = str(Path(__file__).parent.resolve())
if scripts_dir not in sys.path:
    sys.path.append(scripts_dir)

from scrape_cubetv_provider import scrape_single_drama, get_r2

def main():
    r2 = get_r2()
    
    dramas = [
        {"id": "WvlqzZ", "slug": "api-fana-sekejap", "title": "Api Fana Sekejap"},
        {"id": "NZXY5a", "slug": "guru-super-2versi-dubbing", "title": "Guru Super (2Versi Dubbing)"},
        {"id": "dv3R80", "slug": "guru-super", "title": "Guru Super"},
        {"id": "VanqrZ", "slug": "kontrak-putus-mantan-menyesal", "title": "Kontrak Putus Mantan Menyesal"},
        {"id": "yv51Yv", "slug": "pikiran-didengar-ayah-jahat-lebih-kuat", "title": "Pikiran Didengar Ayah Jahat Lebih Kuat"}
    ]
    
    print(f"Starting specific CubeTV dramas scraping for {len(dramas)} dramas sequentially...")
    
    for idx, d in enumerate(dramas):
        print(f"\n==================================================")
        print(f"Processing Drama {idx+1}/{len(dramas)}: '{d['title']}' (ID: {d['id']})")
        print(f"==================================================")
        
        try:
            success = scrape_single_drama(r2, d['id'], d['slug'], d['title'])
            if success:
                print(f"[SUCCESS] Scraping completed for '{d['title']}'")
            else:
                print(f"[FAILED] Scraping failed for '{d['title']}'")
        except Exception as e:
            print(f"[ERROR] Exception processing '{d['title']}': {e}")
            
        # Cooldown between dramas to avoid IP block/rate limit
        cooldown = 15
        if idx < len(dramas) - 1:
            print(f"Cooldown: Waiting {cooldown} seconds before next drama...")
            time.sleep(cooldown)
            
    print("\n==================================================")
    print("FINISHED ALL SPECIFIC CUBETV DRAMAS SCRAPING!")
    print("==================================================")

if __name__ == "__main__":
    main()
