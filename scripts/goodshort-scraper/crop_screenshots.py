#!/usr/bin/env python3
"""
Manual Crop Real Posters from Screenshots
Processes captured screenshots to extract poster covers
"""

from PIL import Image
from pathlib import Path

SCRIPT_DIR = Path(__file__).parent
TEMP_DIR = SCRIPT_DIR / "temp_screenshots"
OUTPUT_DIR = SCRIPT_DIR / "real_covers_final"

OUTPUT_DIR.mkdir(exist_ok=True)

def crop_all_screenshots():
    """Crop all screenshots to get real poster covers."""
    
    print(f"\n{'='*70}")
    print("🎯 Manual Poster Crop - From Screenshots")
    print(f"{'='*70}\n")
    
    screenshots = list(TEMP_DIR.glob("*.png"))
    
    if not screenshots:
        print(f"❌ No screenshots found in {TEMP_DIR}")
        return
    
    print(f"[*] Found {len(screenshots)} screenshots\n")
    
    for screenshot_path in sorted(screenshots):
        print(f"{'─'*70}")
        print(f"📸 {screenshot_path.name}")
        
        try:
            img = Image.open(screenshot_path)
            width, height = img.size
            
            print(f"   Screen: {width}x{height}")
            
            # Poster area coordinates
            # Based on GoodReels drama detail page layout:
            # Poster is on LEFT side, below status bar
            
            left = int(width * 0.05)       # 5% from left
            top = int(height * 0.17)        # 17% from top
            right = int(width * 0.35)       # 35% from left (30% width)  
            bottom = int(height * 0.35)     # 35% from top (18% height)
            
            print(f"   Crop: ({left},{top}) → ({right},{bottom})")
            
            poster = img.crop((left, top, right, bottom))
            
            # Convert RGBA to RGB if needed
            if poster.mode == 'RGBA':
                # Create RGB image with white background
                rgb_poster = Image.new('RGB', poster.size, (255, 255, 255))
                rgb_poster.paste(poster, mask=poster.split()[3])  # Use alpha channel as mask
                poster = rgb_poster
            
            # Save
            output_name = screenshot_path.stem + ".jpg"
            output_path = OUTPUT_DIR / output_name
            poster.save(output_path, 'JPEG', quality=95)
            
            print(f"   ✅ Saved: {output_path.name} ({poster.size[0]}x{poster.size[1]})")
            
        except Exception as e:
            print(f"   ❌ Failed: {e}")
        
        print()
    
    print(f"{'='*70}")
    print("✅ CROP COMPLETE!")
    print(f"{'='*70}\n")
    print(f"📁 Covers: {OUTPUT_DIR}/\n")

if __name__ == "__main__":
    crop_all_screenshots()
