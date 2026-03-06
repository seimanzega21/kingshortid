#!/usr/bin/env python3
"""
R2 UPLOADER - Upload GoodShort Data to Cloudflare R2
===================================================

Uploads scraped drama data to R2 bucket 'kingshortid'

Required env vars:
- R2_ACCOUNT_ID
- R2_ACCESS_KEY_ID
- R2_SECRET_ACCESS_KEY

Usage:
    python upload_to_r2.py
"""

import boto3
import json
import os
from pathlib import Path
from typing import List, Dict
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Configuration
SCRIPT_DIR = Path(__file__).parent
SOURCE_DIR = SCRIPT_DIR / "r2_ready"  # Updated to match our folder structure
R2_BUCKET = os.getenv("R2_BUCKET_NAME", "kingshort")

# R2 Credentials - Extract from .env
R2_ENDPOINT = os.getenv("R2_ENDPOINT", "")
R2_ACCESS_KEY_ID = os.getenv("R2_ACCESS_KEY_ID", "")
R2_SECRET_ACCESS_KEY = os.getenv("R2_SECRET_ACCESS_KEY", "")

# Extract account ID from endpoint URL
# Format: https://{ACCOUNT_ID}.r2.cloudflarestorage.com
if R2_ENDPOINT:
    R2_ACCOUNT_ID = R2_ENDPOINT.split('://')[1].split('.')[0]
else:
    R2_ACCOUNT_ID = ""

class R2Uploader:
    """Upload drama data to Cloudflare R2"""
    
    def __init__(self):
        self.uploaded_files = 0
        self.total_bytes = 0
        self.dramas_uploaded = []
        
        # Initialize S3 client for R2
        self.s3_client = boto3.client(
            's3',
            endpoint_url=f'https://{R2_ACCOUNT_ID}.r2.cloudflarestorage.com',
            aws_access_key_id=R2_ACCESS_KEY_ID,
            aws_secret_access_key=R2_SECRET_ACCESS_KEY,
            region_name='auto'
        )
    
    def get_content_type(self, file_path: Path) -> str:
        """Get content type for file"""
        ext = file_path.suffix.lower()
        content_types = {
            '.jpg': 'image/jpeg',
            '.jpeg': 'image/jpeg',
            '.png': 'image/png',
            '.json': 'application/json',
            '.m3u8': 'application/vnd.apple.mpegurl',
            '.ts': 'video/mp2t'
        }
        return content_types.get(ext, 'application/octet-stream')
    
    def upload_file(self, local_path: Path, s3_key: str) -> bool:
        """Upload single file to R2"""
        try:
            content_type = self.get_content_type(local_path)
            
            # Upload with public-read ACL
            self.s3_client.upload_file(
                str(local_path),
                R2_BUCKET,
                s3_key,
                ExtraArgs={
                    'ContentType': content_type,
                    'ACL': 'public-read'  # Make files publicly accessible
                }
            )
            
            file_size = local_path.stat().st_size
            self.uploaded_files += 1
            self.total_bytes += file_size
            
            return True
            
        except Exception as e:
            print(f"    ❌ Upload failed: {e}")
            return False
    
    def upload_drama(self, drama_folder: Path) -> Dict:
        """Upload complete drama folder to R2 (including episode subfolders)"""
        drama_id = drama_folder.name
        upload_result = {
            "drama_id": drama_id,
            "files_uploaded": 0,
            "errors": []
        }
        
        # Recursively upload all files and folders
        for item in drama_folder.rglob('*'):
            if not item.is_file():
                continue
            
            # Generate R2 path (preserve folder structure)
            relative_path = item.relative_to(drama_folder)
            s3_key = f"{drama_id}/{relative_path.as_posix()}"
            
            print(f"    📤 {relative_path}...")
            
            if self.upload_file(item, s3_key):
                upload_result["files_uploaded"] += 1
            else:
                upload_result["errors"].append(str(relative_path))
        
        return upload_result
    
    def upload_all(self):
        """Upload all dramas from r2_upload_ready"""
        if not SOURCE_DIR.exists():
            print(f"❌ Source directory not found: {SOURCE_DIR}")
            print(f"Run aggressive_scrape_to_r2.py first!")
            return
        
        # Find all drama folders
        drama_folders = [f for f in SOURCE_DIR.iterdir() if f.is_dir()]
        
        if not drama_folders:
            print(f"❌ No drama folders found in {SOURCE_DIR}")
            return
        
        print(f"✅ Found {len(drama_folders)} dramas to upload\n")
        
        # Upload each drama
        for i, folder in enumerate(drama_folders, 1):
            print(f"{'='*70}")
            print(f"📤 Uploading {i}/{len(drama_folders)}: {folder.name}")
            print(f"{'='*70}")
            
            result = self.upload_drama(folder)
            
            if result["files_uploaded"] > 0:
                print(f"  ✅ Uploaded {result['files_uploaded']} files")
                self.dramas_uploaded.append(result["drama_id"])
            
            if result["errors"]:
                print(f"  ⚠️  Errors: {len(result['errors'])} files failed")
            
            print()
        
        # Summary
        print(f"\n{'='*70}")
        print(f"✅ R2 UPLOAD COMPLETE!")
        print(f"{'='*70}")
        print(f"\n📊 Statistics:")
        print(f"  - Dramas uploaded: {len(self.dramas_uploaded)}")
        print(f"  - Files uploaded: {self.uploaded_files}")
        print(f"  - Total size: {self.total_bytes / 1024 / 1024:.2f} MB")
        print(f"\n📦 R2 Bucket: {R2_BUCKET}")
        print(f"🌐 Path: goodshort/{{drama_id}}/")
        print(f"\n💡 Public URLs:")
        for drama_id in self.dramas_uploaded:
            print(f"  https://pub-YOUR_ID.r2.dev/goodshort/{drama_id}/cover.jpg")
            print(f"  https://pub-YOUR_ID.r2.dev/goodshort/{drama_id}/metadata.json")
        print()

def check_credentials():
    """Check if R2 credentials are configured"""
    if not R2_ACCOUNT_ID or not R2_ACCESS_KEY_ID or not R2_SECRET_ACCESS_KEY:
        print("❌ R2 credentials not configured!")
        print("\nPlease set environment variables:")
        print("  - R2_ACCOUNT_ID")
        print("  - R2_ACCESS_KEY_ID")
        print("  - R2_SECRET_ACCESS_KEY")
        print("\nOr create .env file in script directory:")
        print("")
        print("R2_ACCOUNT_ID=your_account_id")
        print("R2_ACCESS_KEY_ID=your_access_key")
        print("R2_SECRET_ACCESS_KEY=your_secret_key")
        print("")
        return False
    return True

def main():
    print("\n" + "="*70)
    print("☁️  R2 UPLOADER - GoodShort to Cloudflare R2")
    print("="*70 + "\n")
    
    # Check credentials
    if not check_credentials():
        return
    
    uploader = R2Uploader()
    uploader.upload_all()

if __name__ == "__main__":
    main()
