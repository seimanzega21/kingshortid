#!/usr/bin/env python3
"""
GoodShort Fully Automated Scraper
==================================

Uses ADB UI Automator to:
1. Auto-navigate app
2. Extract drama titles, IDs, metadata from UI
3. Capture cover screenshots
4. Parse all data automatically

NO FRIDA REQUIRED - Pure ADB automation!

Requirements:
    pip install pillow pytesseract lxml
    
Usage:
    python auto_scraper_ultimate.py --dramas 10
"""

import subprocess
import json
import time
import re
from pathlib import Path
from typing import Dict, List, Any
import xml.etree.ElementTree as ET
from PIL import Image
import base64

# Configuration
SCRIPT_DIR = Path(__file__).parent
OUTPUT_DIR = SCRIPT_DIR / "automated_output"
COVERS_DIR = OUTPUT_DIR / "covers"
SCREENSHOTS_DIR = OUTPUT_DIR / "screenshots"
METADATA_FILE = OUTPUT_DIR / "scraped_metadata.json"

# Ensure directories
OUTPUT_DIR.mkdir(exist_ok=True)
COVERS_DIR.mkdir(exist_ok=True)
SCREENSHOTS_DIR.mkdir(exist_ok=True)

# ADB commands
def adb(cmd: str) -> str:
    """Execute ADB command and return output."""
    full_cmd = f"adb shell {cmd}" if not cmd.startswith("pull") else f"adb {cmd}"
    result = subprocess.run(full_cmd, shell=True, capture_output=True, text=True)
    return result.stdout.strip()

def adb_tap(x: int, y: int):
    """Tap at coordinates."""
    adb(f"input tap {x} {y}")
    time.sleep(1)

def adb_swipe(x1: int, y1: int, x2: int, y2: int, duration: int = 300):
    """Swipe gesture."""
    adb(f"input swipe {x1} {y1} {x2} {y2} {duration}")
    time.sleep(0.5)

def adb_back():
    """Press back button."""
    adb("input keyevent KEYCODE_BACK")
    time.sleep(1)

def get_ui_dump() -> ET.Element:
    """Get UI hierarchy XML."""
    adb("uiautomator dump /sdcard/window_dump.xml")
    time.sleep(0.5)
    
    # Pull to local
    subprocess.run("adb pull /sdcard/window_dump.xml .", shell=True, 
                   capture_output=True, cwd=SCRIPT_DIR)
    
    xml_path = SCRIPT_DIR / "window_dump.xml"
    if xml_path.exists():
        tree = ET.parse(xml_path)
        return tree.getroot()
    return None

def screenshot(filename: str) -> Path:
    """Take screenshot and save locally."""
    device_path = f"/sdcard/{filename}"
    adb(f"screencap -p {device_path}")
    
    local_path = SCREENSHOTS_DIR / filename
    subprocess.run(f"adb pull {device_path} {local_path}", 
                   shell=True, capture_output=True)
    
    return local_path if local_path.exists() else None

def find_nodes_by_text(root: ET.Element, text_pattern: str) -> List[ET.Element]:
    """Find UI nodes containing text pattern."""
    nodes = []
    for node in root.iter():
        text = node.get('text', '')
        if text and re.search(text_pattern, text, re.IGNORECASE):
            nodes.append(node)
    return nodes

def find_nodes_by_resource_id(root: ET.Element, resource_id: str) -> List[ET.Element]:
    """Find UI nodes by resource ID."""
    return [node for node in root.iter() 
            if resource_id in node.get('resource-id', '')]

def extract_bounds(node: ET.Element) -> tuple:
    """Extract center coordinates from bounds string."""
    bounds = node.get('bounds', '[0,0][0,0]')
    match = re.match(r'\[(\d+),(\d+)\]\[(\d+),(\d+)\]', bounds)
    if match:
        x1, y1, x2, y2 = map(int, match.groups())
        center_x = (x1 + x2) // 2
        center_y = (y1 + y2) // 2
        return (center_x, center_y, x2 - x1, y2 - y1)  # x, y, width, height
    return (0, 0, 0, 0)

def extract_drama_from_ui() -> Dict[str, Any]:
    """Extract drama metadata from current UI screen."""
    root = get_ui_dump()
    if not root:
        return None
    
    drama_data = {
        'title': None,
        'views': None,
        'tags': [],
        'description': None,
        'bookId': None
    }
    
    # Find title (usually largest text at top)
    for node in root.iter():
        text = node.get('text', '')
        resource_id = node.get('resource-id', '')
        
        # Title patterns
        if 'title' in resource_id.lower() and text:
            drama_data['title'] = text
        
        # Views pattern (contains "K" or "Ditonton")
        if text and ('ditonton' in text.lower() or re.search(r'\d+\.?\d*[KM]', text)):
            drama_data['views'] = text
        
        # Tags/genres (small clickable text)
        if text and len(text) < 30 and node.get('clickable') == 'true':
            if text not in drama_data['tags'] and text != drama_data['title']:
                drama_data['tags'].append(text)
        
        # Description (long text)
        if text and len(text) > 50:
            drama_data['description'] = text
    
    return drama_data

def get_screen_size() -> tuple:
    """Get device screen resolution."""
    output = adb("wm size")
    match = re.search(r'(\d+)x(\d+)', output)
    if match:
        return tuple(map(int, match.groups()))
    return (1080, 2400)  # Default

class AutomatedScraper:
    def __init__(self, num_dramas: int = 10):
        self.num_dramas = num_dramas
        self.scraped_data = {}
        self.screen_width, self.screen_height = get_screen_size()
        
        print(f"\n{'='*70}")
        print("🤖 GoodShort Fully Automated Scraper")
        print(f"{'='*70}\n")
        print(f"📱 Screen: {self.screen_width}x{self.screen_height}")
        print(f"🎯 Target: {num_dramas} dramas\n")
    
    def start(self):
        """Start automated scraping."""
        print("[*] Launching GoodReels app...")
        adb("am start -n com.newreading.goodreels/.MainActivity")
        time.sleep(5)  # Wait for app to load
        
        print("[*] Starting automated navigation...\n")
        
        for i in range(self.num_dramas):
            print(f"\n{'─'*70}")
            print(f"📚 Drama {i+1}/{self.num_dramas}")
            print(f"{'─'*70}\n")
            
            # Scroll to ensure drama is visible
            if i > 0:
                self.scroll_drama_list()
            
            # Get current UI state
            ui_state = get_ui_dump()
            if not ui_state:
                print("⚠️  Failed to get UI dump, skipping...")
                continue
            
            # Find and tap first drama card (adapt based on screen position)
            drama_y = 400 + (i % 3) * 350  # Navigate through different rows
            self.tap_drama_card(drama_y)
            
            # Wait for detail page to load
            time.sleep(3)
            
            # Extract metadata
            drama_data = self.extract_drama_metadata()
            
            # Capture cover screenshot
            if drama_data:
                cover_path = self.capture_cover(drama_data.get('bookId', f'drama_{i+1}'))
                drama_data['coverLocal'] = str(cover_path) if cover_path else None
            
            # Scroll to see description
            self.scroll_detail_page()
            
            # Extract additional data after scroll
            additional_data = extract_drama_from_ui()
            if additional_data and drama_data:
                drama_data.update({k: v for k, v in additional_data.items() if v and not drama_data.get(k)})
            
            # Store data
            if drama_data and drama_data.get('title'):
                book_id = drama_data.get('bookId', f'unknown_{i+1}')
                self.scraped_data[book_id] = drama_data
                
                print(f"✅ Captured: {drama_data['title']}")
                print(f"   Views: {drama_data.get('views', 'N/A')}")
                print(f"   Tags: {', '.join(drama_data.get('tags', [])[:3])}")
            
            # Go back to list
            adb_back()
            time.sleep(2)
            
            # Auto-save progress
            self.save_data()
        
        print(f"\n{'='*70}")
        print("✅ SCRAPING COMPLETE!")
        print(f"{'='*70}\n")
        self.print_summary()
    
    def scroll_drama_list(self):
        """Scroll drama list down."""
        center_x = self.screen_width // 2
        start_y = int(self.screen_height * 0.7)
        end_y = int(self.screen_height * 0.3)
        adb_swipe(center_x, start_y, center_x, end_y)
    
    def tap_drama_card(self, y_offset: int):
        """Tap drama card at specified Y position."""
        x = self.screen_width // 2
        y = min(y_offset, self.screen_height - 200)
        adb_tap(x, y)
    
    def scroll_detail_page(self):
        """Scroll detail page to see description."""
        center_x = self.screen_width // 2
        start_y = int(self.screen_height * 0.6)
        end_y = int(self.screen_height * 0.4)
        adb_swipe(center_x, start_y, center_x, end_y, 200)
        time.sleep(1)
    
    def extract_drama_metadata(self) -> Dict[str, Any]:
        """Extract drama metadata from UI."""
        data = extract_drama_from_ui()
        
        # Try to extract book ID from UI or screenshot filename pattern
        root = get_ui_dump()
        if root:
            for node in root.iter():
                content_desc = node.get('content-desc', '')
                resource_id = node.get('resource-id', '')
                
                # Look for numeric IDs in resource IDs or content descriptions
                id_match = re.search(r'(\d{11,})', f"{resource_id} {content_desc}")
                if id_match:
                    data['bookId'] = id_match.group(1)
                    break
        
        return data
    
    def capture_cover(self, book_id: str) -> Path:
        """Capture cover screenshot."""
        filename = f"cover_{book_id}.png"
        screenshot_path = screenshot(filename)
        
        if screenshot_path and screenshot_path.exists():
            # Crop to cover area (top-left quadrant typically)
            try:
                img = Image.open(screenshot_path)
                width, height = img.size
                
                # Cover usually in top 1/3 of screen, left or center
                cover_area = img.crop((50, 400, width//2 + 50, 800))
                
                cover_path = COVERS_DIR / f"{book_id}.png"
                cover_area.save(cover_path)
                
                print(f"   📸 Cover saved: {cover_path.name}")
                return cover_path
            except Exception as e:
                print(f"   ⚠️  Cover crop failed: {e}")
        
        return None
    
    def save_data(self):
        """Save scraped data to JSON."""
        with open(METADATA_FILE, 'w', encoding='utf-8') as f:
            json.dump(self.scraped_data, f, indent=2, ensure_ascii=False)
    
    def print_summary(self):
        """Print scraping summary."""
        total = len(self.scraped_data)
        complete = sum(1 for d in self.scraped_data.values() 
                      if d.get('title') and d.get('coverLocal'))
        
        print(f"📊 Total Dramas: {total}")
        print(f"✅ Complete: {complete}")
        print(f"🖼️  Covers: {len(list(COVERS_DIR.glob('*.png')))}")
        print(f"\n📁 Output:")
        print(f"   Metadata: {METADATA_FILE}")
        print(f"   Covers: {COVERS_DIR}/")
        print(f"   Screenshots: {SCREENSHOTS_DIR}/\n")

def main():
    import argparse
    
    parser = argparse.ArgumentParser(description="Fully automated GoodShort scraper")
    parser.add_argument('--dramas', type=int, default=10, 
                       help='Number of dramas to scrape (default: 10)')
    
    args = parser.parse_args()
    
    scraper = AutomatedScraper(num_dramas=args.dramas)
    scraper.start()

if __name__ == "__main__":
    main()
