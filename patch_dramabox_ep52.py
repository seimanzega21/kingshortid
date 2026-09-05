"""
Manual patch: Download & register Episode 52 for Hati Yang Dihancurkan (dramabox).
The dramabox API uses 1-indexed offset, so episode=51 returns the content for EP 52.
"""
import requests, boto3, subprocess, os, time
from botocore.config import Config

API_BASE  = 'http://141.11.160.187:3000'
ADMIN_KEY = '00ca04e3e2702be565d7bf44e783255247708289bce9b2fb6187a2e117f87fd14'
ADMIN_HDR = {'x-admin-key': ADMIN_KEY, 'Content-Type': 'application/json'}
R2_ENDPOINT = 'https://a142d3b29a5d64943cb251157e25eaf3.r2.cloudflarestorage.com'
R2_KEY_ID   = '07c99c897986ea52703c1285308d5e2c'
R2_SECRET   = '44788d376ffb216e1e73784b6fe1ff1423607928898a87c50819b52cdfc12e44'
R2_BUCKET   = 'shortlovers'
R2_PUBLIC   = 'https://stream.shortlovers.id'
TEMP_DIR    = 'd:/kingshortid/temp_dramabox'
os.makedirs(TEMP_DIR, exist_ok=True)

DRAMA_ID_DB = 'kjhmxxf2mk12ulrr7eqcyl8m'
DRAMA_SLUG  = 'hati-yang-dihancurkan'
BOOK_ID     = '42000025364'
EP_NO       = 52  # episode number to register in DB

HDR = {'User-Agent': 'Mozilla/5.0'}

r2 = boto3.client(
    's3', endpoint_url=R2_ENDPOINT,
    aws_access_key_id=R2_KEY_ID, aws_secret_access_key=R2_SECRET,
    config=Config(signature_version='s3v4'), region_name='auto'
)

# Fetch video URL — request episode=51 to get EP52 content (off-by-one on their API)
print(f"Fetching stream URL for EP{EP_NO} (using api episode=51)...")
r = requests.get(f'https://vidrama.asia/api/dramabox?action=stream&id={BOOK_ID}&episode=51&lang=in', headers=HDR, timeout=20)
data = r.json().get('data', {})
video_url = data.get('videoUrl') or data.get('rawVideoUrl', '')
print(f"Video URL: {video_url[:100]}")

if not video_url:
    print("ERROR: No video URL!")
    exit(1)

# Test accessibility
rt = requests.get(video_url, headers=HDR, timeout=10, stream=True)
print(f"Stream HTTP: {rt.status_code} {rt.headers.get('Content-Type','')}")
if rt.status_code != 200:
    print("ERROR: Stream not accessible!")
    exit(1)

# Download & transcode
src  = os.path.join(TEMP_DIR, f"src_ep{EP_NO:03d}.mp4")
p720 = os.path.join(TEMP_DIR, f"ep{EP_NO:03d}_720p.mp4")
p540 = os.path.join(TEMP_DIR, f"ep{EP_NO:03d}_540p.mp4")

print(f"\nDownloading source...")
res = subprocess.run(['ffmpeg', '-y', '-i', video_url, '-c', 'copy', '-loglevel', 'warning', src],
    capture_output=True, text=True, errors='ignore', timeout=300)
print("DL result:", res.returncode, f"({os.path.getsize(src)/1024/1024:.1f}MB)" if os.path.exists(src) else "FAILED")

print("Encoding 720p...")
subprocess.run(['ffmpeg', '-y', '-i', src,
    '-vf', 'scale=720:-2', '-c:v', 'libx264', '-crf', '23', '-preset', 'fast',
    '-fps_mode', 'cfr', '-af', 'aresample=async=1',
    '-maxrate', '1500k', '-bufsize', '3000k',
    '-c:a', 'aac', '-b:a', '128k', '-movflags', '+faststart', '-loglevel', 'warning', p720],
    capture_output=True, timeout=180)

print("Encoding 540p...")
subprocess.run(['ffmpeg', '-y', '-i', src,
    '-vf', 'scale=540:-2', '-c:v', 'libx264', '-crf', '26', '-preset', 'fast',
    '-fps_mode', 'cfr', '-af', 'aresample=async=1',
    '-maxrate', '1000k', '-bufsize', '2000k',
    '-c:a', 'aac', '-b:a', '96k', '-movflags', '+faststart', '-loglevel', 'warning', p540],
    capture_output=True, timeout=180)

os.remove(src)

key720 = f"dramas/{DRAMA_SLUG}/ep{EP_NO:03d}_720p.mp4"
key540 = f"dramas/{DRAMA_SLUG}/ep{EP_NO:03d}_540p.mp4"

def upload(local, key):
    mb = os.path.getsize(local)/1024/1024
    with open(local, 'rb') as f:
        r2.upload_fileobj(f, R2_BUCKET, key, ExtraArgs={'ContentType': 'video/mp4', 'CacheControl': 'public, max-age=31536000'})
    print(f"  Uploaded {os.path.basename(key)} ({mb:.1f} MB)")
    os.remove(local)
    return f"{R2_PUBLIC}/{key}"

url_720 = upload(p720, key720) if os.path.exists(p720) else None
url_540 = upload(p540, key540) if os.path.exists(p540) else None

print(f"\nRegistering EP{EP_NO} in DB...")
payload = {
    'episodeNumber': EP_NO,
    'title': f'Episode {EP_NO}',
    'videoUrl': url_720 or '',
    'videoUrl540p': url_540 or '',
    'isVip': False, 'coinPrice': 0, 'isActive': False,
}
r = requests.post(f"{API_BASE}/api/admin/dramas/{DRAMA_ID_DB}/episodes",
                  headers=ADMIN_HDR, json=payload, timeout=20)
if r.ok:
    print(f"DONE! EP{EP_NO} registered, ID: {r.json().get('id')}")
else:
    print(f"FAILED: {r.status_code} {r.text[:200]}")
