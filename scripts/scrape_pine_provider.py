#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
KingShort Scraper untuk Provider Pine (via vidrama.asia)
=========================================================
RUN INSTRUCTIONS:
  python scripts/scrape_pine_provider.py

Cara Kerja:
1. Ambil daftar semua drama dari API Pine (?action=list)
2. Cek duplikat terhadap database
3. Ambil detail drama (?action=detail&collection_id=ID)
4. Ambil daftar episode (?action=episodes&collection_id=ID)
5. Per episode: ambil video URL (?action=play&collection_id=ID&episode=N)
6. Download, encode (720p + 540p), upload ke R2, simpan ke DB (status Pending)
"""
import requests
import boto3
import subprocess
import time
import tempfile
import urllib3
import re
import sys
import json
from pathlib import Path
from botocore.config import Config

urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)
sys.stdout.reconfigure(encoding='utf-8')

# ── CONFIG ───────────────────────────────────────────────────────────────────
API_BASE    = 'https://api.shortlovers.id/api'
ADMIN_KEY   = '00ca04e3e2702be565d7bf44e783255247708289bce9b2fb6187a2e117f87fd14'
ADMIN_HDR   = {'x-admin-key': ADMIN_KEY, 'Content-Type': 'application/json'}

R2_ENDPOINT = 'https://a142d3b29a5d64943cb251157e25eaf3.r2.cloudflarestorage.com'
R2_KEY_ID   = '07c99c897986ea52703c1285308d5e2c'
R2_SECRET   = '44788d376ffb216e1e73784b6fe1ff1423607928898a87c50819b52cdfc12e44'
R2_BUCKET   = 'shortlovers'
R2_PUBLIC   = 'https://stream.shortlovers.id'

PINE_API    = 'https://vidrama.asia/api/pine'

WEB_HDRS    = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36',
    'Referer': 'https://vidrama.asia/',
    'Cookie': '_fbp=fb.1.1770653154777.876935444165455244; global_ui_lang=id; cf_clearance=gi8rBDL4U_sV5dFUP.Dckjr.DONUzFar9fJlBMJx5_c-1778228148-1.2.1.1-rcSC4qbKF5H0KxB5Zt6Ic88iCIyXH7DESdcJA5w9WLWZvk58Y70clfcHFfqOyxmSRb1I97eRy.96PRr0zF1vV_PWs7vWkLZg2IsJNYLl5ZJvxdv7AnK4pZgxEBspgbrAod7jxce171vMiENcKPDXk_1eVFpBk_P5H8TA07xIBdq5HsL3uPTZKn8BCJv.HufjCR4mRr3DVOGDRagaNcc1CD_VmnRYY6tkanYH9QuDUyPeqreywRNxjb_5tsJVseZjz24po7Gw9o9ZVi3mSl9Ypm88Po1s4zr5n3DfE5R4BCKekPgqBAog2SDMQmDCWQJjMpzKKsJ_iXUHRaincYv9WQ'
}

TEMP_DIR = Path(tempfile.gettempdir()) / 'pine_scraper'
TEMP_DIR.mkdir(exist_ok=True)

# ── HELPERS ──────────────────────────────────────────────────────────────────
def get_r2():
    return boto3.client('s3', endpoint_url=R2_ENDPOINT,
                        aws_access_key_id=R2_KEY_ID, aws_secret_access_key=R2_SECRET,
                        config=Config(signature_version='s3v4'), region_name='auto')

def r2_exists(r2, key):
    try:
        r2.head_object(Bucket=R2_BUCKET, Key=key)
        return True
    except:
        return False

def r2_upload(r2, local_path, key, content_type='video/mp4'):
    r2.upload_file(str(local_path), R2_BUCKET, key,
                   ExtraArgs={'ContentType': content_type},
                   Config=boto3.s3.transfer.TransferConfig(
                       multipart_threshold=30*1024*1024,
                       multipart_chunksize=10*1024*1024))
    return f"{R2_PUBLIC}/{key}"

def slugify(text):
    text = text.lower()
    return re.sub(r'[\W_]+', '-', text).strip('-')

def check_duplicate_in_db(title):
    """Check if drama already exists in DB. Returns drama ID or None."""
    try:
        import urllib.parse
        words = title.strip().split()
        q = ' '.join(words[:4])
        r = requests.get(f"{API_BASE}/dramas/search?q={urllib.parse.quote(q)}", timeout=10)
        if r.ok:
            dramas = r.json().get('dramas', [])
            def clean_t(t):
                t = t.lower()
                return re.sub(r'[^a-z0-9]', '', t)
            my_clean = clean_t(title)
            for d in dramas:
                if clean_t(d['title']) == my_clean:
                    return d['id']
    except Exception as e:
        print(f"      [WARN] Error checking duplicate: {e}")
    return None

def generate_description(title, categories, api_desc=None):
    if api_desc and len(api_desc.strip()) > 20:
        return api_desc.strip()
    if not categories:
        categories = 'Drama, Romansa'
    title_lower = title.lower()
    if any(k in title_lower for k in ["suami", "istri", "nikah", "pengantin"]):
        return f"Drama pernikahan dan romansa menarik '{title}'. Kisah lika-liku hubungan rumah tangga, konflik keluarga, dan perjuangan cinta penuh kejutan."
    elif any(k in title_lower for k in ["bos", "ceo", "miliarder", "kaya"]):
        return f"Drama romansa perkotaan '{title}'. Kisah cinta beda status, konflik kekuasaan, dan intrik dunia bisnis penuh kejutan."
    elif any(k in title_lower for k in ["dendam", "khianat", "bangkit", "juara", "legenda"]):
        return f"Drama kebangkitan '{title}'. Kisah perjuangan merebut hak, mengatasi pengkhianatan, dan takdir yang penuh ketegangan."
    else:
        return f"Drama seru '{title}' bertema {categories}. Nikmati kisah yang penuh emosi, konflik mendalam, dan perjuangan cinta yang menghanyutkan di setiap episodenya."

def api_create_drama(title, description, cover_url, total_eps, categories):
    payload = {
        'title': title,
        'description': description,
        'cover': cover_url,
        'genres': [c.strip() for c in categories.split(',')][:3] if categories else ['Drama'],
        'totalEpisodes': total_eps,
        'isComplete': True,
        'country': 'China',
        'language': 'Indonesia',
        'status': 'completed',
        'provider': 'pine',
        'isActive': False,  # Pending!
    }
    try:
        r = requests.post(f"{API_BASE}/admin/dramas", headers=ADMIN_HDR, json=payload, timeout=20)
        if r.ok:
            return r.json().get('id')
        print(f"      [ERROR] Failed to create drama. Status: {r.status_code}, Body: {r.text[:200]}")
    except Exception as e:
        print(f"      [ERROR] Exception creating drama: {e}")
    return None

def api_mark_active(drama_db_id):
    try:
        r = requests.patch(f"{API_BASE}/admin/dramas/{drama_db_id}",
                          headers=ADMIN_HDR, json={'isActive': True}, timeout=15)
        return r.ok
    except:
        return False

def api_upsert_episode(drama_db_id, ep_no, url_720, url_540=None):
    payload = {
        'episodeNumber': ep_no,
        'title': f'Episode {ep_no}',
        'videoUrl': url_720,
        'isActive': True
    }
    if url_540:
        payload['videoUrl540p'] = url_540
    try:
        r = requests.post(f"{API_BASE}/admin/dramas/{drama_db_id}/episodes",
                          headers=ADMIN_HDR, json=payload, timeout=20)
        if not r.ok:
            print(f"      [WARN] DB Episode upsert failed. Status: {r.status_code}")
            return None
        return r.json().get('id')
    except Exception as e:
        print(f"      [ERROR] DB Episode upsert exception: {e}")
    return None

def encode_720_and_540(inp, out_720, out_540):
    cmd_720 = [
        'ffmpeg', '-y', '-i', str(inp),
        '-c:v', 'libx264', '-crf', '26', '-preset', 'fast',
        '-maxrate', '1500k', '-bufsize', '3000k',
        '-c:a', 'aac', '-b:a', '128k',
        '-movflags', '+faststart',
        '-loglevel', 'error', str(out_720)
    ]
    res = subprocess.run(cmd_720, timeout=600)
    if res.returncode != 0:
        return False
    cmd_540 = [
        'ffmpeg', '-y', '-i', str(out_720),
        '-vf', 'scale=-2:540',
        '-c:v', 'libx264', '-crf', '28', '-preset', 'fast',
        '-c:a', 'aac', '-b:a', '96k',
        '-movflags', '+faststart',
        '-loglevel', 'error', str(out_540)
    ]
    return subprocess.run(cmd_540, timeout=600).returncode == 0

def get_pine_drama_list():
    """Get all dramas from Pine provider."""
    r = requests.get(f"{PINE_API}?action=list", headers=WEB_HDRS, verify=False, timeout=15)
    if r.ok:
        return r.json().get('dramas', [])
    print(f"[ERROR] Failed to get drama list. Status: {r.status_code}")
    return []

def get_pine_detail(collection_id):
    """Get drama detail from Pine."""
    r = requests.get(f"{PINE_API}?action=detail&collection_id={collection_id}",
                     headers=WEB_HDRS, verify=False, timeout=15)
    if r.ok:
        return r.json()
    return None

def get_pine_episodes(collection_id):
    """Get episode list from Pine."""
    r = requests.get(f"{PINE_API}?action=episodes&collection_id={collection_id}",
                     headers=WEB_HDRS, verify=False, timeout=15)
    if r.ok:
        return r.json().get('episodes', [])
    return []

def get_pine_video_url(collection_id, ep_num, retries=3):
    """Get video playback URL for a specific episode."""
    for attempt in range(retries):
        try:
            r = requests.get(f"{PINE_API}?action=play&collection_id={collection_id}&episode={ep_num}",
                             headers=WEB_HDRS, verify=False, timeout=15)
            if r.ok:
                data = r.json()
                return data.get('playUrl')
        except Exception as e:
            print(f"      [WARN] Attempt {attempt+1} failed: {e}")
            time.sleep(2)
    return None

def download_video(url, out_path, retries=3):
    """Download a video file."""
    dl_hdrs = {
        'User-Agent': 'Mozilla/5.0',
        'Referer': 'https://www.tiktok.com/',
    }
    for attempt in range(retries):
        try:
            with requests.get(url, stream=True, headers=dl_hdrs, verify=False, timeout=120) as r:
                r.raise_for_status()
                with open(out_path, 'wb') as f:
                    for chunk in r.iter_content(chunk_size=1024*1024):
                        if chunk:
                            f.write(chunk)
            if Path(out_path).stat().st_size > 10000:
                return True
        except Exception as e:
            print(f"      [WARN] Download attempt {attempt+1} failed: {e}")
            time.sleep(3)
    return False

def scrape_drama(r2, drama_info):
    """Scrape a single drama from Pine provider."""
    collection_id = drama_info['id']
    title = drama_info.get('title', 'Unknown')
    
    print(f"\n{'='*60}")
    print(f"Processing: '{title}' (ID: {collection_id})")

    # 1. Check for duplicate in DB
    dup_id = check_duplicate_in_db(title)

    # 2. Get full detail
    detail = get_pine_detail(collection_id)
    if not detail:
        print(f"  -> [ERROR] Failed to get detail")
        return False

    total_eps = detail.get('totalEpisodes', 0)
    categories = detail.get('categories', 'Drama')
    description = detail.get('description', '')
    cover_url_raw = detail.get('cover') or detail.get('image', '')

    print(f"  -> Total episodes: {total_eps}")
    print(f"  -> Categories: {categories}")

    slug = slugify(title)
    prefix = f"pine/{slug}"

    if dup_id:
        print(f"  -> [DB] Already exists in DB (ID: {dup_id}). Resuming episode check...")
        drama_db_id = dup_id
    else:
        # 3. Download & upload cover
        cover_r2_key = f"{prefix}/cover.jpg"
        if r2_exists(r2, cover_r2_key):
            cover_r2_url = f"{R2_PUBLIC}/{cover_r2_key}"
            print(f"  -> [R2] Cover already exists")
        elif not cover_url_raw or cover_url_raw == 'None':
            # No cover available - use a default placeholder
            cover_r2_url = "https://stream.shortlovers.id/pine/sang-legenda/cover.jpg"
            print(f"  -> [WARN] No cover URL from API, using placeholder cover")
        else:
            try:
                cov_r = requests.get(cover_url_raw, headers=WEB_HDRS, timeout=30, verify=False)
                cov_r.raise_for_status()
                cover_path = TEMP_DIR / f"{slug}_cover.jpg"
                cover_path.write_bytes(cov_r.content)
                cover_r2_url = r2_upload(r2, cover_path, cover_r2_key, 'image/jpeg')
                cover_path.unlink(missing_ok=True)
                print(f"  -> [R2] Cover uploaded successfully")
            except Exception as e:
                print(f"  -> [WARN] Cover upload failed: {e}, using placeholder")
                cover_r2_url = "https://stream.shortlovers.id/pine/sang-legenda/cover.jpg"

        # 4. Create drama in DB
        desc = generate_description(title, categories, description)
        drama_db_id = api_create_drama(title, desc, cover_r2_url, total_eps, categories)
        if not drama_db_id:
            print(f"  -> [ERROR] Failed to create drama in DB")
            return False
        print(f"  -> [DB] Created drama entry (ID: {drama_db_id}, status: Pending)")

    # 5. Get episode list
    episodes = get_pine_episodes(collection_id)
    if not episodes:
        print(f"  -> [ERROR] No episodes found")
        return False

    print(f"  -> Total episodes to process: {len(episodes)}")

    # 6. Process each episode
    success_count = 0
    fail_count = 0

    for ep_info in episodes:
        ep_num = ep_info['num']
        ep_tag = f"ep{ep_num:03d}"
        
        r2_720_key = f"{prefix}/{ep_tag}_720.mp4"
        r2_540_key = f"{prefix}/{ep_tag}_540.mp4"

        # Check if already uploaded
        if r2_exists(r2, r2_720_key):
            url_720 = f"{R2_PUBLIC}/{r2_720_key}"
            url_540 = f"{R2_PUBLIC}/{r2_540_key}" if r2_exists(r2, r2_540_key) else None
            api_upsert_episode(drama_db_id, ep_num, url_720, url_540)
            print(f"    {ep_tag}: already in R2, linked to DB")
            success_count += 1
            continue

        # Get video URL
        video_url = get_pine_video_url(collection_id, ep_num)
        if not video_url:
            print(f"    {ep_tag}: processing... FAILED (no video URL)")
            fail_count += 1
            continue

        # Download
        raw_path = TEMP_DIR / f"{slug}_{ep_tag}_raw.mp4"
        out_720 = TEMP_DIR / f"{slug}_{ep_tag}_720.mp4"
        out_540 = TEMP_DIR / f"{slug}_{ep_tag}_540.mp4"

        print(f"    {ep_tag}: processing...", end='', flush=True)

        if not download_video(video_url, raw_path):
            print(f" FAILED (download error)")
            fail_count += 1
            continue

        # Encode
        if not encode_720_and_540(raw_path, out_720, out_540):
            print(f" FAILED (encode error)")
            raw_path.unlink(missing_ok=True)
            fail_count += 1
            continue

        raw_path.unlink(missing_ok=True)

        # Upload to R2
        try:
            url_720 = r2_upload(r2, out_720, r2_720_key)
            url_540 = None
            if out_540.exists() and out_540.stat().st_size > 1000:
                url_540 = r2_upload(r2, out_540, r2_540_key)
        except Exception as e:
            print(f" FAILED (R2 upload error: {e})")
            out_720.unlink(missing_ok=True)
            out_540.unlink(missing_ok=True)
            fail_count += 1
            continue

        out_720.unlink(missing_ok=True)
        out_540.unlink(missing_ok=True)

        # Save to DB
        api_upsert_episode(drama_db_id, ep_num, url_720, url_540)

        print(f" SUCCESS")
        success_count += 1

    print(f"\n  -> Scrape results for '{title}': {success_count} success, {fail_count} failed")

    # Mark drama as active if all episodes done
    if success_count > 0 and fail_count == 0:
        api_mark_active(drama_db_id)
        print(f"  -> [DB] Drama marked as Active!")
    else:
        print(f"  -> [DB] Drama stays Pending (review needed)")

    return success_count > 0

def main():
    print("=" * 60)
    print("  KingShort - Pine Provider Scraper")
    print("=" * 60)

    r2 = get_r2()

    # Get all dramas from Pine
    print("\nFetching drama list from Pine provider...")
    dramas = get_pine_drama_list()
    if not dramas:
        print("[ERROR] No dramas found in Pine provider!")
        return

    print(f"Found {len(dramas)} dramas in Pine provider:")
    for d in dramas:
        print(f"  - [{d['id']}] {d.get('title', 'N/A')}")

    print(f"\n{'='*60}")
    print("Starting scraping process...")
    print("=" * 60)

    total_success = 0
    total_skip = 0
    total_fail = 0

    for i, drama in enumerate(dramas, 1):
        print(f"\n[{i}/{len(dramas)}]", end='')
        
        success = scrape_drama(r2, drama)
        if success:
            total_success += 1
        else:
            total_fail += 1

        # Wait between dramas to avoid rate limiting
        if i < len(dramas):
            print(f"\nWaiting 5 seconds before next drama...")
            time.sleep(5)

    print(f"\n{'='*60}")
    print("SCRAPING COMPLETE!")
    print(f"  Success: {total_success}")
    print(f"  Failed:  {total_fail}")
    print("=" * 60)

if __name__ == '__main__':
    main()
