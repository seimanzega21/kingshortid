import json
import subprocess
import requests
import boto3
from botocore.config import Config
from pathlib import Path
import time
import re
import urllib3
urllib3.disable_warnings()

API_BASE    = 'https://api.shortlovers.id/api'
ADMIN_KEY   = '00ca04e3e2702be565d7bf44e783255247708289bce9b2fb6187a2e117f87fd14'
ADMIN_HDR   = {'x-admin-key': ADMIN_KEY, 'Content-Type': 'application/json'}

R2_ENDPOINT = 'https://a142d3b29a5d64943cb251157e25eaf3.r2.cloudflarestorage.com'
R2_KEY_ID   = '07c99c897986ea52703c1285308d5e2c'
R2_SECRET   = '44788d376ffb216e1e73784b6fe1ff1423607928898a87c50819b52cdfc12e44'
R2_BUCKET   = 'shortlovers'
R2_PUBLIC   = 'https://stream.shortlovers.id'

s3 = boto3.client('s3', endpoint_url=R2_ENDPOINT,
                  aws_access_key_id=R2_KEY_ID, aws_secret_access_key=R2_SECRET,
                  config=Config(signature_version='s3v4'), region_name='auto')

TEMP_DIR = Path('temp_covers')
TEMP_DIR.mkdir(exist_ok=True)

def slugify(text):
    text = text.lower()
    return re.sub(r'[\W_]+', '-', text).strip('-')

with open('broken_covers.json', 'r', encoding='utf-8') as f:
    broken_list = json.load(f)

print(f"Total broken covers to fix: {len(broken_list)}")

# Test first 3 dramas
test_items = broken_list[:3]
for item in test_items:
    did = item['id']
    title = item['title']
    slug = slugify(title)
    print(f"\n--- Testing fix for: {title} ({did}) ---")

    # 1. Fetch episodes
    r_eps = requests.get(f"{API_BASE}/dramas/{did}/episodes", timeout=10)
    if not r_eps.ok:
        print(f"Failed to fetch episodes: {r_eps.status_code}")
        continue
    data = r_eps.json()
    eps = data if isinstance(data, list) else data.get('episodes', [])
    if not eps:
        print("No episodes found!")
        continue

    video_url = eps[0].get('videoUrl')
    if not video_url:
        print("No videoUrl in ep 1!")
        continue

    print(f"Video URL: {video_url}")
    out_jpg = TEMP_DIR / f"{slug}_cover.jpg"

    # 2. Extract frame at second 8 (usually main characters are clearly visible)
    # Using scale=-1:720 or keeping original aspect ratio
    cmd = [
        'ffmpeg', '-y',
        '-ss', '00:00:08',
        '-i', video_url,
        '-vframes', '1',
        '-q:v', '2',
        str(out_jpg)
    ]
    res = subprocess.run(cmd, capture_output=True, text=True, timeout=30)
    if res.returncode != 0 or not out_jpg.exists() or out_jpg.stat().st_size < 1000:
        # Fallback to second 4
        cmd[2] = '00:00:04'
        res = subprocess.run(cmd, capture_output=True, text=True, timeout=30)

    if out_jpg.exists() and out_jpg.stat().st_size >= 1000:
        print(f"Frame extracted! Size: {out_jpg.stat().st_size} bytes")
        # 3. Upload to R2
        cover_key = f"dramas/covers/{slug}_cover_v2.jpg"
        s3.upload_file(str(out_jpg), R2_BUCKET, cover_key, ExtraArgs={'ContentType': 'image/jpeg'})
        new_cover_url = f"{R2_PUBLIC}/{cover_key}"
        print(f"Uploaded to R2: {new_cover_url}")

        # 4. Patch database
        patch_res = requests.patch(f"{API_BASE}/admin/dramas/{did}", headers=ADMIN_HDR, json={'cover': new_cover_url})
        print(f"DB Patch status: {patch_res.status_code}")

        # 5. Verify HTTP status of new cover
        ver = requests.head(new_cover_url)
        print(f"Verification HTTP status: {ver.status_code}")
        out_jpg.unlink(missing_ok=True)
    else:
        print("Failed to extract frame.")
