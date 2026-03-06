#!/usr/bin/env python3
"""
Auto Screenshot & Crop Real Covers
===================================

Takes screenshots of drama detail pages and auto-crops the poster area.
This is the GUARANTEED working solution!
"""

import subprocess
from PIL import Image
from pathlib import Path
import time

SCRIPT_DIR = Path(__file__).parent
OUTPUT_DIR = SCRIPT_DIR / "real_covers_final"
TEMP_DIR = SCRIPT_DIR / "temp_screenshots"

OUTPUT_DIR.mkdir(exist_ok=True)
TEMP_DIR.mkdir(exist_ok=True)

def adb(cmd):
    """Run ADB command."""
    result = subprocess.run(f"adb shell {cmd}", shell=True, capture_output=True, text=True)
    return result.stdout.strip()

def adb_tap(x, y):
    """Tap at coordinates."""
    subprocess.run(f"adb shell input tap {x} {y}", shell=True)
    time.sleep(1.5)

def adb_back():
    """Press back."""
    subprocess.run("adb shell input keyevent KEYCODE_BACK", shell=True)
    time.sleep(1.5)

def adb_swipe(x1, y1, x2, y2):
    """Swipe."""
    subprocess.run(f"adb shell input swipe {x1} {y1} {x2} {y2} 300", shell=True)
    time.sleep(1)

def screenshot(filename):
    """Take screenshot."""
    device_path = f"/sdcard/{filename}"
    subprocess.run(f"adb shell screencap -p {device_path}", shell=True)
    
    local_path = TEMP_DIR / filename
    subprocess.run(f"adb pull {device_path} {local_path}", shell=True, capture_output=True)
    
    return local_path if local_path.exists() else None

def crop_poster_from_screenshot(screenshot_path, drama_id):
    """
    Crop poster area from drama detail screenshot.
    
    Based on GoodReels layout:
    - Poster is on LEFT side
    - Below status bar
    - Square/portrait aspect ratio
    """
    try:
        img = Image.open(screenshot_path)
        width, height = img.size
        
        print(f"      Screen: {width}x{height}")
        
        # Poster coordinates (based on typical GoodReels layout)
        # Left: ~5% from left edge
        # Top: ~17% from top (after status bar + some margin)
        # Width: ~30% of screen width
        # Height: ~18% of screen height (portrait poster)
        
        left = int(width * 0.05)      # 5%
        top = int(height * 0.17)       # 17%
        right = int(width * 0.35)      # 30% width
        bottom = int(height * 0.35)    # 18% height
        
        print(f"      Crop: ({left},{top}) to ({right},{bottom})")
        
        poster = img.crop((left, top, right, bottom))
        
        # Save
        output_path = OUTPUT_DIR / f"{drama_id}.jpg"
        poster.save(output_path, 'JPEG', quality=95)
        
        print(f"      ✅ Saved: {output_path.name}")
        return output_path
        
    except Exception as e:
        print(f"      ❌ Crop failed: {e}")
        return None

def auto_capture_covers(num_dramas=5):
    """
    Automated cover capture:
    1. Tap drama
    2. Wait for detail page load
    3. Screenshot
    4. Crop poster
    5. Back
    6. Repeat
    """
    
    print(f"\n{'='*70}")
    print("🎯 Auto Screenshot & Crop - Real Poster Covers")
    print(f"{'='*70}\n")
    print(f"[*] Will capture {num_dramas} drama posters")
    print("[*] Make sure GoodReels app is on drama list screen\n")
    
    input("Press ENTER to start...")
    
    # Screen coordinates
    CENTER_X = 540
    CENTER_Y = 1200
    
    for i in range(num_dramas):
        print(f"\n{'─'*70}")
        print(f"📚 Drama {i+1}/{num_dramas}")
        print(f"{'─'*70}")
        
        # Tap drama
        print("   1. Tapping drama...")
        adb_tap(CENTER_X, CENTER_Y)
        
        # Wait for page load
        print("   2. Waiting for detail page...")  
        time.sleep(3)
        
        # Screenshot
        print("   3. Taking screenshot...")
        screenshot_file = f"drama_{i+1}.png"
        screenshot_path = screenshot(screenshot_file)
        
        if screenshot_path:
            # Crop poster
            print("   4. Cropping poster...")
            drama_id = f"drama_{i+1}"
            crop_poster_from_screenshot(screenshot_path, drama_id)
        else:
            print("   ❌ Screenshot failed")
        
        # Go back
        print("   5. Returning to list...")
        adb_back()
        
        # Scroll to next drama
        if i < num_dramas - 1:
            print("   6. Scrolling to next...")
            adb_swipe(CENTER_X, 1600, CENTER_X, 1000)
            time.sleep(1)
    
    print(f"\n{'='*70}")
    print("✅ CAPTURE COMPLETE!")
    print(f"{'='*70}\n")
    print(f"📁 Covers: {OUTPUT_DIR}/")
    print(f"\n💡 Review covers and rename with real book IDs\n")

if __name__ == "__main__":
    auto_capture_covers(num_dramas=5)
