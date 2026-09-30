# -*- coding: utf-8 -*-
"""
Ingest Drama: Sopir Taksi Ternyata Bos Dunia (StardustTV, ID: 22434)
- 44 episodes
- HLS M3U8 source (burned-in subtitle, no VTT needed)
- Upload to R2, register in KingShort DB
"""
import requests
import boto3
import json
import time
import os
import subprocess
import urllib3
import io
import tempfile
from botocore.config import Config

urllib3.disable_warnings()

# ─── CONFIG ────────────────────────────────────────────────────────────────
API_BASE  = 'https://api.shortlovers.id'
ADMIN_KEY = '00ca04e3e2702be565d7bf44e783255247708289bce9b2fb6187a2e117f87fd14'
ADMIN_HDR = {'x-admin-key': ADMIN_KEY, 'Content-Type': 'application/json'}

R2_ENDPOINT = 'https://a142d3b29a5d64943cb251157e25eaf3.r2.cloudflarestorage.com'
R2_KEY_ID   = '07c99c897986ea52703c1285308d5e2c'
R2_SECRET   = '44788d376ffb216e1e73784b6fe1ff1423607928898a87c50819b52cdfc12e44'
R2_BUCKET   = 'shortlovers'
R2_PUBLIC   = 'https://stream.shortlovers.id'

DRAMA_ID   = '22434'
DRAMA_SLUG = 'sopir-taksi-ternyata-bos-dunia'
GENRES     = ['Action', 'Romantis', 'Drama']

TEMP_DIR   = tempfile.mkdtemp(prefix='stardust_')

FFMPEG_HEADERS = (
    "User-Agent: Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
    "(KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36\r\n"
    "Referer: https://vidrama.asia/\r\n"
)

# ─── R2 CLIENT ─────────────────────────────────────────────────────────────
def get_r2():
    return boto3.client(
        's3', endpoint_url=R2_ENDPOINT,
        aws_access_key_id=R2_KEY_ID, aws_secret_access_key=R2_SECRET,
        config=Config(signature_version='s3v4'), region_name='auto'
    )

# ─── FETCH DRAMA DETAILS ────────────────────────────────────────────────────
def fetch_drama_details():
    url = f'https://vidrama.asia/api/stardusttv?action=detail&id={DRAMA_ID}&lang=id'
    headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'}
    for attempt in range(1, 4):
        try:
            r = requests.get(url, headers=headers, timeout=20)
            if r.ok:
                data = r.json()
                if data.get('success') and data.get('data'):
                    return data['data']
            print(f"  ⚠ HTTP {r.status_code} (attempt {attempt}/3)")
        except Exception as e:
            print(f"  ⚠ Error (attempt {attempt}/3): {e}")
        time.sleep(3)
    return None

# ─── COVER: CONVERT & UPLOAD ────────────────────────────────────────────────
def upload_cover(r2, cover_url):
    r2_key = f'dramas/{DRAMA_SLUG}/cover_hq.jpg'

    # Check if already uploaded
    try:
        r2.head_object(Bucket=R2_BUCKET, Key=r2_key)
        url = f'{R2_PUBLIC}/{r2_key}'
        print(f"  ✓ Cover already in R2: {url}")
        return url
    except Exception:
        pass

    print(f"  🖼 Downloading & converting cover...")
    raw_path = os.path.join(TEMP_DIR, 'cover_raw')
    clean_path = os.path.join(TEMP_DIR, 'cover_clean.jpg')

    try:
        r = requests.get(cover_url, timeout=30, verify=False)
        r.raise_for_status()
        with open(raw_path, 'wb') as f:
            f.write(r.content)

        # Convert to pure JPEG (handles HEIC/WebP/etc)
        result = subprocess.run(
            ['ffmpeg', '-y', '-i', raw_path, '-update', '1', '-q:v', '2', clean_path],
            capture_output=True, timeout=60
        )
        if result.returncode != 0 or not os.path.exists(clean_path):
            # Fallback: upload raw if ffmpeg fails
            print("  ⚠ ffmpeg convert failed, uploading raw...")
            clean_path = raw_path

        with open(clean_path, 'rb') as f:
            r2.upload_fileobj(
                f, R2_BUCKET, r2_key,
                ExtraArgs={'ContentType': 'image/jpeg', 'CacheControl': 'public, max-age=31536000'}
            )
        url = f'{R2_PUBLIC}/{r2_key}'
        print(f"  ✅ Cover uploaded: {url}")
        return url
    except Exception as e:
        print(f"  ✗ Cover upload failed: {e}")
        return cover_url

# ─── REGISTER DRAMA ─────────────────────────────────────────────────────────
def register_drama(metadata, cover_r2_url):
    # Check if already exists
    r = requests.get(f'{API_BASE}/api/dramas', params={'search': metadata['title']}, timeout=15)
    if r.ok:
        dramas = r.json().get('dramas', [])
        for d in dramas:
            if metadata['title'].lower() in d.get('title', '').lower():
                print(f"  ✓ Drama already in DB: {d['id']}")
                return d['id']

    payload = {
        'title': metadata['title'],
        'description': metadata.get('description') or metadata.get('introduction') or '',
        'cover': cover_r2_url,
        'genres': GENRES,
        'totalEpisodes': len(metadata.get('list', [])),
        'status': 'completed',
        'country': 'China',
        'language': 'Indonesia',
        'isActive': False,
        'isVip': False,
    }
    r = requests.post(f'{API_BASE}/api/admin/dramas', headers=ADMIN_HDR, json=payload, timeout=30)
    if r.ok:
        resp = r.json()
        drama_id = resp.get('id') or resp.get('drama', {}).get('id')
        print(f"  ✅ Drama registered! ID: {drama_id}")
        return drama_id
    else:
        print(f"  ✗ Drama registration failed: {r.status_code} {r.text[:300]}")
        return None

# ─── DOWNLOAD + TRANSCODE ───────────────────────────────────────────────────
def download_and_transcode(m3u8_url, ep_no):
    local_720 = os.path.join(TEMP_DIR, f'ep{ep_no:03d}_720p.mp4')
    local_540 = os.path.join(TEMP_DIR, f'ep{ep_no:03d}_540p.mp4')

    for f in [local_720, local_540]:
        if os.path.exists(f):
            os.remove(f)

    # 720p – stream copy with faststart
    success_720 = False
    for attempt in range(1, 4):
        cmd = [
            'ffmpeg', '-y',
            '-headers', FFMPEG_HEADERS,
            '-i', m3u8_url,
            '-c', 'copy',
            '-movflags', '+faststart',
            '-loglevel', 'warning',
            local_720
        ]
        res = subprocess.run(cmd, capture_output=True, text=True, errors='ignore', timeout=600)
        if res.returncode == 0 and os.path.exists(local_720) and os.path.getsize(local_720) > 50000:
            size_mb = os.path.getsize(local_720) / (1024 * 1024)
            print(f"    ✓ 720p ready ({size_mb:.1f} MB)")
            success_720 = True
            break
        else:
            print(f"    ⚠ 720p attempt {attempt}/3 failed: {res.stderr.strip()[-200:]}")
            time.sleep(5)

    if not success_720:
        return None, None

    # 540p transcode with faststart
    success_540 = False
    for attempt in range(1, 4):
        cmd = [
            'ffmpeg', '-y',
            '-i', local_720,
            '-vf', 'scale=-2:540',
            '-c:v', 'libx264', '-crf', '26', '-preset', 'fast',
            '-maxrate', '1000k', '-bufsize', '2000k',
            '-c:a', 'aac', '-b:a', '96k',
            '-movflags', '+faststart',
            '-loglevel', 'warning',
            local_540
        ]
        res = subprocess.run(cmd, capture_output=True, text=True, errors='ignore', timeout=300)
        if res.returncode == 0 and os.path.exists(local_540) and os.path.getsize(local_540) > 50000:
            size_mb = os.path.getsize(local_540) / (1024 * 1024)
            print(f"    ✓ 540p ready ({size_mb:.1f} MB)")
            success_540 = True
            break
        else:
            print(f"    ⚠ 540p attempt {attempt}/3 failed: {res.stderr.strip()[-200:]}")
            time.sleep(5)

    if not success_540:
        return local_720, None

    return local_720, local_540

# ─── UPLOAD TO R2 ───────────────────────────────────────────────────────────
def upload_to_r2(r2, local_path, r2_key):
    try:
        size_mb = os.path.getsize(local_path) / (1024 * 1024)
        with open(local_path, 'rb') as f:
            r2.upload_fileobj(
                f, R2_BUCKET, r2_key,
                ExtraArgs={'ContentType': 'video/mp4', 'CacheControl': 'public, max-age=31536000'}
            )
        print(f"    ✓ Uploaded {os.path.basename(r2_key)} ({size_mb:.1f} MB)")
        return f'{R2_PUBLIC}/{r2_key}'
    except Exception as e:
        print(f"    ✗ Upload failed: {e}")
        return None

# ─── REGISTER EPISODE ───────────────────────────────────────────────────────
def register_episode(drama_id, ep_no, url_720, url_540):
    payload = {
        'episodeNumber': ep_no,
        'title': f'Episode {ep_no}',
        'videoUrl': url_720 or url_540 or '',
        'videoUrl540p': url_540 or '',
        'isVip': False,
        'coinPrice': 0,
        'isActive': True,
    }
    r = requests.post(
        f'{API_BASE}/api/admin/dramas/{drama_id}/episodes',
        headers=ADMIN_HDR, json=payload, timeout=20
    )
    if r.ok:
        ep_id = r.json().get('id')
        return ep_id
    # Try PATCH if already exists
    r2 = requests.patch(
        f'{API_BASE}/api/admin/dramas/{drama_id}/episodes/{ep_no}',
        headers=ADMIN_HDR, json=payload, timeout=20
    )
    if r2.ok:
        return r2.json().get('id') or 'updated'
    return None

# ─── MAIN ───────────────────────────────────────────────────────────────────
def main():
    print("=" * 65)
    print("🎬 INGESTING: Sopir Taksi Ternyata Bos Dunia (StardustTV)")
    print(f"   Drama ID : {DRAMA_ID}")
    print(f"   Slug     : {DRAMA_SLUG}")
    print(f"   Temp Dir : {TEMP_DIR}")
    print("=" * 65)

    r2 = get_r2()

    # 1. Fetch metadata
    print("\n[1/5] Fetching drama metadata...")
    metadata = fetch_drama_details()
    if not metadata:
        print("❌ Failed to fetch metadata. Aborting.")
        return

    episodes = metadata.get('list', [])
    print(f"  Title  : {metadata['title']}")
    print(f"  Episodes: {len(episodes)}")

    # 2. Upload cover
    print("\n[2/5] Processing cover...")
    cover_url = metadata.get('cover') or metadata.get('image', '')
    cover_r2_url = upload_cover(r2, cover_url)

    # 3. Register drama
    print("\n[3/5] Registering drama in DB...")
    drama_id = register_drama(metadata, cover_r2_url)
    if not drama_id:
        print("❌ Drama registration failed. Aborting.")
        return

    # 4. Get already-done episodes
    done_eps = set()
    er = requests.get(f'{API_BASE}/api/dramas/{drama_id}/episodes', timeout=15)
    if er.ok:
        ep_data = er.json()
        eps_list = ep_data if isinstance(ep_data, list) else ep_data.get('episodes', [])
        for ep in eps_list:
            done_eps.add(int(ep.get('episodeNumber', 0)))
    print(f"\n[4/5] Already in DB: {len(done_eps)} episodes")

    # 5. Process each episode
    print(f"\n[5/5] Processing {len(episodes)} episodes...\n")
    success_count = 0
    fail_count = 0
    start_time = time.time()

    for ep in episodes:
        ep_no = int(ep.get('episodeNumber') or ep.get('episodeNo', 0))
        m3u8_url = ep.get('h264') or ep.get('videoUrl') or ep.get('videoPath', '')

        if not ep_no or not m3u8_url:
            print(f"  ⚠ Skipping EP {ep_no} - missing URL")
            continue

        print(f"\n  📺 Episode {ep_no}/{len(episodes)}")

        if ep_no in done_eps:
            print("    ✓ Already in DB, skipping.")
            success_count += 1
            continue

        r2_key_720 = f'dramas/{DRAMA_SLUG}/ep{ep_no:03d}_720p.mp4'
        r2_key_540 = f'dramas/{DRAMA_SLUG}/ep{ep_no:03d}_540p.mp4'

        url_720 = None
        url_540 = None

        # Check R2
        try:
            r2.head_object(Bucket=R2_BUCKET, Key=r2_key_720)
            url_720 = f'{R2_PUBLIC}/{r2_key_720}'
            print(f"    ✓ 720p already in R2")
        except Exception:
            pass

        try:
            r2.head_object(Bucket=R2_BUCKET, Key=r2_key_540)
            url_540 = f'{R2_PUBLIC}/{r2_key_540}'
            print(f"    ✓ 540p already in R2")
        except Exception:
            pass

        # Download, transcode & upload if needed
        if not url_720:
            print(f"    ⬇ Downloading & transcoding from HLS...")
            local_720, local_540 = download_and_transcode(m3u8_url, ep_no)
            if not local_720:
                print(f"    ❌ Download failed for EP {ep_no}")
                fail_count += 1
                continue

            url_720 = upload_to_r2(r2, local_720, r2_key_720)
            if local_540:
                url_540 = upload_to_r2(r2, local_540, r2_key_540)

            # Cleanup temp files
            for f in [local_720, local_540]:
                if f and os.path.exists(f):
                    try:
                        os.remove(f)
                    except Exception:
                        pass

            if not url_720:
                print(f"    ❌ R2 upload failed for EP {ep_no}")
                fail_count += 1
                continue

        # Register in DB
        ep_id = register_episode(drama_id, ep_no, url_720, url_540)
        if ep_id:
            elapsed = time.time() - start_time
            remaining = (elapsed / max(success_count + 1, 1)) * (len(episodes) - success_count - 1)
            print(f"    ✅ Registered! ID: {ep_id} | ETA: {remaining/60:.1f} min")
            success_count += 1
            done_eps.add(ep_no)
        else:
            print(f"    ❌ DB registration failed for EP {ep_no}")
            fail_count += 1

        time.sleep(0.5)

    # 6. Activate drama
    print(f"\n[6/6] Activating drama...")
    r = requests.patch(
        f'{API_BASE}/api/admin/dramas/{drama_id}',
        headers=ADMIN_HDR,
        json={'isActive': True},
        timeout=20
    )
    if r.ok:
        print(f"  ✅ Drama activated!")
    else:
        print(f"  ⚠ Activation response: {r.status_code} {r.text[:200]}")

    # Summary
    elapsed = time.time() - start_time
    print("\n" + "=" * 65)
    print("🏁 INGESTION COMPLETE!")
    print(f"   Drama ID  : {drama_id}")
    print(f"   Success   : {success_count}/{len(episodes)} episodes")
    print(f"   Failed    : {fail_count}/{len(episodes)} episodes")
    print(f"   Duration  : {elapsed/60:.1f} minutes")
    print("=" * 65)

if __name__ == '__main__':
    main()
