#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
KingShort - Pine Queue Scraper
==============================
Membaca scripts/pine_queue.json dan memproses drama satu per satu.
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

# ── CONFIG ────────────────────────────────────────────────────────────────────
API_BASE    = 'https://api.shortlovers.id/api'
ADMIN_KEY   = '00ca04e3e2702be565d7bf44e783255247708289bce9b2fb6187a2e117f87fd14'
ADMIN_HDR   = {'x-admin-key': ADMIN_KEY, 'Content-Type': 'application/json'}

R2_ENDPOINT = 'https://a142d3b29a5d64943cb251157e25eaf3.r2.cloudflarestorage.com'
R2_KEY_ID   = '07c99c897986ea52703c1285308d5e2c'
R2_SECRET   = '44788d376ffb216e1e73784b6fe1ff1423607928898a87c50819b52cdfc12e44'
R2_BUCKET   = 'shortlovers'
R2_PUBLIC   = 'https://stream.shortlovers.id'

PINE_API    = 'https://vidrama.asia/api/pine'
QUEUE_PATH  = Path(__file__).parent / 'pine_queue.json'

WEB_HDRS = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36',
    'Referer': 'https://vidrama.asia/',
    'Cookie': '_fbp=fb.1.1770653154777.876935444165455244; global_ui_lang=id; cf_clearance=gi8rBDL4U_sV5dFUP.Dckjr.DONUzFar9fJlBMJx5_c-1778228148-1.2.1.1-rcSC4qbKF5H0KxB5Zt6Ic88iCIyXH7DESdcJA5w9WLWZvk58Y70clfcHFfqOyxmSRb1I97eRy.96PRr0zF1vV_PWs7vWkLZg2IsJNYLl5ZJvxdv7AnK4pZgxEBspgbrAod7jxce171vMiENcKPDXk_1eVFpBk_P5H8TA07xIBdq5HsL3uPTZKn8BCJv.HufjCR4mRr3DVOGDRagaNcc1CD_VmnRYY6tkanYH9QuDUyPeqreywRNxjb_5tsJVseZjz24po7Gw9o9ZVi3mSl9Ypm88Po1s4zr5n3DfE5R4BCKekPgqBAog2SDMQmDCWQJjMpzKKsJ_iXUHRaincYv9WQ'
}

TEMP_DIR = Path(tempfile.gettempdir()) / 'pine_queue_scraper'
TEMP_DIR.mkdir(exist_ok=True)

# ── HELPERS ───────────────────────────────────────────────────────────────────
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
    try:
        import urllib.parse
        words = title.strip().split()
        q = ' '.join(words[:4])
        r = requests.get(f"{API_BASE}/dramas/search?q={urllib.parse.quote(q)}", timeout=10)
        if r.ok:
            dramas = r.json().get('dramas', [])
            def clean_t(t):
                return re.sub(r'[^a-z0-9]', '', t.lower())
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
    title_lower = title.lower()
    cats = categories or 'Drama'
    if any(k in title_lower for k in ["dendam", "balas", "khianat", "bangkit", "juara", "legenda", "master"]):
        return f"Drama kebangkitan dan balas dendam '{title}'. Kisah perjuangan merebut hak, mengatasi pengkhianatan, dan takdir penuh ketegangan yang memukau di setiap episodenya."
    elif any(k in title_lower for k in ["suami", "istri", "nikah", "kontrak"]):
        return f"Drama romansa '{title}'. Kisah lika-liku hubungan, konflik cinta, dan perjuangan menuju kebahagiaan sejati yang penuh kejutan."
    elif any(k in title_lower for k in ["raja", "dewa", "kaisar", "ratu", "putri"]):
        return f"Drama fantasi epik '{title}'. Kisah kekuasaan, kebangkitan sang tokoh utama, dan perjuangan menghadapi takdir yang menghanyutkan."
    elif any(k in title_lower for k in ["dokter", "satpam", "master", "peramal"]):
        return f"Drama aksi seru '{title}'. Kisah seseorang yang menyembunyikan kemampuan tersembunyinya, mengejutkan semua orang di sekitarnya."
    else:
        return f"Drama seru '{title}' bertema {cats}. Penuh emosi, konflik mendalam, dan perjuangan cinta yang menghanyutkan di setiap episodenya."

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
        'isActive': False,
    }
    try:
        r = requests.post(f"{API_BASE}/admin/dramas", headers=ADMIN_HDR, json=payload, timeout=20)
        if r.ok:
            return r.json().get('id')
        print(f"      [ERROR] Create drama failed: {r.status_code} {r.text[:200]}")
    except Exception as e:
        print(f"      [ERROR] Create drama exception: {e}")
    return None

def api_mark_active(drama_db_id):
    try:
        r = requests.patch(f"{API_BASE}/admin/dramas/{drama_db_id}",
                           headers=ADMIN_HDR, json={'isActive': True}, timeout=15)
        return r.ok
    except:
        return False

def api_upsert_episode(drama_db_id, ep_no, url_720, url_540=None):
    payload = {'episodeNumber': ep_no, 'title': f'Episode {ep_no}', 'videoUrl': url_720, 'isActive': True}
    if url_540:
        payload['videoUrl540p'] = url_540
    try:
        r = requests.post(f"{API_BASE}/admin/dramas/{drama_db_id}/episodes",
                          headers=ADMIN_HDR, json=payload, timeout=20)
        if not r.ok:
            print(f"      [WARN] Episode upsert failed: {r.status_code}")
            return None
        return r.json().get('id')
    except Exception as e:
        print(f"      [ERROR] Episode upsert exception: {e}")
    return None

def encode_video(inp, out_720, out_540):
    cmd = ['ffmpeg', '-y', '-i', str(inp),
           '-c:v', 'libx264', '-crf', '26', '-preset', 'fast',
           '-maxrate', '1500k', '-bufsize', '3000k',
           '-c:a', 'aac', '-b:a', '128k', '-movflags', '+faststart',
           '-loglevel', 'error', str(out_720)]
    if subprocess.run(cmd, timeout=600).returncode != 0:
        return False
    cmd2 = ['ffmpeg', '-y', '-i', str(out_720), '-vf', 'scale=-2:540',
            '-c:v', 'libx264', '-crf', '28', '-preset', 'fast',
            '-c:a', 'aac', '-b:a', '96k', '-movflags', '+faststart',
            '-loglevel', 'error', str(out_540)]
    return subprocess.run(cmd2, timeout=600).returncode == 0

def get_video_url(collection_id, ep_num, retries=3):
    for attempt in range(retries):
        try:
            r = requests.get(f"{PINE_API}?action=play&collection_id={collection_id}&episode={ep_num}",
                             headers=WEB_HDRS, verify=False, timeout=15)
            if r.ok:
                return r.json().get('playUrl')
        except Exception as e:
            print(f"      [WARN] Attempt {attempt+1} play URL failed: {e}")
            time.sleep(2)
    return None

def download_video(url, out_path, retries=3):
    dl_hdrs = {'User-Agent': 'Mozilla/5.0', 'Referer': 'https://www.tiktok.com/'}
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

def load_queue():
    with open(QUEUE_PATH, 'r', encoding='utf-8') as f:
        return json.load(f)

def save_queue(queue):
    with open(QUEUE_PATH, 'w', encoding='utf-8') as f:
        json.dump(queue, f, ensure_ascii=False, indent=2)

def scrape_drama(r2, item):
    collection_id = item['id']
    title = item['title']

    print(f"\n{'='*60}")
    print(f"=== PROCESSING QUEUE ITEM ===")
    print(f"ID: {collection_id}")
    print(f"Title: {title}")
    print(f"Status: pending")

    # Check duplicate
    dup_id = check_duplicate_in_db(title)
    if dup_id:
        print(f"  -> [SKIP] Already in DB (ID: {dup_id})")
        return 'skipped'

    # Get detail
    r = requests.get(f"{PINE_API}?action=detail&collection_id={collection_id}",
                     headers=WEB_HDRS, verify=False, timeout=15)
    if not r.ok or not r.json().get('title'):
        print(f"  -> [ERROR] Failed to get detail: {r.status_code}")
        return 'failed'
    detail = r.json()

    total_eps = detail.get('totalEpisodes', 0)
    categories = detail.get('categories', 'Drama')
    description = detail.get('description', '')
    cover_url_raw = detail.get('cover') or detail.get('image', '')
    slug = slugify(title)
    prefix = f"pine/{slug}"

    print(f"\nProcessing drama: '{title}' (ID: {collection_id}, Slug: {slug})")

    # Upload cover
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

    # Create drama in DB
    desc = generate_description(title, categories, description)
    drama_db_id = api_create_drama(title, desc, cover_r2_url, total_eps, categories)
    if not drama_db_id:
        print(f"  -> [ERROR] Failed to create drama in DB")
        return 'failed'
    print(f"  -> [DB] Created drama entry (ID: {drama_db_id}, status: Pending)")

    # Get episodes
    ep_r = requests.get(f"{PINE_API}?action=episodes&collection_id={collection_id}",
                        headers=WEB_HDRS, verify=False, timeout=15)
    episodes = ep_r.json().get('episodes', []) if ep_r.ok else []
    if not episodes:
        print(f"  -> [ERROR] No episodes found")
        return 'failed'

    print(f"  -> Total Episodes to process: {len(episodes)}")

    success_count = 0
    fail_count = 0

    for ep_info in episodes:
        ep_num = ep_info['num']
        ep_tag = f"ep{ep_num:03d}"
        r2_720_key = f"{prefix}/{ep_tag}_720.mp4"
        r2_540_key = f"{prefix}/{ep_tag}_540.mp4"

        if r2_exists(r2, r2_720_key):
            url_720 = f"{R2_PUBLIC}/{r2_720_key}"
            url_540 = f"{R2_PUBLIC}/{r2_540_key}" if r2_exists(r2, r2_540_key) else None
            api_upsert_episode(drama_db_id, ep_num, url_720, url_540)
            print(f"    {ep_tag}: already in R2, linked to DB")
            success_count += 1
            continue

        print(f"    {ep_tag}: processing...", end='', flush=True)

        video_url = get_video_url(collection_id, ep_num)
        if not video_url:
            print(f" FAILED (no video URL)")
            fail_count += 1
            continue

        raw_path = TEMP_DIR / f"{slug}_{ep_tag}_raw.mp4"
        out_720  = TEMP_DIR / f"{slug}_{ep_tag}_720.mp4"
        out_540  = TEMP_DIR / f"{slug}_{ep_tag}_540.mp4"

        if not download_video(video_url, raw_path):
            print(f" FAILED (download error)")
            fail_count += 1
            continue

        if not encode_video(raw_path, out_720, out_540):
            print(f" FAILED (encode error)")
            raw_path.unlink(missing_ok=True)
            fail_count += 1
            continue

        raw_path.unlink(missing_ok=True)

        try:
            url_720 = r2_upload(r2, out_720, r2_720_key)
            url_540 = r2_upload(r2, out_540, r2_540_key) if out_540.exists() and out_540.stat().st_size > 1000 else None
        except Exception as e:
            print(f" FAILED (R2 upload: {e})")
            out_720.unlink(missing_ok=True)
            out_540.unlink(missing_ok=True)
            fail_count += 1
            continue

        out_720.unlink(missing_ok=True)
        out_540.unlink(missing_ok=True)

        api_upsert_episode(drama_db_id, ep_num, url_720, url_540)
        print(f" SUCCESS")
        success_count += 1

    result_str = f"{success_count} success, {fail_count} failed, 0 skipped."
    print(f"  -> Scrape results for '{title}': {result_str}")

    if success_count > 0:
        api_mark_active(drama_db_id)
        print(f"Successfully processed and marked '{title}' as completed.")
        return 'done'
    return 'failed'

def main():
    print("=" * 60)
    print("  KingShort - Pine Queue Scraper")
    print("=" * 60)

    if not QUEUE_PATH.exists():
        print(f"[ERROR] Queue file not found: {QUEUE_PATH}")
        return

    r2 = get_r2()
    queue = load_queue()
    pending = [item for item in queue if item.get('status') == 'pending']

    print(f"\nTotal pending items: {len(pending)}")

    for i, item in enumerate(queue):
        if item.get('status') != 'pending':
            continue

        result = scrape_drama(r2, item)
        item['status'] = result
        save_queue(queue)

        pending_left = sum(1 for x in queue if x.get('status') == 'pending')
        if pending_left > 0:
            print(f"\nWaiting 5 seconds before next drama to avoid rate limiting...")
            time.sleep(5)

    print(f"\n{'='*60}")
    done  = sum(1 for x in queue if x.get('status') == 'done')
    skip  = sum(1 for x in queue if x.get('status') == 'skipped')
    fail  = sum(1 for x in queue if x.get('status') == 'failed')
    print(f"=== NO MORE PENDING DRAMAS FOUND IN QUEUE ===")
    print(f"Done: {done} | Skipped: {skip} | Failed: {fail}")
    print("=" * 60)

if __name__ == '__main__':
    main()
