#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
KingShort Batch Scraper for Specific DramaWaveV2 Dramas
========================================================
Scrapes a list of requested DramaWaveV2 dramas sequentially.
"""
import sys
import time
from pathlib import Path

# Force UTF-8 output
sys.stdout.reconfigure(encoding='utf-8')

# Add scripts directory to path to import scrape_dramawavev2_provider
scripts_dir = str(Path(__file__).parent.resolve())
if scripts_dir not in sys.path:
    sys.path.append(scripts_dir)

from scrape_dramawavev2_provider import scrape_single_drama, get_r2

def main():
    r2 = get_r2()
    
    dramas = [
        {"id": "DZ7ojuOfG1", "title": "Putra Sakti Pembawa Rezeki"},
        {"id": "Fhw9lPgepN", "title": "Mata Ilahi Penguasa Kota"},
        {"id": "VVgygnCkFl", "title": "Nafsu Gelap"}
    ]
    
    print(f"Starting specific DramaWaveV2 dramas scraping for {len(dramas)} dramas sequentially...")
    
    for idx, d in enumerate(dramas):
        print(f"\n==================================================")
        print(f"Processing Drama {idx+1}/{len(dramas)}: '{d['title']}' (ID: {d['id']})")
        print(f"==================================================")
        
        try:
            success = scrape_single_drama(r2, d['id'])
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
    print("FINISHED ALL SPECIFIC DRAMAWAVEV2 DRAMAS SCRAPING!")
    print("==================================================")

if __name__ == "__main__":
    main()
