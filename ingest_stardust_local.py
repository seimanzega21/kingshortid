# -*- coding: utf-8 -*-
"""
LOCAL PIPELINE: Ingest 13 StardustTV dramas sequentially.
Uses /api/stardusttv?action=detail&id= and ?action=episode&id=&episode=
"""
import requests
import boto3
import sys
import json
import time
import os
import subprocess
import urllib3
import io
import tempfile
from botocore.config import Config

urllib3.disable_warnings()

# ─── CONFIG ─────────────────────────────────────────────────────────────────
API_BASE  = 'http://141.11.160.187:3000'
ADMIN_KEY = '00ca04e3e2702be565d7bf44e783255247708289bce9b2fb6187a2e117f87fd14'
ADMIN_HDR = {'x-admin-key': ADMIN_KEY, 'Content-Type': 'application/json'}

R2_ENDPOINT = 'https://a142d3b29a5d64943cb251157e25eaf3.r2.cloudflarestorage.com'
R2_KEY_ID   = '07c99c897986ea52703c1285308d5e2c'
R2_SECRET   = '44788d376ffb216e1e73784b6fe1ff1423607928898a87c50819b52cdfc12e44'
R2_BUCKET   = 'shortlovers'
R2_PUBLIC   = 'https://stream.shortlovers.id'

TEMP_DIR = 'd:/kingshortid/temp_stardust'
os.makedirs(TEMP_DIR, exist_ok=True)

BASE_HDRS = {
    'User-Agent': 'Mozilla/5.0 (Linux; Android 15; Pixel 9) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/151.0.0.0 Mobile Safari/537.36',
    'Accept': '*/*',
    'Referer': 'https://vidrama.asia/',
}

# ─── DRAMA QUEUE ─────────────────────────────────────────────────────────────
# Only DUBBING-ID dramas (Indonesian audio) — skip NO-DUB
DRAMAS_TO_PROCESS = [
    {'id': '20188', 'slug': 'enam-pewaris-untuk-presdir-bo', 'genres': ['Drama', 'Family']},
    {'id': '21861', 'slug': 'gladiator-api-darah-dan-dendam', 'genres': ['Action', 'Drama']},
    {'id': '21734', 'slug': 'dari-rival-jadi-kekasih',       'genres': ['Romantis', 'Drama']},
    {'id': '20849', 'slug': 'mantan-istriku-ternyata-ceo',   'genres': ['Romantis', 'Drama']},
    {'id': '20119', 'slug': 'aku-cerai-bos-mafia-gila',      'genres': ['Romantis', 'Drama', 'Action']},
]

# ─── HELPERS ─────────────────────────────────────────────────────────────────
def get_r2():
    return boto3.client(
        's3', endpoint_url=R2_ENDPOINT,
        aws_access_key_id=R2_KEY_ID, aws_secret_access_key=R2_SECRET,
        config=Config(signature_version='s3v4'), region_name='auto'
    )

def fetch_drama_details(mid):
    """Fetch metadata using /api/stardusttv?action=detail&id="""
    url = f"https://vidrama.asia/api/stardusttv?action=detail&id={mid}&lang=id"
    print(f"   Fetching detail for ID {mid}...")
    for attempt in range(1, 4):
        try:
            r = requests.get(url, headers=BASE_HDRS, timeout=20, verify=False)
            if r.ok:
                data = r.json()
                if data.get('success') and data.get('data'):
                    return data['data']
            print(f"      WARN HTTP {r.status_code} (attempt {attempt}/3): {r.text[:100]}")
        except Exception as e:
            print(f"      WARN error (attempt {attempt}/3): {e}")
        time.sleep(3)
    return None

def fetch_episode_url(mid, ep_no):
    """Fetch m3u8 URL for a specific episode using ?action=episode"""
    url = f"https://vidrama.asia/api/stardusttv?action=episode&id={mid}&episode={ep_no}&lang=id"
    for attempt in range(1, 4):
        try:
            r = requests.get(url, headers=BASE_HDRS, timeout=20, verify=False)
            if r.ok:
                data = r.json()
                if data.get('success') and data.get('data'):
                    ep_data = data['data']
                    # Prefer h264 videoUrl over fallback (h265)
                    return ep_data.get('videoUrl') or ep_data.get('url') or ep_data.get('fallbackUrl')
            print(f"      WARN episode {ep_no} HTTP {r.status_code} (attempt {attempt}/3)")
        except Exception as e:
            print(f"      WARN episode {ep_no} error (attempt {attempt}/3): {e}")
        time.sleep(2)
    return None

def download_and_transcode(m3u8_url, slug, ep_no):
    local_720 = os.path.join(TEMP_DIR, f"{slug}_ep{ep_no:03d}_720p.mp4")
    local_540 = os.path.join(TEMP_DIR, f"{slug}_ep{ep_no:03d}_540p.mp4")

    for f in [local_720, local_540]:
        if os.path.exists(f): os.remove(f)

    headers_str = (
        "User-Agent: Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
        "(KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36\r\n"
        "Referer: https://vidrama.asia/\r\n"
    )

    # 720p — stream copy first
    success_720 = False
    for attempt in range(1, 4):
        cmd = [
            'ffmpeg', '-y',
            '-headers', headers_str,
            '-i', m3u8_url,
            '-c', 'copy',
            '-movflags', '+faststart',
            '-loglevel', 'warning',
            local_720
        ]
        res = subprocess.run(cmd, capture_output=True, text=True, errors='ignore', timeout=300)
        if res.returncode == 0 and os.path.exists(local_720) and os.path.getsize(local_720) > 50000:
            size_mb = os.path.getsize(local_720) / (1024*1024)
            print(f"      Downloaded 720p ({size_mb:.1f} MB)")
            success_720 = True
            break
        else:
            print(f"      WARN 720p attempt {attempt} failed: {res.stderr.strip()[-150:]}")
            if attempt < 3: time.sleep(5)

    if not success_720:
        return None, None

    # 540p transcode
    success_540 = False
    for attempt in range(1, 4):
        cmd = [
            'ffmpeg', '-y',
            '-i', local_720,
            '-vf', 'scale=-2:540',
            '-c:v', 'libx264', '-crf', '26', '-preset', 'fast',
            '-maxrate', '1200k', '-bufsize', '2400k',
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
            print(f"      WARN 540p attempt {attempt} failed: {res.stderr.strip()[-150:]}")
            if attempt < 3: time.sleep(5)

    return local_720, (local_540 if success_540 else None)

def upload_to_r2(r2, local_path, r2_key):
    try:
        size_mb = os.path.getsize(local_path) / (1024*1024)
        with open(local_path, 'rb') as f:
            r2.upload_fileobj(
                f, R2_BUCKET, r2_key,
                ExtraArgs={'ContentType': 'video/mp4', 'CacheControl': 'public, max-age=31536000'}
            )
        print(f"      Uploaded {os.path.basename(r2_key)} ({size_mb:.1f} MB)")
        return f"{R2_PUBLIC}/{r2_key}"
    except Exception as e:
        print(f"      Upload FAILED: {e}")
        return None

def upload_cover(r2, slug, cover_url):
    key = f"dramas/netshort/{slug}/cover_hq.jpg"
    try:
        r2.head_object(Bucket=R2_BUCKET, Key=key)
        print(f"   Cover already in R2")
        return f"{R2_PUBLIC}/{key}"
    except Exception:
        pass

    try:
        r = requests.get(cover_url, timeout=30, verify=False)
        if r.ok:
            with tempfile.NamedTemporaryFile(suffix='.tmp', delete=False) as tmp:
                tmp.write(r.content)
                tmp_path = tmp.name
            jpg_path = tmp_path + '.jpg'
            subprocess.run(
                ['ffmpeg', '-y', '-update', '1', '-i', tmp_path, jpg_path],
                capture_output=True, timeout=30
            )
            os.unlink(tmp_path)
            if os.path.exists(jpg_path):
                with open(jpg_path, 'rb') as f:
                    r2.upload_fileobj(
                        f, R2_BUCKET, key,
                        ExtraArgs={'ContentType': 'image/jpeg', 'CacheControl': 'public, max-age=31536000'}
                    )
                os.unlink(jpg_path)
                return f"{R2_PUBLIC}/{key}"
    except Exception as e:
        print(f"      WARN Cover upload failed: {e}")
    return cover_url

def get_or_register_drama(meta, total_eps, slug, genres):
    title = meta.get('title', slug)

    r = requests.get(f"{API_BASE}/api/dramas", params={"search": title}, timeout=15)
    if r.ok:
        data = r.json()
        dramas = data if isinstance(data, list) else data.get('dramas', [])
        for d in dramas:
            if title.lower() in d.get('title', '').lower():
                print(f"   Drama already in DB: {d['id']}")
                return d['id']

    print(f"   Uploading cover...")
    r2 = get_r2()
    cover_url = meta.get('cover') or meta.get('poster') or meta.get('image') or ''
    cover_r2 = upload_cover(r2, slug, cover_url)

    payload = {
        'title': title,
        'description': meta.get('description') or meta.get('introduction') or meta.get('intro') or '',
        'cover': cover_r2,
        'genres': genres,
        'totalEpisodes': total_eps,
        'status': 'ongoing',
        'country': 'China',
        'language': 'Indonesia',
        'isActive': True,
        'isVip': False,
    }
    r = requests.post(f"{API_BASE}/api/admin/dramas", headers=ADMIN_HDR, json=payload, timeout=30)
    if r.ok:
        resp = r.json()
        drama_id = resp.get('id') or resp.get('drama', {}).get('id')
        print(f"   Registered! DB ID: {drama_id}")
        return drama_id
    else:
        print(f"   Registration FAILED: {r.status_code} {r.text[:200]}")
        return None

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
        f"{API_BASE}/api/admin/dramas/{drama_id}/episodes",
        headers=ADMIN_HDR, json=payload, timeout=20
    )
    if r.ok:
        return r.json().get('id')
    r2 = requests.put(
        f"{API_BASE}/api/admin/dramas/{drama_id}/episodes/{ep_no}",
        headers=ADMIN_HDR, json=payload, timeout=20
    )
    if r2.ok:
        return r2.json().get('id') or 'updated'
    return None

# ─── MAIN PROCESS ────────────────────────────────────────────────────────────
def process_drama(d_info, r2):
    mid    = d_info['id']
    slug   = d_info['slug']
    genres = d_info['genres']

    print("\n" + "=" * 65)
    print(f"PROCESSING: {slug} (ID: {mid})")
    print("=" * 65)

    meta = fetch_drama_details(mid)
    if not meta:
        print(f"FAILED to fetch detail for {slug}! Skipping.")
        return False

    total_eps = int(meta.get('chapterCount') or meta.get('totalEpisodes') or 0)
    print(f"   Title: {meta.get('title')}")
    print(f"   Total Episodes: {total_eps}")

    if total_eps == 0:
        print(f"   WARN: could not determine total episodes, trying 60")
        total_eps = 60

    drama_id = get_or_register_drama(meta, total_eps, slug, genres)
    if not drama_id:
        print(f"FAILED to register {slug}! Skipping.")
        return False

    # Get existing episodes
    done_eps = set()
    er = requests.get(f"{API_BASE}/api/dramas/{drama_id}/episodes", timeout=15)
    if er.ok:
        for ep in er.json():
            done_eps.add(int(ep.get('episodeNumber', 0)))
    print(f"   Already done: {len(done_eps)} episodes")

    success_count = 0
    fail_count = 0

    for ep_no in range(1, total_eps + 1):
        print(f"\n   Episode {ep_no}/{total_eps}:")

        if ep_no in done_eps:
            print("      Already done, skipping.")
            success_count += 1
            continue

        r2_key_720 = f"dramas/netshort/{slug}/ep{ep_no:03d}_720p.mp4"
        r2_key_540 = f"dramas/netshort/{slug}/ep{ep_no:03d}_540p.mp4"

        url_720 = None
        url_540 = None

        # Check R2 first
        try:
            r2.head_object(Bucket=R2_BUCKET, Key=r2_key_720)
            url_720 = f"{R2_PUBLIC}/{r2_key_720}"
            print("      Already in R2")
        except Exception:
            pass

        try:
            r2.head_object(Bucket=R2_BUCKET, Key=r2_key_540)
            url_540 = f"{R2_PUBLIC}/{r2_key_540}"
        except Exception:
            pass

        if not url_720:
            # Fetch m3u8 URL for this episode
            m3u8_url = fetch_episode_url(mid, ep_no)
            if not m3u8_url:
                print(f"      FAILED: Could not get stream URL for EP {ep_no}")
                fail_count += 1
                continue

            local_720, local_540 = download_and_transcode(m3u8_url, slug, ep_no)
            if not local_720:
                print(f"      FAILED: Download/transcode failed for EP {ep_no}")
                fail_count += 1
                continue

            url_720 = upload_to_r2(r2, local_720, r2_key_720)
            if local_540:
                url_540 = upload_to_r2(r2, local_540, r2_key_540)

            for f in [local_720, local_540]:
                if f and os.path.exists(f): os.remove(f)

            if not url_720:
                print(f"      FAILED: R2 upload failed for EP {ep_no}")
                fail_count += 1
                continue

        ep_id = register_episode(drama_id, ep_no, url_720, url_540)
        if ep_id:
            print(f"      Done! DB ID: {ep_id}")
            success_count += 1
            done_eps.add(ep_no)
        else:
            print(f"      FAILED: DB registration failed for EP {ep_no}")
            fail_count += 1

        time.sleep(0.3)

    print(f"\n   {slug} DONE! Success: {success_count}/{total_eps}  Failed: {fail_count}/{total_eps}")
    return True


def main():
    print("=" * 65)
    print("STARTING STARDUSTTV INGESTION — 13 DRAMAS")
    print("=" * 65)

    r2 = get_r2()
    total_start = time.time()

    for d in DRAMAS_TO_PROCESS:
        try:
            process_drama(d, r2)
        except Exception as e:
            print(f"\nUncaught error processing {d['slug']}: {e}")
            import traceback; traceback.print_exc()

    elapsed = time.time() - total_start
    print("\n" + "=" * 65)
    print(f"ALL 13 DRAMAS PROCESSED!")
    print(f"Total Time: {elapsed/60:.1f} minutes")
    print("=" * 65)

if __name__ == '__main__':
    main()
