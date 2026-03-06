"""
MASTER PIPELINE - Complete GoodShort Scraper
=============================================
This is the ONE script that does EVERYTHING:
1. Capture all data (metadata + videos)
2. Download video segments
3. Combine into full videos
4. Generate HLS manifests
5. Upload to R2

Usage:
    python master_pipeline.py [--skip-capture] [--skip-upload]
"""
import sys
import os
import subprocess
from pathlib import Path

def run_step(name, command, cwd=None):
    """Run a pipeline step"""
    print("\n" + "=" * 60)
    print(f"STEP: {name}")
    print("=" * 60)
    
    result = subprocess.run(command, cwd=cwd, shell=True)
    
    if result.returncode != 0:
        print(f"[!] Step failed: {name}")
        return False
    return True

def main():
    args = sys.argv[1:]
    skip_capture = '--skip-capture' in args
    skip_upload = '--skip-upload' in args
    
    print("=" * 60)
    print("GOODSHORT MASTER PIPELINE")
    print("=" * 60)
    print("\nThis script runs the complete pipeline:")
    print("  1. Capture (metadata + videos)")
    print("  2. Parse & Download segments")  
    print("  3. Combine videos")
    print("  4. Generate HLS")
    print("  5. Upload to R2")
    print()
    
    base_dir = Path(__file__).parent
    
    # Step 1: Complete Capture
    if not skip_capture:
        print("\n[STEP 1] COMPLETE CAPTURE")
        print("-" * 40)
        print("This will:")
        print("  - Clear app cache")
        print("  - Attach Frida hooks")
        print("  - Wait for you to browse (5 min)")
        print()
        
        # Clear cache first
        subprocess.run(['adb', 'shell', 'pm', 'clear', 'com.newreading.goodreels'])
        
        # Run capture
        result = subprocess.run(['python', 'complete_capture.py'], cwd=base_dir)
        if result.returncode != 0:
            print("[!] Capture failed!")
            return
    else:
        print("\n[STEP 1] SKIPPED (--skip-capture)")
    
    # Step 2: Parse and Download
    print("\n[STEP 2] PARSE & DOWNLOAD")
    print("-" * 40)
    result = subprocess.run(['python', 'parse_and_test.py'], cwd=base_dir)
    result = subprocess.run(['python', 'download_videos.py'], cwd=base_dir)
    
    # Step 3: Combine
    print("\n[STEP 3] COMBINE VIDEOS")
    print("-" * 40)
    result = subprocess.run(['python', 'combine_videos.py'], cwd=base_dir)
    
    # Step 4: Generate HLS
    print("\n[STEP 4] GENERATE HLS")
    print("-" * 40)
    result = subprocess.run(['python', 'generate_hls.py'], cwd=base_dir)
    
    # Step 5: Upload to R2
    if not skip_upload:
        print("\n[STEP 5] UPLOAD TO R2")
        print("-" * 40)
        result = subprocess.run(['npx', 'tsx', 'src/upload-combined.ts'], cwd=base_dir, shell=True)
    else:
        print("\n[STEP 5] SKIPPED (--skip-upload)")
    
    # Summary
    print("\n" + "=" * 60)
    print("PIPELINE COMPLETE!")
    print("=" * 60)
    
    # Check results
    books_file = base_dir / 'scraped_data' / 'books_metadata.json'
    videos_dir = base_dir / 'scraped_data' / 'combined'
    hls_dir = base_dir / 'scraped_data' / 'hls'
    
    if books_file.exists():
        import json
        with open(books_file) as f:
            books = json.load(f)
        print(f"\n  Books with metadata: {len(books)}")
    
    if videos_dir.exists():
        videos = list(videos_dir.glob('*.ts'))
        print(f"  Combined videos: {len(videos)}")
    
    if hls_dir.exists():
        playlists = list(hls_dir.rglob('*.m3u8'))
        print(f"  HLS playlists: {len(playlists)}")
    
    print("\nOutput locations:")
    print(f"  Metadata: scraped_data/books_metadata.json")
    print(f"  Videos: scraped_data/combined/")
    print(f"  HLS: scraped_data/hls/")

if __name__ == '__main__':
    main()
