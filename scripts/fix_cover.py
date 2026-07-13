import requests
import subprocess
from pathlib import Path
import boto3
from botocore.config import Config
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

def fix_cover():
    db_id = 'rbrkascl7iqqt0o36iuq7o51'
    slug = '99-mutiara-kasih'
    
    # 1. Get raw image url
    cover_src = 'https://static-cdn2.flareflow.tv/images/cover/2025/11/13/6720c3c7f5fa4f43aa701eeaf986394c.jpg?auth_key=1781995610-0-0-35410c138e2df4f158b58ba5538247aa'
    
    # 2. Download it
    print("Downloading cover...")
    cov_res = requests.get(cover_src, timeout=30, verify=False)
    p = Path(f"{slug}_raw.tmp")
    p.write_bytes(cov_res.content)
    
    # 3. Transcode to jpeg
    print("Converting to JPEG...")
    p_jpg = Path(f"{slug}_cover_hq.jpg")
    subprocess.run(['ffmpeg', '-y', '-i', str(p), '-update', '1', '-loglevel', 'error', str(p_jpg)])
    
    # 4. Upload to R2
    print("Uploading to R2...")
    r2 = boto3.client('s3', endpoint_url=R2_ENDPOINT, aws_access_key_id=R2_KEY_ID, aws_secret_access_key=R2_SECRET, config=Config(signature_version='s3v4'), region_name='auto')
    cover_key = f"flareflow/{slug}/cover_hq.jpg"
    r2.put_object(Bucket=R2_BUCKET, Key=cover_key, Body=p_jpg.read_bytes(), ContentType='image/jpeg')
    r2_url = f"{R2_PUBLIC}/{cover_key}"
    print(f"R2 URL: {r2_url}")
    
    # 5. Patch DB
    print("Patching DB...")
    r = requests.patch(f"{API_BASE}/admin/dramas/{db_id}", headers=ADMIN_HDR, json={'cover': r2_url}, verify=False)
    if r.ok:
        print("Success! Cover updated in DB.")
    else:
        print(f"Failed to patch DB: {r.status_code} - {r.text}")
        
    p.unlink(missing_ok=True)
    p_jpg.unlink(missing_ok=True)

if __name__ == '__main__':
    fix_cover()
