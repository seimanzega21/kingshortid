import requests
import os
import subprocess
import boto3
import json
from botocore.config import Config

API_BASE     = 'http://141.11.160.187:3000'
ADMIN_HDR    = {'x-admin-key': '00ca04e3e2702be565d7bf44e783255247708289bce9b2fb6187a2e117f87fd14', 'Content-Type': 'application/json'}
R2_ENDPOINT  = 'https://a142d3b29a5d64943cb251157e25eaf3.r2.cloudflarestorage.com'
R2_KEY_ID    = '07c99c897986ea52703c1285308d5e2c'
R2_SECRET    = '44788d376ffb216e1e73784b6fe1ff1423607928898a87c50819b52cdfc12e44'
R2_BUCKET    = 'shortlovers'
R2_PUBLIC    = 'https://stream.shortlovers.id'

def get_r2():
    return boto3.client('s3', endpoint_url=R2_ENDPOINT, aws_access_key_id=R2_KEY_ID, aws_secret_access_key=R2_SECRET, config=Config(signature_version='s3v4'), region_name='auto')

def fetch_ep3_url():
    url = f"https://vidrama.asia/en/watch/slug--31001700648/3?provider=goodshortv2&lang=in"
    hdrs = {'User-Agent': 'Mozilla/5.0', 'next-action': '6066b29df5a42ec2b7c0dabc982dc69ef60f3f5f6d'}
    r = requests.post(url, headers=hdrs, json=["31001700648", 3])
    for line in r.text.splitlines():
        if line.startswith('1:{'):
            data = json.loads(line[2:])
            return data.get('videoUrl')
    return None

def main():
    print("Fetching URL for EP 3...")
    m3u8_url = fetch_ep3_url()
    if not m3u8_url:
        print("Failed to fetch M3U8")
        return
    print(m3u8_url)
    
    local_source = "d:/kingshortid/temp_goodshort_queue/ep3_source.mp4"
    local_720 = "d:/kingshortid/temp_goodshort_queue/ep3_720p.mp4"
    local_540 = "d:/kingshortid/temp_goodshort_queue/ep3_540p.mp4"
    
    print("Downloading/Transcoding source...")
    subprocess.run(['ffmpeg', '-y', '-i', m3u8_url, '-c', 'copy', local_source])
    
    print("Transcoding 720p...")
    subprocess.run(['ffmpeg', '-y', '-i', local_source, '-vf', 'scale=720:-2', '-c:v', 'libx264', '-crf', '23', '-preset', 'fast', '-fps_mode', 'cfr', '-af', 'aresample=async=1', '-maxrate', '1500k', '-bufsize', '3000k', '-c:a', 'aac', '-b:a', '128k', '-movflags', '+faststart', local_720])
    
    print("Transcoding 540p...")
    subprocess.run(['ffmpeg', '-y', '-i', local_source, '-vf', 'scale=540:-2', '-c:v', 'libx264', '-crf', '26', '-preset', 'fast', '-fps_mode', 'cfr', '-af', 'aresample=async=1', '-maxrate', '1000k', '-bufsize', '2000k', '-c:a', 'aac', '-b:a', '96k', '-movflags', '+faststart', local_540])
    
    print("Uploading to R2...")
    r2 = get_r2()
    r2_key_720 = "dramas/kiamat-datang-aku-beli-istri/ep003_720p.mp4"
    r2_key_540 = "dramas/kiamat-datang-aku-beli-istri/ep003_540p.mp4"
    
    with open(local_720, 'rb') as f:
        r2.upload_fileobj(f, R2_BUCKET, r2_key_720, ExtraArgs={'ContentType': 'video/mp4'})
    url_720 = f"{R2_PUBLIC}/{r2_key_720}"
    
    with open(local_540, 'rb') as f:
        r2.upload_fileobj(f, R2_BUCKET, r2_key_540, ExtraArgs={'ContentType': 'video/mp4'})
    url_540 = f"{R2_PUBLIC}/{r2_key_540}"
    
    print("Registering to DB...")
    payload = {
        'episodeNumber': 3,
        'title': 'Episode 3',
        'videoUrl': url_720,
        'videoUrl540p': url_540,
        'isVip': False,
        'coinPrice': 0,
        'isActive': False,
    }
    drama_id = "u3ex27s5mcvycoxkwxvo4f0g"
    r = requests.post(f"{API_BASE}/api/admin/dramas/{drama_id}/episodes", headers=ADMIN_HDR, json=payload)
    print(r.status_code, r.text)

if __name__ == "__main__":
    main()
