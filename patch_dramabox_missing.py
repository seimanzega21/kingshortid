"""
Patch: Download & register Episode 1 (true) for Hati Yang Dihancurkan.
The dramabox API is 0-indexed: episode=0 → real EP1, episode=51 → real EP52.
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
HDR = {'User-Agent': 'Mozilla/5.0'}

r2 = boto3.client(
    's3', endpoint_url=R2_ENDPOINT,
    aws_access_key_id=R2_KEY_ID, aws_secret_access_key=R2_SECRET,
    config=Config(signature_version='s3v4'), region_name='auto'
)

# Patch both missing episodes:
# - EP1: use episode=0 (true first episode)
# - EP52: use episode=51 (true last episode, now backend is 200)
patches = [
    {'ep_no': 1,  'api_ep': 0,  'force': True},   # True EP1 is at api episode=0
    {'ep_no': 52, 'api_ep': 51, 'force': False},   # True EP52 is at api episode=51
]

for patch in patches:
    ep_no  = patch['ep_no']
    api_ep = patch['api_ep']
    force  = patch.get('force', False)

    print(f"\n{'='*55}")
    print(f"Patching EP{ep_no} (api episode={api_ep}, force={force})...")
    print(f"{'='*55}")

    # Check if already in DB (skip only if not force)
    er = requests.get(f"{API_BASE}/api/dramas/{DRAMA_ID_DB}/episodes", timeout=15)
    existing = {int(e.get('episodeNumber', 0)): e for e in (er.json() if er.ok else [])}
    if ep_no in existing and not force:
        print(f"EP{ep_no} already in DB, skipping.")
        continue

    # Fetch fresh URL
    r = requests.get(
        f'https://vidrama.asia/api/dramabox?action=stream&id={BOOK_ID}&episode={api_ep}&lang=in',
        headers=HDR, timeout=20
    )
    data = r.json().get('data', {})
    video_url = data.get('videoUrl') or data.get('rawVideoUrl', '')
    print(f"Video URL: {video_url[:100]}")

    if not video_url:
        print(f"ERROR: No URL for EP{ep_no}!")
        continue

    # Download & transcode
    src  = os.path.join(TEMP_DIR, f"src_ep{ep_no:03d}.mp4")
    p720 = os.path.join(TEMP_DIR, f"ep{ep_no:03d}_720p.mp4")
    p540 = os.path.join(TEMP_DIR, f"ep{ep_no:03d}_540p.mp4")

    print(f"Downloading...")
    res = subprocess.run(
        ['ffmpeg', '-y', '-i', video_url, '-c', 'copy', '-loglevel', 'warning', src],
        capture_output=True, text=True, errors='ignore', timeout=300
    )
    size = os.path.getsize(src)/1024/1024 if os.path.exists(src) else 0
    print(f"Download: code={res.returncode} ({size:.1f}MB)")

    if not os.path.exists(src) or size < 0.5:
        print("Download FAILED!")
        continue

    print("Encoding 720p...")
    subprocess.run(
        ['ffmpeg', '-y', '-i', src,
         '-vf', 'scale=720:-2', '-c:v', 'libx264', '-crf', '23', '-preset', 'fast',
         '-fps_mode', 'cfr', '-af', 'aresample=async=1',
         '-maxrate', '1500k', '-bufsize', '3000k',
         '-c:a', 'aac', '-b:a', '128k', '-movflags', '+faststart', '-loglevel', 'warning', p720],
        capture_output=True, timeout=180
    )

    print("Encoding 540p...")
    subprocess.run(
        ['ffmpeg', '-y', '-i', src,
         '-vf', 'scale=540:-2', '-c:v', 'libx264', '-crf', '26', '-preset', 'fast',
         '-fps_mode', 'cfr', '-af', 'aresample=async=1',
         '-maxrate', '1000k', '-bufsize', '2000k',
         '-c:a', 'aac', '-b:a', '96k', '-movflags', '+faststart', '-loglevel', 'warning', p540],
        capture_output=True, timeout=180
    )

    if os.path.exists(src): os.remove(src)

    key720 = f"dramas/{DRAMA_SLUG}/ep{ep_no:03d}_720p.mp4"
    key540 = f"dramas/{DRAMA_SLUG}/ep{ep_no:03d}_540p.mp4"

    url_720 = url_540 = None
    for local, key, label in [(p720, key720, '720p'), (p540, key540, '540p')]:
        if os.path.exists(local):
            mb = os.path.getsize(local)/1024/1024
            with open(local, 'rb') as f:
                r2.upload_fileobj(f, R2_BUCKET, key,
                    ExtraArgs={'ContentType': 'video/mp4', 'CacheControl': 'public, max-age=31536000'})
            print(f"Uploaded {label} ({mb:.1f}MB)")
            os.remove(local)
            if label == '720p': url_720 = f"{R2_PUBLIC}/{key}"
            else: url_540 = f"{R2_PUBLIC}/{key}"

    # Register or update in DB
    payload = {
        'episodeNumber': ep_no,
        'title': f'Episode {ep_no}',
        'videoUrl': url_720 or '',
        'videoUrl540p': url_540 or '',
        'isVip': False, 'coinPrice': 0, 'isActive': False,
    }
    if force and ep_no in existing:
        # Update existing episode
        ep_id = existing[ep_no].get('id')
        reg = requests.patch(
            f"{API_BASE}/api/admin/dramas/{DRAMA_ID_DB}/episodes/{ep_id}",
            headers=ADMIN_HDR, json=payload, timeout=20
        )
        if not reg.ok:
            reg = requests.put(
                f"{API_BASE}/api/admin/dramas/{DRAMA_ID_DB}/episodes/{ep_id}",
                headers=ADMIN_HDR, json=payload, timeout=20
            )
    else:
        reg = requests.post(
            f"{API_BASE}/api/admin/dramas/{DRAMA_ID_DB}/episodes",
            headers=ADMIN_HDR, json=payload, timeout=20
        )
    if reg.ok:
        print(f"✅ EP{ep_no} {'updated' if force else 'registered'}! ID: {reg.json().get('id', ep_no)}")
    else:
        print(f"❌ DB failed: {reg.status_code} {reg.text[:100]}")

print("\nPatch done!")
