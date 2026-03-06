#!/usr/bin/env python3
"""
YT-DLP HLS DOWNLOADER
=====================

Professional HLS downloader using yt-dlp.
yt-dlp can bypass many CDN protections!

Test with known HLS URL from Jenderal Jadi Tukang Episode 1.
"""

import subprocess
import json
from pathlib import Path

# Test URL
TEST_URL = "https://v2-akm.goodreels.com/mts/books/963/31001221963/614590/t5hgdagimt/720p/viisdqecsr_720p.m3u8"

# Output
OUTPUT_DIR = Path("test_ytdlp_download")
OUTPUT_DIR.mkdir(exist_ok=True)

def test_ytdlp():
    """Test yt-dlp download"""
    
    print("="*70)
    print("YT-DLP TEST - Episode 1 Download")
    print("="*70)
    print()
    
    print(f"URL: {TEST_URL[:80]}...")
    print(f"Output: {OUTPUT_DIR}/")
    print()
    
    # yt-dlp command with various headers to mimic app
    cmd = [
        "yt-dlp",
        TEST_URL,
        "--output", str(OUTPUT_DIR / "episode_1.%(ext)s"),
        "--user-agent", "GoodShort/2.5.1 (Linux; Android 11)",
        "--add-header", "Accept: */*",
        "--add-header", "Accept-Encoding: identity",
        "--merge-output-format", "mp4",
        "--verbose"
    ]
    
    print("Running yt-dlp...")
    print()
    
    try:
        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            timeout=120
        )
        
        print(result.stdout)
        
        if result.returncode == 0:
            print()
            print("="*70)
            print("✅ SUCCESS! Video downloaded!")
            print("="*70)
            print()
            
            # Check output
            files = list(OUTPUT_DIR.glob("*"))
            for f in files:
                print(f"📁 {f.name} ({f.stat().st_size / 1024 / 1024:.2f} MB)")
            
            return True
        else:
            print()
            print("="*70)
            print("❌ FAILED")
            print("="*70)
            print()
            print("Error:")
            print(result.stderr)
            return False
            
    except Exception as e:
        print(f"❌ Error: {e}")
        return False

if __name__ == "__main__":
    success = test_ytdlp()
    
    if success:
        print()
        print("🎉 yt-dlp WORKS! Can proceed with full download!")
        print()
        print("Next steps:")
        print("  1. Create script to download all episodes")
        print("  2. Convert to HLS segments for R2")
        print("  3. Upload to R2 bucket")
    else:
        print()
        print("⚠️  yt-dlp also blocked by CDN")
        print()
        print("Fallback options:")
        print("  A. Screenrecord method (slower but 100% works)")
        print("  B. Hybrid approach (metadata + covers only)")
