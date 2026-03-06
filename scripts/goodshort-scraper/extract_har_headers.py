#!/usr/bin/env python3
"""
Extract headers from HTTP Toolkit HAR export
Find .ts video segments with 200 status and extract their headers
"""

import json
import sys
from pathlib import Path

def extract_headers_from_har(har_file: Path):
    """Extract headers from first successful .ts request"""
    
    print(f"📂 Loading HAR file: {har_file.name}")
    
    with open(har_file, 'r', encoding='utf-8') as f:
        har_data = json.load(f)
    
    entries = har_data.get('log', {}).get('entries', [])
    print(f"📊 Total requests: {len(entries)}")
    
    # Find .ts requests with 200 status
    ts_requests = []
    for entry in entries:
        url = entry['request']['url']
        status = entry['response']['status']
        
        if '.ts' in url and 'goodreels.com' in url and status == 200:
            ts_requests.append(entry)
    
    print(f"🎥 Found {len(ts_requests)} successful .ts requests")
    
    if not ts_requests:
        print("\n❌ No successful .ts requests found!")
        print("   Make sure you played a video with HTTP Toolkit connected")
        return None
    
    # Use first one
    first_ts = ts_requests[0]
    url = first_ts['request']['url']
    headers = first_ts['request']['headers']
    
    print(f"\n✅ Using request:")
    print(f"   URL: {url[:80]}...")
    print(f"   Status: {first_ts['response']['status']}")
    
    # Convert headers array to dict
    headers_dict = {}
    for header in headers:
        name = header['name'].lower()
        value = header['value']
        
        # Skip some headers
        if name in ['content-length', 'connection', 'host']:
            continue
        
        headers_dict[name] = value
    
    print(f"\n📋 Extracted {len(headers_dict)} headers:")
    for key, value in headers_dict.items():
        # Mask sensitive values
        if 'token' in key or 'auth' in key or 'session' in key:
            display = value[:20] + '...' if len(value) > 20 else value
        else:
            display = value
        print(f"   {key}: {display}")
    
    return headers_dict, url

def main():
    # Check for HAR file
    script_dir = Path(__file__).parent
    
    # Try multiple locations
    possible_paths = [
        script_dir / "HTTPToolkit_2026-02-01_23-48.har",
        Path("C:/Users/Seiman/Downloads/HTTPToolkit_2026-02-01_23-48.har"),
        script_dir / "downloads" / "HTTPToolkit_2026-02-01_23-48.har",
    ]
    
    # Also check existing HAR files in scraper dir
    existing_hars = list(script_dir.glob("*.har"))
    if existing_hars:
        possible_paths.extend(sorted(existing_hars, key=lambda x: x.stat().st_mtime, reverse=True))
    
    har_file = None
    for path in possible_paths:
        if path.exists():
            har_file = path
            break
    
    if not har_file:
        print("❌ HAR file not found!")
        print("\nSearched in:")
        for p in possible_paths[:3]:
            print(f"  - {p}")
        return
    
    # Extract headers
    result = extract_headers_from_har(har_file)
    if not result:
        return
    
    headers_dict, sample_url = result
    
    # Save headers
    output_file = script_dir / "http_toolkit_headers.json"
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(headers_dict, f, indent=2)
    
    print(f"\n✅ Headers saved to: {output_file}")
    
    # Save sample URL for testing
    url_file = script_dir / "sample_video_url.txt"
    with open(url_file, 'w', encoding='utf-8') as f:
        f.write(sample_url)
    
    print(f"✅ Sample URL saved to: {url_file}")
    
    print("\n🎯 Next steps:")
    print("   Test download:")
    print(f"   python download_with_http_toolkit.py --test-url \"{sample_url[:60]}...\"")

if __name__ == "__main__":
    main()
