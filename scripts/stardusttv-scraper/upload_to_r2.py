#!/usr/bin/env python3
"""
StardustTV to R2 Uploader
==========================

Upload StardustTV M3U8 videos to Cloudflare R2.

Strategy:
- M3U8 files are playlists, not actual videos
- For each episode, keep M3U8 URL as-is (direct link)
- Update database with R2-compatible structure
- No need to download/re-upload M3U8 (they're already hosted by StardustTV CDN)

Alternative if needed:
- Download M3U8 + all TS segments
- Re-upload to R2 for full control
"""

import json
from pathlib import Path
import boto3
from dotenv import load_dotenv
import os

# Load R2 credentials
load_dotenv(Path(__file__).parent.parent.parent / 'backend' / '.env')

def get_r2_client():
    """Create R2 client"""
    return boto3.client(
        's3',
        endpoint_url=os.getenv('R2_ENDPOINT'),
        aws_access_key_id=os.getenv('R2_ACCESS_KEY_ID'),
        aws_secret_access_key=os.getenv('R2_SECRET_ACCESS_KEY'),
        region_name='auto'
    )

def create_metadata_json(drama_data):
    """Create metadata.json for drama"""
    return {
        'title': drama_data['title'],
        'description': drama_data.get('description', ''),
        'slug': drama_data.get('slug', ''),
        'totalEpisodes': drama_data.get('totalEpisodes', 0),
        'coverUrl': drama_data.get('coverUrl', ''),
        'source': 'stardusttv',
        'country': 'USA',
        'language': 'English'
    }

def upload_to_r2(r2, drama_data, bucket_name='kingshort'):
    """
    Upload drama metadata to R2
    
    Note: M3U8 URLs are external CDN links, we keep them as-is
    Only upload metadata for organization
    """
    
    # Sanitize title for folder name
    safe_title = drama_data['title'].replace('/', '-').replace('\\', '-')
    base_path = f"stardusttv/{safe_title}"
    
    # Upload metadata
    metadata = create_metadata_json(drama_data)
    r2.put_object(
        Bucket=bucket_name,
        Key=f"{base_path}/metadata.json",
        Body=json.dumps(metadata, indent=2),
        ContentType='application/json'
    )
    
    print(f"   [R2] Uploaded metadata for {drama_data['title']}")
    
    # Create episode manifest
    episodes_manifest = []
    for ep in drama_data.get('episodes', []):
        if ep.get('videoUrl'):
            episodes_manifest.append({
                'episodeNumber': ep.get('episodeNumber'),
                'title': ep.get('title'),
                'videoUrl': ep.get('videoUrl'),  # Keep original M3U8 URL
                'duration': ep.get('duration', 0)
            })
    
    if episodes_manifest:
        r2.put_object(
            Bucket=bucket_name,
            Key=f"{base_path}/episodes.json",
            Body=json.dumps(episodes_manifest, indent=2),
            ContentType='application/json'
        )
        print(f"      - {len(episodes_manifest)} episodes manifest uploaded")
    
    return base_path

def main():
    """Main upload process"""
    print("="*70)
    print("StardustTV to R2 Upload")
    print("="*70)
    print("\n[INFO] M3U8 videos will use external CDN URLs (no re-upload needed)\n")
    
    # Find scraped dramas
    scraped_dir = Path("scraped_dramas")
    drama_files = list(scraped_dir.glob("*.json"))
    
    if not drama_files:
        print("[ERROR] No scraped dramas found!")
        return
    
    print(f"[INFO] Found {len(drama_files)} drama(s)\n")
    
    # Connect to R2
    print("[INFO] Connecting to R2...")
    try:
        r2 = get_r2_client()
        print("[OK] Connected\n")
    except Exception as e:
        print(f"[ERROR] R2 connection failed: {e}")
        return
    
    # Upload each drama
    uploaded = 0
    for drama_file in drama_files:
        print(f"[PROCESSING] {drama_file.name}")
        
        with open(drama_file, 'r', encoding='utf-8') as f:
            drama_data = json.load(f)
        
        try:
            upload_to_r2(r2, drama_data)
            uploaded += 1
        except Exception as e:
            print(f"   [ERROR] Upload failed: {e}")
    
    print(f"\n{'='*70}")
    print("[SUCCESS] UPLOAD COMPLETE!")
    print(f"{'='*70}\n")
    print(f"Uploaded: {uploaded}/{len(drama_files)} dramas")
    print("\n[NOTE] Video URLs remain on StardustTV CDN")
    print("       Metadata stored in R2 for organization\n")

if __name__ == '__main__':
    main()
