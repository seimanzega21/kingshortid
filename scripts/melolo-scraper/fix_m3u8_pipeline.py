import os
import requests
import json
import subprocess
import boto3
import time
from pathlib import Path
from dotenv import load_dotenv

# Load correct credentials 
load_dotenv('d:\\kingshortid\\scripts\\melolo-scraper\\.env')

# Setup S3
R2_ENDPOINT = os.getenv("R2_ENDPOINT")
R2_ACCESS_KEY_ID = os.getenv("R2_ACCESS_KEY_ID")
R2_SECRET_ACCESS_KEY = os.getenv("R2_SECRET_ACCESS_KEY")
R2_BUCKET = os.getenv("R2_BUCKET", "shortlovers")

if not R2_ACCESS_KEY_ID:
    print("[FATAL] R2 Credentials missing! Make sure d:\\kingshortid\\scripts\\melolo-scraper\\.env is correct.")
    exit(1)

s3 = boto3.client(
    "s3",
    endpoint_url=R2_ENDPOINT,
    aws_access_key_id=R2_ACCESS_KEY_ID,
    aws_secret_access_key=R2_SECRET_ACCESS_KEY,
)

# Admin API Setup
API_BASE = "https://api.shortlovers.id/api/admin/system"
ADMIN_KEY = "00ca04e3e2702be565d7bf44e783255247708289bce9b2fb6187a2e117f87fd14"
HEADERS = {
    "X-Admin-Key": ADMIN_KEY,
    "Content-Type": "application/json"
}

TEMP_DIR = Path("C:/tmp/microdrama_fix")
os.makedirs(TEMP_DIR, exist_ok=True)

def fetch_m3u8_episodes():
    print("[*] Fetching all m3u8 episodes from database...")
    res = requests.get(f"{API_BASE}/m3u8-episodes", headers=HEADERS)
    if res.status_code != 200:
        print(f"[ERROR] Failed to fetch episodes: {res.text}")
        return []
    
    data = res.json()
    episodes = data.get("episodes", [])
    print(f"[*] Found {len(episodes)} episodes containing m3u8 playlists!")
    return episodes

def update_episode_url(ep_id, new_url):
    res = requests.put(
        f"{API_BASE}/episodes/{ep_id}",
        headers=HEADERS,
        json={"videoUrl": new_url}
    )
    if res.status_code == 200:
        return True
    return False

def process_episode(ep):
    ep_id = ep['id']
    drama_id = ep['dramaId']
    ep_num = ep['episodeNumber']
    video_url = ep['videoUrl']
    
    print(f"\n==================================================")
    print(f"[*] Processing Drama [{drama_id}] - Episode {ep_num}...")
    print(f"[*] URL: {video_url}")
    
    output_mp4 = TEMP_DIR / f"{ep_id}.mp4"
    
    # 1. FFmpeg download and re-encode
    cmd = [
        "ffmpeg", "-y",
        "-i", video_url,
        "-c:v", "libx264", "-preset", "fast", "-crf", "23",
        "-c:a", "aac", "-b:a", "128k",
        "-movflags", "+faststart",
        str(output_mp4)
    ]
    
    try:
        subprocess.run(cmd, capture_output=True, text=True, check=True)
        size_mb = os.path.getsize(output_mp4) / (1024 * 1024)
        print(f"    [+] FFmpeg rendered MP4 successfully ({size_mb:.2f} MB)")
    except Exception as e:
        print(f"    [!] FFmpeg failed: {e}")
        return False
        
    # 2. Upload to Cloudflare R2
    # Create a clean drama slug for the R2 key (just use drama_id to avoid fetching drama title)
    r2_key = f"dramas/microdrama/{drama_id}/ep{ep_num:03d}.mp4"
    print(f"    [~] Uploading to R2: {r2_key} ...")
    
    try:
        s3.upload_file(
            Filename=str(output_mp4),
            Bucket=R2_BUCKET,
            Key=r2_key,
            ExtraArgs={
                "ContentType": "video/mp4",
                "CacheControl": "public, max-age=31536000, immutable"
            }
        )
        # Using R2 public URL
        r2_url = f"https://stream.shortlovers.id/{r2_key}"
        print(f"    [+] Upload successful! URL: {r2_url}")
        
        # 3. Update DB
        print(f"    [~] Updating database via API...")
        if update_episode_url(ep_id, r2_url):
            print(f"    [+] Database updated! Episode {ep_num} is now fixed!")
            
            # Clean up temp file
            try:
                os.remove(output_mp4)
            except:
                pass
            return True
        else:
            print(f"    [!] Failed to update database!")
            return False
            
    except Exception as e:
        print(f"    [!] R2 Upload check failed: {e}")
        return False

def main():
    eps = fetch_m3u8_episodes()
    if not eps:
        print("Nothing to process.")
        return
        
    success_count = 0
    fail_count = 0
    
    for ep in eps:
        if process_episode(ep):
            success_count += 1
        else:
            fail_count += 1
            
    print(f"\nDONE! Successfully fixed: {success_count}. Failed: {fail_count}.")

if __name__ == "__main__":
    main()
