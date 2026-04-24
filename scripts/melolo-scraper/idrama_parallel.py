import os
import sys
import time
import json
import asyncio
import subprocess
from pathlib import Path
from concurrent.futures import ThreadPoolExecutor
import requests
import boto3
import re
from slugify import slugify

# Try importing playwright
try:
    from playwright.sync_api import sync_playwright
except ImportError:
    print("Please install playwright: pip install playwright && playwright install chromium")
    sys.exit(1)

# Configuration
ADMIN_KEY = "seimanzega21"
API_DRAMAS = "https://api.shortlovers.id/api/dramas"
API_EPISODES = "https://api.shortlovers.id/api/episodes"

# R2 Credentials
R2_ENDPOINT = 'https://a142d3b29a5d64943cb251157e25eaf3.r2.cloudflarestorage.com'
R2_ACCESS   = 'aebcd5da90bf6217462cc29dfce47fb5'
R2_SECRET   = 'e3e7fbbbb87ff261c6bceba462b5340ce9ba354ca790a16af616013626ca3d8f'
R2_BUCKET   = 'shortlovers'
R2_PUBLIC   = 'https://stream.shortlovers.id'

AUTH_FILE = 'idrama_auth.json'
TEMP_DIR = Path('/tmp/idrama_temp') if os.name == 'posix' else Path('./tmp_idrama')

def get_r2():
    return boto3.client('s3', endpoint_url=R2_ENDPOINT, aws_access_key_id=R2_ACCESS, aws_secret_access_key=R2_SECRET, region_name='auto')

def do_login():
    print("Launching browser for login...")
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=False)
        context = browser.new_context()
        page = context.new_page()
        page.goto("https://vidrama.asia/login")
        print("\n*** PLEASE LOGIN IN THE BROWSER WINDOW ***")
        print("*** AFTER LOGGING IN, CLOSE THE BROWSER WINDOW TO SAVE SESSION ***\n")
        page.wait_for_event("close", timeout=0)
        context.storage_state(path=AUTH_FILE)
        print(f"Session saved to {AUTH_FILE}. You can now run the scraper without --login")

def upload_to_r2(local_path, s3_key, content_type):
    r2c = get_r2()
    try:
        r2c.head_object(Bucket=R2_BUCKET, Key=s3_key)
        return True
    except:
        pass
    
    extra_args = {'ContentType': content_type}
    if content_type == 'video/mp4':
        extra_args['ContentDisposition'] = 'inline'
    
    r2c.upload_file(str(local_path), R2_BUCKET, s3_key, ExtraArgs=extra_args)
    return True

def process_episode(ep_data, drama_slug):
    # This function will be called in a ThreadPoolExecutor
    ep_num = ep_data['ep_num']
    video_url = ep_data['video_url']
    
    print(f"  [Ep {ep_num}] Downloading...")
    t_720 = TEMP_DIR / f"{drama_slug}_ep{ep_num}_720p.mp4"
    t_540 = TEMP_DIR / f"{drama_slug}_ep{ep_num}_540p.mp4"
    
    # Download
    r = requests.get(video_url, stream=True)
    with open(t_720, 'wb') as f:
        for chunk in r.iter_content(chunk_size=1024*1024):
            f.write(chunk)
            
    # Transcode 540p
    print(f"  [Ep {ep_num}] Transcoding 540p...")
    cmd = ['ffmpeg', '-y', '-i', str(t_720), '-vf', 'scale=-2:540', '-c:v', 'libx264', '-crf', '28', '-preset', 'fast', '-c:a', 'aac', '-b:a', '128k', str(t_540)]
    subprocess.run(cmd, capture_output=True)
    
    # Upload R2
    print(f"  [Ep {ep_num}] Uploading...")
    key_720 = f"dramas/idrama/{drama_slug}/ep{ep_num:03d}.mp4"
    key_540 = f"dramas/idrama/{drama_slug}/ep{ep_num:03d}_540p.mp4"
    
    upload_to_r2(t_720, key_720, 'video/mp4')
    upload_to_r2(t_540, key_540, 'video/mp4')
    
    # Insert to DB via API
    payload = {
        'dramaSlug': drama_slug,
        'episodeNumber': ep_num,
        'videoUrl': f"{R2_PUBLIC}/{key_720}",
        'videoUrl540p': f"{R2_PUBLIC}/{key_540}",
        'title': f"Episode {ep_num}"
    }
    resp = requests.post(API_EPISODES, json=payload, headers={'x-admin-key': ADMIN_KEY})
    
    t_720.unlink(missing_ok=True)
    t_540.unlink(missing_ok=True)
    print(f"  [Ep {ep_num}] Done")

def scrape_idrama():
    if not os.path.exists(AUTH_FILE):
        print(f"Auth file {AUTH_FILE} not found. Please run with --login first.")
        sys.exit(1)
        
    TEMP_DIR.mkdir(parents=True, exist_ok=True)
    
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        context = browser.new_context(storage_state=AUTH_FILE)
        page = context.new_page()
        
        print("Navigating to iDrama provider...")
        page.goto("https://vidrama.asia/provider/idrama")
        
        # NOTE: Implement actual Next.js data extraction here based on the page DOM!
        print("This is a skeleton for the scraping logic. Once we have a valid VIP login, we can inspect the DOM and complete this part!")
        
        browser.close()

if __name__ == "__main__":
    if len(sys.argv) > 1 and sys.argv[1] == '--login':
        do_login()
    else:
        scrape_idrama()
