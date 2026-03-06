#!/usr/bin/env python3
"""
Episode-HLS Combiner
====================

Combines episode numbers with captured HLS URLs based on sequential tapping
"""

# Based on observed Frida captures, HLS pattern is:
# https://v2-akm.goodreels.com/mts/books/{book_id_part}/{full_book_id}/{episode_id}/{hash}/720p/{hash}_720p.m3u8

# Example from captures:
# Book ID: 31001160993
# Episode ID: 572654
# HLS: https://v2-akm.goodreels.com/mts/books/993/31001160993/572654/nebouzpinv/720p/ghlekogur4_720p.m3u8

# Since Frida captured HLS URLs during episode taps, we can map them sequentially

import json
from pathlib import Path

SCRIPT_DIR = Path(__file__).parent

def combine_episode_data():
    """
    Combines episode numbers with HLS URLs
    """
    
    print("\n" + "="*70)
    print("📊 Episode-HLS Data Combiner")
    print("="*70 + "\n")
    
    # Sample structure based on what we know works
    drama_data = {
        "bookId": "31001160993",  # From Frida captures
        "title": "Drama Title",
        "description": "Drama description",
        "totalEpisodes": 20,
        "coverUrl": "https://acf.goodreels.com/videobook/202510/cover-uqBw0xaL1J.jpg",
        "episodes": []
    }
    
    # Generate episode structure
    # In production, this would come from Frida captures
    for i in range(1, 21):
        episode = {
            "episodeNumber": i,
            "title": f"Episode {i}",
            "hlsUrl": None  # Will be filled from Frida captures
        }
        drama_data["episodes"].append(episode)
    
    # Save structure
    output_file = SCRIPT_DIR / "combined_episode_data.json"
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(drama_data, f, indent=2, ensure_ascii=False)
    
    print(f"✅ Combined data structure created")
    print(f"📁 {output_file}")
    print(f"\nEpisodes: {len(drama_data['episodes'])}")
    print("\n" + "="*70 + "\n")

if __name__ == "__main__":
    combine_episode_data()
