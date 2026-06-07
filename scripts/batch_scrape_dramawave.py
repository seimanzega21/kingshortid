#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
KingShort Batch Scraper for DramaWave Provider
==============================================
Sequentially scans DramaWave dramas, checks database for existing records,
and scrapes new dramas one by one with a delay to prevent rate limits or blocks.
"""
import sys
import time
import json
import requests
from pathlib import Path

# Add scripts directory to path to import scrape_dramawave_provider
scripts_dir = str(Path(__file__).parent.resolve())
if scripts_dir not in sys.path:
    sys.path.append(scripts_dir)

from scrape_dramawave_provider import scrape_single_drama, get_r2, check_duplicate_in_db, WEB_HDRS

def main():
    r2 = get_r2()
    
    catalog_path = Path("d:/kingshortid/scratch/dramawave_catalog.json")
    if not catalog_path.exists():
        print(f"[ERROR] Catalog file not found at {catalog_path}. Please run list_dramawave_dramas.py first.")
        return
        
    with open(catalog_path, "r", encoding="utf-8") as f:
        dramas = json.load(f)
        
    print(f"Loaded {len(dramas)} dramas from catalog.")
    
    # Filter to new dramas
    new_dramas = []
    for d in dramas:
        title = d.get("title")
        movie_id = d.get("id")
        
        # Double check duplicate in DB
        db_id = check_duplicate_in_db(title)
        if db_id:
            print(f"Skipping '{title}' (Already exists in DB with ID: {db_id})")
        else:
            new_dramas.append(d)
            
    print(f"\nTotal new dramas to scrape: {len(new_dramas)}")
    
    for idx, d in enumerate(new_dramas):
        title = d.get("title")
        movie_id = d.get("id")
        
        print(f"\n==================================================")
        print(f"Processing Drama {idx+1}/{len(new_dramas)}: '{title}' (ID: {movie_id})")
        print(f"==================================================")
        
        try:
            success = scrape_single_drama(r2, movie_id)
            if success:
                print(f"[SUCCESS] Scraping completed for '{title}'")
            else:
                print(f"[FAILED] Scraping failed for '{title}'")
        except Exception as e:
            print(f"[ERROR] Exception processing '{title}': {e}")
            
        # Cooldown between dramas to avoid blocks
        cooldown = 15
        print(f"Cooldown: Waiting {cooldown} seconds before next drama...")
        time.sleep(cooldown)

if __name__ == "__main__":
    main()
