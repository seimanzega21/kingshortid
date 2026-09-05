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
HDR = {'User-Agent': 'Mozilla/5.0'}

r2 = boto3.client(
    's3', endpoint_url=R2_ENDPOINT,
    aws_access_key_id=R2_KEY_ID, aws_secret_access_key=R2_SECRET,
    config=Config(signature_version='s3v4'), region_name='auto'
)

print("STEP 1: Shifting R2 files up by 1 (51 -> 52, 1 -> 2)...")
for i in range(51, 0, -1):
    for res in ['720p', '540p']:
        old_key = f"dramas/{DRAMA_SLUG}/ep{i:03d}_{res}.mp4"
        new_key = f"dramas/{DRAMA_SLUG}/ep{i+1:03d}_{res}.mp4"
        try:
            r2.copy_object(
                Bucket=R2_BUCKET,
                CopySource={'Bucket': R2_BUCKET, 'Key': old_key},
                Key=new_key
            )
            r2.delete_object(Bucket=R2_BUCKET, Key=old_key)
            print(f"  Moved {old_key} -> {new_key}")
        except Exception as e:
            pass # if missing, ignore

print("\nSTEP 2: Shifting DB episodes up by 1...")
er = requests.get(f"{API_BASE}/api/dramas/{DRAMA_ID_DB}/episodes", timeout=15)
eps = sorted(er.json(), key=lambda x: int(x.get('episodeNumber', 0)), reverse=True)

for ep in eps:
    old_no = int(ep.get('episodeNumber'))
    new_no = old_no + 1
    ep_id = ep['id']
    
    # Calculate new URLs
    url720 = f"{R2_PUBLIC}/dramas/{DRAMA_SLUG}/ep{new_no:03d}_720p.mp4"
    url540 = f"{R2_PUBLIC}/dramas/{DRAMA_SLUG}/ep{new_no:03d}_540p.mp4"
    
    payload = {
        'episodeNumber': new_no,
        'title': f'Episode {new_no}',
        'videoUrl': url720,
        'videoUrl540p': url540,
    }
    
    upd = requests.put(
        f"{API_BASE}/api/admin/dramas/{DRAMA_ID_DB}/episodes/{ep_id}",
        headers=ADMIN_HDR, json=payload, timeout=20
    )
    if upd.ok:
        print(f"  DB Updated: EP{old_no} -> EP{new_no}")
    else:
        # fallback to patch
        upd = requests.patch(
            f"{API_BASE}/api/admin/dramas/{DRAMA_ID_DB}/episodes/{ep_id}",
            headers=ADMIN_HDR, json=payload, timeout=20
        )
        print(f"  DB Patched: EP{old_no} -> EP{new_no} | Status: {upd.status_code}")

print("\nSTEP 3: Downloading TRUE EP 1 (api episode=0)...")
r = requests.get(
    f'https://vidrama.asia/api/dramabox?action=stream&id={BOOK_ID}&episode=0&lang=in',
    headers=HDR, timeout=20
)
data = r.json().get('data', {})
video_url = data.get('videoUrl') or data.get('rawVideoUrl', '')
print(f"  Video URL: {video_url[:100]}")

src  = os.path.join(TEMP_DIR, "src_ep001_true.mp4")
p720 = os.path.join(TEMP_DIR, "ep001_720p_true.mp4")
p540 = os.path.join(TEMP_DIR, "ep001_540p_true.mp4")

for f in [src, p720, p540]:
    if os.path.exists(f): os.remove(f)

res = subprocess.run(
    ['ffmpeg', '-y', '-i', video_url, '-c', 'copy', '-loglevel', 'warning', src],
    capture_output=True, text=True, errors='ignore', timeout=300
)

print("  Encoding 720p...")
subprocess.run(
    ['ffmpeg', '-y', '-i', src,
     '-vf', 'scale=720:-2', '-c:v', 'libx264', '-crf', '23', '-preset', 'fast',
     '-fps_mode', 'cfr', '-af', 'aresample=async=1',
     '-maxrate', '1500k', '-bufsize', '3000k',
     '-c:a', 'aac', '-b:a', '128k', '-movflags', '+faststart', '-loglevel', 'warning', p720],
    capture_output=True, timeout=180
)

print("  Encoding 540p...")
subprocess.run(
    ['ffmpeg', '-y', '-i', src,
     '-vf', 'scale=540:-2', '-c:v', 'libx264', '-crf', '26', '-preset', 'fast',
     '-fps_mode', 'cfr', '-af', 'aresample=async=1',
     '-maxrate', '1000k', '-bufsize', '2000k',
     '-c:a', 'aac', '-b:a', '96k', '-movflags', '+faststart', '-loglevel', 'warning', p540],
    capture_output=True, timeout=180
)

if os.path.exists(src): os.remove(src)

key720 = f"dramas/{DRAMA_SLUG}/ep001_720p.mp4"
key540 = f"dramas/{DRAMA_SLUG}/ep001_540p.mp4"

url_720 = url_540 = None
for local, key, label in [(p720, key720, '720p'), (p540, key540, '540p')]:
    if os.path.exists(local):
        mb = os.path.getsize(local)/1024/1024
        with open(local, 'rb') as f:
            r2.upload_fileobj(f, R2_BUCKET, key,
                ExtraArgs={'ContentType': 'video/mp4', 'CacheControl': 'public, max-age=31536000'})
        print(f"  ✅ Uploaded EP1 {label} ({mb:.1f}MB)")
        os.remove(local)
        if label == '720p': url_720 = f"{R2_PUBLIC}/{key}"
        else: url_540 = f"{R2_PUBLIC}/{key}"

print("\nSTEP 4: Registering TRUE EP1 in DB...")
payload = {
    'episodeNumber': 1,
    'title': 'Episode 1',
    'videoUrl': url_720 or '',
    'videoUrl540p': url_540 or '',
    'isVip': False, 'coinPrice': 0, 'isActive': False,
}
reg = requests.post(
    f"{API_BASE}/api/admin/dramas/{DRAMA_ID_DB}/episodes",
    headers=ADMIN_HDR, json=payload, timeout=20
)
if reg.ok:
    print(f"✅ True EP1 registered! ID: {reg.json().get('id')}")
else:
    print(f"❌ DB failed: {reg.status_code} {reg.text[:100]}")

print("\nALL FIXED!")
