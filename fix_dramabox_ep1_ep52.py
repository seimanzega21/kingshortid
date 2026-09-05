"""
FIX:
1. Re-download EP1 using episode=1 (what Vidrama shows as EP1) - overwrite R2
2. Delete fake EP52 from DB (it's duplicate of EP51)
3. Remove fake EP52 from R2
"""
import requests, boto3, subprocess, os
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

# ── STEP 1: Delete fake EP52 from DB ────────────────────────────────────────
print("STEP 1: Remove fake EP52 from DB...")
er = requests.get(f"{API_BASE}/api/dramas/{DRAMA_ID_DB}/episodes", timeout=15)
eps = er.json() if er.ok else []
ep52 = next((e for e in eps if int(e.get('episodeNumber', 0)) == 52), None)
if ep52:
    ep52_id = ep52['id']
    rd = requests.delete(
        f"{API_BASE}/api/dramas/{DRAMA_ID_DB}/episodes/{ep52_id}",
        headers=ADMIN_HDR, timeout=15
    )
    if rd.ok:
        print(f"  ✅ EP52 deleted from DB (ID: {ep52_id})")
    else:
        # Try admin endpoint
        rd2 = requests.delete(
            f"{API_BASE}/api/admin/dramas/{DRAMA_ID_DB}/episodes/{ep52_id}",
            headers=ADMIN_HDR, timeout=15
        )
        print(f"  {'✅ Deleted' if rd2.ok else '❌ Failed'}: {rd2.status_code} {rd2.text[:80]}")
else:
    print("  EP52 not found in DB.")

# Delete EP52 from R2
for res in ['720p', '540p']:
    key = f"dramas/{DRAMA_SLUG}/ep052_{res}.mp4"
    try:
        r2.delete_object(Bucket=R2_BUCKET, Key=key)
        print(f"  ✅ Deleted R2: {key}")
    except Exception as e:
        print(f"  R2 delete {key}: {e}")

# ── STEP 2: Re-download EP1 from episode=1 (correct Vidrama EP1) ─────────────
print("\nSTEP 2: Re-download EP1 using api episode=1 (Vidrama's EP1)...")
r = requests.get(
    f'https://vidrama.asia/api/dramabox?action=stream&id={BOOK_ID}&episode=1&lang=in',
    headers=HDR, timeout=20
)
data = r.json().get('data', {})
video_url = data.get('videoUrl') or data.get('rawVideoUrl', '')
print(f"  Video URL: {video_url[:100]}")

if not video_url:
    print("  ERROR: No URL!")
    exit(1)

# Verify accessible
rt = requests.head(video_url, headers=HDR, timeout=10, allow_redirects=True)
print(f"  Backend HTTP: {rt.status_code}")

src  = os.path.join(TEMP_DIR, "src_ep001_fix.mp4")
p720 = os.path.join(TEMP_DIR, "ep001_720p_fix.mp4")
p540 = os.path.join(TEMP_DIR, "ep001_540p_fix.mp4")

print("  Downloading source...")
res = subprocess.run(
    ['ffmpeg', '-y', '-i', video_url, '-c', 'copy', '-loglevel', 'warning', src],
    capture_output=True, text=True, errors='ignore', timeout=300
)
size = os.path.getsize(src)/1024/1024 if os.path.exists(src) else 0
print(f"  Download: code={res.returncode} ({size:.1f}MB)")

if not os.path.exists(src) or size < 0.5:
    print("  FAILED!")
    exit(1)

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

# Upload to R2 (overwrite old wrong EP1)
key720 = f"dramas/{DRAMA_SLUG}/ep001_720p.mp4"
key540 = f"dramas/{DRAMA_SLUG}/ep001_540p.mp4"

for local, key, label in [(p720, key720, '720p'), (p540, key540, '540p')]:
    if os.path.exists(local):
        mb = os.path.getsize(local)/1024/1024
        with open(local, 'rb') as f:
            r2.upload_fileobj(f, R2_BUCKET, key,
                ExtraArgs={'ContentType': 'video/mp4', 'CacheControl': 'public, max-age=31536000'})
        print(f"  ✅ Uploaded {label} ({mb:.1f}MB) → {key}")
        os.remove(local)

# ── STEP 3: Verify final state ───────────────────────────────────────────────
print("\nSTEP 3: Verify final DB state...")
er2 = requests.get(f"{API_BASE}/api/dramas/{DRAMA_ID_DB}/episodes", timeout=15)
eps2 = sorted(er2.json(), key=lambda x: int(x.get('episodeNumber', 0)))
nums = [int(e.get('episodeNumber', 0)) for e in eps2]
print(f"  Total episodes in DB: {len(eps2)}")
print(f"  Episode numbers: {nums[:5]}...{nums[-5:]}")
print(f"  Max episode: {max(nums) if nums else 0}")

print("\nFIX COMPLETE!")
