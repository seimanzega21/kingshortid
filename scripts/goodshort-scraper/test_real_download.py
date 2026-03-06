#!/usr/bin/env python3
"""
Test full episode download using real HLS URL from HAR file
"""

import json
import requests
from pathlib import Path
import subprocess

SCRIPT_DIR = Path(__file__).parent
HEADERS_FILE = SCRIPT_DIR / "http_toolkit_headers.json"
TEST_OUTPUT = SCRIPT_DIR / "test_real_download"

def main():
    # Load headers
    with open(HEADERS_FILE, 'r') as f:
        headers = json.load(f)
    
    print(f"📋 Loaded headers: {list(headers.keys())}")
    
    # Find real m3u8 URL from HAR
    har_file = SCRIPT_DIR / "HTTPToolkit_2026-02-01_23-48.har"
    with open(har_file, 'r') as f:
        har_data = json.load(f)
    
    # Find first .m3u8 request
    playlist_url = None
    for entry in har_data['log']['entries']:
        url = entry['request']['url']
        if '.m3u8' in url and 'goodreels.com' in url:
            if entry['response']['status'] == 200:
                playlist_url = url
                break
    
    if not playlist_url:
        print("❌ No m3u8 URL found in HAR")
        return
    
    print(f"\n✅ Found playlist URL:")
    print(f"   {playlist_url[:80]}...")
    
    # Parse playlist
    print(f"\n📥 Fetching playlist...")
    response = requests.get(playlist_url, headers=headers, timeout=10)
    
    if response.status_code != 200:
        print(f"❌ Failed: {response.status_code}")
        return
    
    content = response.text
    print(f"✅ Playlist fetched: {len(content)} bytes")
    
    # Extract segments
    base_url = '/'.join(playlist_url.split('/')[:-1])
    segments = []
    for line in content.split('\n'):
        line = line.strip()
        if line and not line.startswith('#'):
            if line.startswith('http'):
                segments.append(line)
            else:
                segments.append(f"{base_url}/{line}")
    
    print(f"\n🎥 Found {len(segments)} segments")
    
    # Create output folder
    TEST_OUTPUT.mkdir(exist_ok=True)
    
    # Download first 5 segments as test
    print(f"\n📥 Downloading test segments (first 5)...")
    for i, segment_url in enumerate(segments[:5]):
        print(f"   [{i+1}/5] ", end='', flush=True)
        
        try:
            r = requests.get(segment_url, headers=headers, timeout=10)
            if r.status_code == 200:
                output_file = TEST_OUTPUT / f"segment_{i:06d}.ts"
                output_file.write_bytes(r.content)
                print(f"✅ {len(r.content)/1024:.1f} KB")
            else:
                print(f"❌ {r.status_code}")
        except Exception as e:
            print(f"❌ {e}")
    
    # Check downloaded files
    downloaded = list(TEST_OUTPUT.glob("segment_*.ts"))
    print(f"\n✅ Downloaded: {len(downloaded)} segments")
    
    if len(downloaded) >= 3:
        # Try to combine with ffmpeg
        print(f"\n🔧 Combining segments with ffmpeg...")
        concat_file = TEST_OUTPUT / "concat.txt"
        
        with open(concat_file, 'w') as f:
            for segment in sorted(downloaded):
                f.write(f"file '{segment.absolute()}'\n")
        
        output_video = TEST_OUTPUT / "test_video.mp4"
        cmd = [
            'ffmpeg',
            '-f', 'concat',
            '-safe', '0',
            '-i', str(concat_file),
            '-c', 'copy',
            '-y',
            str(output_video)
        ]
        
        try:
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=30)
            if result.returncode == 0 and output_video.exists():
                size_mb = output_video.stat().st_size / 1024 / 1024
                print(f"✅ Video created: {output_video.name} ({size_mb:.2f} MB)")
                print(f"\n🎯 Test video: {output_video}")
            else:
                print(f"❌ ffmpeg failed: {result.stderr[:200]}")
        except FileNotFoundError:
            print(f"⚠️  ffmpeg not found - segments downloaded but not combined")
            print(f"   Download ffmpeg: https://ffmpeg.org/download.html")
    
    print(f"\n📁 Test output: {TEST_OUTPUT}")

if __name__ == "__main__":
    main()
