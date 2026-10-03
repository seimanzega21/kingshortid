# -*- coding: utf-8 -*-
"""
Ingest Drama: Rahasia Bos Mafia (StardustTV, ID: 20302)
- 70 episodes
- Vidrama: https://vidrama.asia/movie/rahasia-bos-mafia--20302?provider=stardusttv&lang=id
- HLS M3U8 source -> 720p stream copy + 540p transcode
- Upload to Cloudflare R2: dramas/rahasia-bos-mafia/
- Register in KingShort DB via admin API
- Activate drama on completion
"""
import requests
import boto3
import json
import time
import os
import sys
import subprocess
import urllib3
import tempfile
from concurrent.futures import ThreadPoolExecutor, as_completed
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

DRAMA_ID    = '20302'
DRAMA_SLUG  = 'rahasia-bos-mafia'
GENRES      = ['Drama', 'Romantis', 'Aksi', 'Eksklusif']

TEMP_DIR    = 'D:/kingshortid/temp_stardust'
os.makedirs(TEMP_DIR, exist_ok=True)

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

# ─── FETCH METADATA ────────────────────────────────────────────────────────
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
            print(f"  [WARN] HTTP {r.status_code} (attempt {attempt}/3)")
        except Exception as e:
            print(f"  [WARN] Error (attempt {attempt}/3): {e}")
        time.sleep(3)
    return None

def fetch_episode_url_fallback(ep_no):
    url = f'https://vidrama.asia/api/stardusttv?action=episode&id={DRAMA_ID}&episode={ep_no}&lang=id'
    headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'}
    try:
        r = requests.get(url, headers=headers, timeout=20)
        if r.ok:
            data = r.json()
            if data.get('success') and data.get('data'):
                ep_data = data['data']
                return ep_data.get('videoUrl') or ep_data.get('url') or ep_data.get('fallbackUrl')
    except Exception as e:
        print(f"    [WARN] Fallback EP {ep_no} error: {e}")
    return None

# ─── COVER PROCESSING ──────────────────────────────────────────────────────
def upload_cover(r2, cover_url):
    r2_key = f'dramas/{DRAMA_SLUG}/cover_hq.jpg'

    try:
        r2.head_object(Bucket=R2_BUCKET, Key=r2_key)
        url = f'{R2_PUBLIC}/{r2_key}'
        print(f"  [OK] Cover already in R2: {url}")
        return url
    except Exception:
        pass

    print(f"  Downloading & converting cover...")
    raw_path = os.path.join(TEMP_DIR, f'{DRAMA_SLUG}_cover_raw')
    clean_path = os.path.join(TEMP_DIR, f'{DRAMA_SLUG}_cover_clean.jpg')

    try:
        r = requests.get(cover_url, timeout=30, verify=False)
        r.raise_for_status()
        with open(raw_path, 'wb') as f:
            f.write(r.content)

        result = subprocess.run(
            ['ffmpeg', '-y', '-i', raw_path, '-update', '1', '-q:v', '2', clean_path],
            capture_output=True, timeout=60
        )
        upload_path = clean_path if (result.returncode == 0 and os.path.exists(clean_path)) else raw_path

        with open(upload_path, 'rb') as f:
            r2.upload_fileobj(
                f, R2_BUCKET, r2_key,
                ExtraArgs={'ContentType': 'image/jpeg', 'CacheControl': 'public, max-age=31536000'}
            )
        url = f'{R2_PUBLIC}/{r2_key}'
        print(f"  [OK] Cover uploaded: {url}")

        for p in [raw_path, clean_path]:
            if os.path.exists(p):
                try: os.remove(p)
                except: pass

        return url
    except Exception as e:
        print(f"  [ERROR] Cover upload failed: {e}")
        return cover_url

# ─── REGISTER DRAMA ─────────────────────────────────────────────────────────
def register_drama(metadata, cover_r2_url):
    title = metadata.get('title', 'Rahasia Bos Mafia')

    # Check if already in DB
    r = requests.get(f'{API_BASE}/api/dramas/search', params={'q': title}, timeout=15)
    if r.ok:
        dramas_list = r.json().get('dramas', [])
        for d in dramas_list:
            if title.lower() in d.get('title', '').lower():
                print(f"  [OK] Drama already in DB: {d['id']} ({d['title']})")
                return d['id']

    payload = {
        'title': title,
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
        print(f"  [OK] Drama registered! ID: {drama_id}")
        return drama_id
    else:
        print(f"  [ERROR] Drama registration failed: {r.status_code} {r.text[:300]}")
        return None

# ─── DOWNLOAD + TRANSCODE ───────────────────────────────────────────────────
def download_and_transcode(m3u8_url, ep_no):
    local_720 = os.path.join(TEMP_DIR, f'{DRAMA_SLUG}_ep{ep_no:03d}_720p.mp4')
    local_540 = os.path.join(TEMP_DIR, f'{DRAMA_SLUG}_ep{ep_no:03d}_540p.mp4')

    for f in [local_720, local_540]:
        if os.path.exists(f):
            try: os.remove(f)
            except: pass

    # 1. 720p: stream copy
    success_720 = False
    urls_to_try = [m3u8_url]
    for attempt in range(1, 4):
        cur_url = urls_to_try[0]
        cmd = [
            'ffmpeg', '-y',
            '-headers', FFMPEG_HEADERS,
            '-i', cur_url,
            '-c', 'copy',
            '-movflags', '+faststart',
            '-loglevel', 'warning',
            local_720
        ]
        res = subprocess.run(cmd, capture_output=True, text=True, errors='ignore', timeout=600)
        if res.returncode == 0 and os.path.exists(local_720) and os.path.getsize(local_720) > 50000:
            sz_mb = os.path.getsize(local_720) / (1024 * 1024)
            success_720 = True
            break
        else:
            print(f"    [WARN] EP {ep_no} 720p attempt {attempt}/3 failed")
            if attempt == 1:
                fallback = fetch_episode_url_fallback(ep_no)
                if fallback and fallback != cur_url:
                    urls_to_try = [fallback]
            time.sleep(4)

    if not success_720:
        return None, None

    # 2. 540p: transcode
    success_540 = False
    for attempt in range(1, 4):
        cmd = [
            'ffmpeg', '-y',
            '-i', local_720,
            '-vf', 'scale=-2:540',
            '-c:v', 'libx264', '-crf', '26', '-preset', 'veryfast',
            '-maxrate', '1000k', '-bufsize', '2000k',
            '-c:a', 'aac', '-b:a', '96k',
            '-movflags', '+faststart',
            '-loglevel', 'warning',
            local_540
        ]
        res = subprocess.run(cmd, capture_output=True, text=True, errors='ignore', timeout=300)
        if res.returncode == 0 and os.path.exists(local_540) and os.path.getsize(local_540) > 50000:
            success_540 = True
            break
        else:
            print(f"    [WARN] EP {ep_no} 540p attempt {attempt}/3 failed")
            time.sleep(3)

    return local_720, (local_540 if success_540 else None)

# ─── UPLOAD TO R2 ───────────────────────────────────────────────────────────
def upload_to_r2(r2, local_path, r2_key):
    for attempt in range(1, 4):
        try:
            size_mb = os.path.getsize(local_path) / (1024 * 1024)
            with open(local_path, 'rb') as f:
                r2.upload_fileobj(
                    f, R2_BUCKET, r2_key,
                    ExtraArgs={'ContentType': 'video/mp4', 'CacheControl': 'public, max-age=31536000'}
                )
            return f'{R2_PUBLIC}/{r2_key}'
        except Exception as e:
            print(f"    [WARN] Upload {r2_key} attempt {attempt}/3 failed: {e}")
            time.sleep(3)
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
    for attempt in range(1, 4):
        try:
            r = requests.post(
                f'{API_BASE}/api/admin/dramas/{drama_id}/episodes',
                headers=ADMIN_HDR, json=payload, timeout=25
            )
            if r.ok:
                return r.json().get('id') or 'created'

            # Try patch if already exists
            r2 = requests.patch(
                f'{API_BASE}/api/admin/dramas/{drama_id}/episodes/{ep_no}',
                headers=ADMIN_HDR, json=payload, timeout=25
            )
            if r2.ok:
                return r2.json().get('id') or 'updated'
        except Exception as e:
            time.sleep(2)
    return None

# ─── SINGLE EPISODE PIPELINE ───────────────────────────────────────────────
def process_single_episode(ep, drama_id, r2, total_eps):
    ep_no = int(ep.get('episodeNumber') or ep.get('episodeNo', 0))
    m3u8_url = ep.get('h264') or ep.get('videoUrl') or ep.get('videoPath', '')

    if not ep_no or not m3u8_url:
        return ep_no, False, 'missing url'

    r2_key_720 = f'dramas/{DRAMA_SLUG}/ep{ep_no:03d}_720p.mp4'
    r2_key_540 = f'dramas/{DRAMA_SLUG}/ep{ep_no:03d}_540p.mp4'

    url_720 = None
    url_540 = None

    # Check R2
    try:
        r2.head_object(Bucket=R2_BUCKET, Key=r2_key_720)
        url_720 = f'{R2_PUBLIC}/{r2_key_720}'
    except Exception:
        pass

    try:
        r2.head_object(Bucket=R2_BUCKET, Key=r2_key_540)
        url_540 = f'{R2_PUBLIC}/{r2_key_540}'
    except Exception:
        pass

    # Download + transcode if not in R2
    if not url_720:
        local_720, local_540 = download_and_transcode(m3u8_url, ep_no)
        if not local_720:
            return ep_no, False, 'download/transcode failed'

        url_720 = upload_to_r2(r2, local_720, r2_key_720)
        if local_540:
            url_540 = upload_to_r2(r2, local_540, r2_key_540)

        # Cleanup
        for f in [local_720, local_540]:
            if f and os.path.exists(f):
                try: os.remove(f)
                except: pass

        if not url_720:
            return ep_no, False, 'R2 upload failed'

    # Register in DB
    ep_id = register_episode(drama_id, ep_no, url_720, url_540)
    if not ep_id:
        return ep_no, False, 'DB registration failed'

    return ep_no, True, ep_id

# ─── MAIN ───────────────────────────────────────────────────────────────────
def main():
    print("=" * 65)
    print("🎬 INGESTING: Rahasia Bos Mafia (StardustTV)")
    print(f"   Drama ID : {DRAMA_ID}")
    print(f"   Slug     : {DRAMA_SLUG}")
    print(f"   Temp Dir : {TEMP_DIR}")
    print("=" * 65)

    r2 = get_r2()

    # 1. Fetch metadata
    print("\n[1/5] Fetching drama metadata...")
    metadata = fetch_drama_details()
    if not metadata:
        print("[ERROR] Failed to fetch metadata. Aborting.")
        return

    episodes = metadata.get('list', [])
    total_eps = len(episodes)
    print(f"  Title   : {metadata.get('title')}")
    print(f"  Episodes: {total_eps}")

    # 2. Upload cover
    print("\n[2/5] Processing cover...")
    cover_url = metadata.get('cover') or metadata.get('poster') or metadata.get('image', '')
    cover_r2_url = upload_cover(r2, cover_url)

    # 3. Register drama
    print("\n[3/5] Registering drama in DB...")
    drama_id = register_drama(metadata, cover_r2_url)
    if not drama_id:
        print("[ERROR] Drama registration failed. Aborting.")
        return

    # 4. Check already done episodes
    done_eps = set()
    er = requests.get(f'{API_BASE}/api/dramas/{drama_id}/episodes', timeout=15)
    if er.ok:
        ep_data = er.json()
        eps_list = ep_data if isinstance(ep_data, list) else ep_data.get('episodes', [])
        for ep in eps_list:
            done_eps.add(int(ep.get('episodeNumber', 0)))
    print(f"\n[4/5] Already in DB: {len(done_eps)} / {total_eps} episodes")

    # Filter episodes to process
    remaining = [ep for ep in episodes if int(ep.get('episodeNumber') or ep.get('episodeNo', 0)) not in done_eps]
    print(f"  Remaining to process: {len(remaining)} episodes")

    # 5. Process episodes with ThreadPoolExecutor (2 parallel workers)
    print(f"\n[5/5] Processing remaining episodes with 2 workers...\n")
    start_time = time.time()
    success_count = len(done_eps)
    fail_count = 0

    with ThreadPoolExecutor(max_workers=2) as executor:
        future_map = {
            executor.submit(process_single_episode, ep, drama_id, r2, total_eps): ep
            for ep in remaining
        }

        for future in as_completed(future_map):
            ep_no, ok, msg = future.result()
            if ok:
                success_count += 1
                elapsed = time.time() - start_time
                done_now = success_count - len(done_eps)
                rem_now = len(remaining) - done_now
                eta_min = ((elapsed / max(done_now, 1)) * rem_now) / 60
                print(f"  [EP {ep_no:02d}/{total_eps}] DONE (DB ID: {msg}) | Total Done: {success_count}/{total_eps} | ETA: {eta_min:.1f} min")
            else:
                fail_count += 1
                print(f"  [EP {ep_no:02d}/{total_eps}] FAILED: {msg} | Total Done: {success_count}/{total_eps}")

    # 6. Activate drama
    print(f"\n[6/6] Activating drama in DB...")
    r = requests.patch(
        f'{API_BASE}/api/admin/dramas/{drama_id}',
        headers=ADMIN_HDR,
        json={'isActive': True, 'totalEpisodes': success_count},
        timeout=20
    )
    if r.ok:
        print(f"  [OK] Drama activated successfully!")
    else:
        print(f"  [WARN] Activation response: {r.status_code} {r.text[:200]}")

    elapsed = time.time() - start_time
    print("\n" + "=" * 65)
    print("INGESTION FINISHED!")
    print(f"   Drama ID  : {drama_id}")
    print(f"   Success   : {success_count}/{total_eps} episodes")
    print(f"   Failed    : {fail_count}/{total_eps} episodes")
    print(f"   Duration  : {elapsed/60:.1f} minutes")
    print("=" * 65)

if __name__ == '__main__':
    main()
