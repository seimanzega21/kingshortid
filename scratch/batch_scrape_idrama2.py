# -*- coding: utf-8 -*-
"""
Batch Scraper and Ingestion Script for 10 Dramas
Provider: idrama2
- Loops through a list of upstream drama IDs.
- Fetches metadata, registers the drama as Pending if missing.
- Downloads M3U8 streams, transcodes to 720p & 540p faststart MP4.
- Uploads to Cloudflare R2 and registers episodes to DB.
- Logs detailed progress to scratch/batch_scrape.log.
"""
import requests
import boto3
import sys
import json
import time
import os
import re
import subprocess
import argparse
import urllib3
from pathlib import Path
from botocore.config import Config

urllib3.disable_warnings()
sys.stdout.reconfigure(encoding='utf-8')

# Configuration
API_BASE = 'https://api.shortlovers.id/api'
ADMIN_KEY = '00ca04e3e2702be565d7bf44e783255247708289bce9b2fb6187a2e117f87fd14'
ADMIN_HDR = {'x-admin-key': ADMIN_KEY, 'Content-Type': 'application/json'}

R2_ENDPOINT = 'https://a142d3b29a5d64943cb251157e25eaf3.r2.cloudflarestorage.com'
R2_KEY_ID = '07c99c897986ea52703c1285308d5e2c'
R2_SECRET = '44788d376ffb216e1e73784b6fe1ff1423607928898a87c50819b52cdfc12e44'
R2_BUCKET = 'shortlovers'
R2_PUBLIC = 'https://stream.shortlovers.id'

HEADERS = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36',
    'Referer': 'https://vidrama.asia/',
}

# Directories
WORKSPACE_DIR = Path(__file__).resolve().parent.parent
TEMP_DIR = WORKSPACE_DIR / 'temp_batch'
TEMP_DIR.mkdir(exist_ok=True)
LOG_FILE = WORKSPACE_DIR / 'scratch' / 'batch_scrape.log'

def log(msg):
    timestamp = time.strftime('%Y-%m-%d %H:%M:%S')
    full_msg = f"[{timestamp}] {msg}"
    print(full_msg, flush=True)
    with open(LOG_FILE, 'a', encoding='utf-8') as f:
        f.write(full_msg + '\n')

def get_r2():
    return boto3.client(
        's3', endpoint_url=R2_ENDPOINT,
        aws_access_key_id=R2_KEY_ID, aws_secret_access_key=R2_SECRET,
        config=Config(signature_version='s3v4'), region_name='auto'
    )

def make_slug(title):
    s = title.strip().lower()
    s = s.replace("(dubbing)", "")
    s = s.replace("(sulih suara)", "")
    s = re.sub(r'[^\w\s-]', '', s)
    s = re.sub(r'[-\s]+', '-', s)
    return s.strip('-')

def get_db_drama_by_title(title):
    """Search for existing drama in local database by title"""
    try:
        url = f"{API_BASE}/dramas/search?q={requests.utils.quote(title)}"
        r = requests.get(url, timeout=15)
        if r.ok:
            dramas = r.json()
            if isinstance(dramas, dict):
                dramas = dramas.get('dramas', [])
            for d in dramas:
                if d.get('title', '').lower().strip() == title.lower().strip():
                    return d.get('id')
    except Exception as e:
        log(f"  [WARN] DB duplicate check failed: {e}")
    return None

def register_drama_api(title, meta, cover_r2_url):
    """Register drama in admin panel as Pending (isActive=False)"""
    payload = {
        'title': title,
        'description': meta.get('introduction', ''),
        'cover': cover_r2_url,
        'genres': [],
        'totalEpisodes': meta.get('current_count', 0),
        'status': 'ongoing',
        'country': 'China',
        'language': 'Indonesia',
        'isActive': False,  # Pending
        'isVip': False,
    }
    r = requests.post(f"{API_BASE}/admin/dramas", headers=ADMIN_HDR, json=payload, timeout=30)
    if r.ok:
        return r.json().get('id')
    log(f"  [ERROR] Failed to register drama in DB. Status: {r.status_code}, Body: {r.text[:200]}")
    return None

def get_registered_episodes(drama_db_id):
    """Fetch registered episode numbers from DB"""
    url = f"{API_BASE}/dramas/{drama_db_id}/episodes?includeInactive=true"
    r = requests.get(url, timeout=15)
    if r.ok:
        eps = r.json()
        ep_list = eps if isinstance(eps, list) else eps.get('episodes', eps.get('data', []))
        return {e.get('episodeNumber') for e in ep_list}
    return set()

def fetch_episode_unlock_info(upstream_id, ep_no):
    """Call unlock API for the episode"""
    url = f"https://vidrama.asia/api/idrama2/unlock/{upstream_id}/{ep_no}?lang=id"
    r = requests.get(url, headers=HEADERS, verify=False, timeout=20)
    if r.ok:
        data = r.json()
        return data.get('target_ep_info', {})
    return {}

def download_m3u8_stream(m3u8_url, local_path):
    """Download HLS stream and transcode to 720p faststart MP4"""
    headers_str = f"Referer: https://vidrama.asia/\r\nUser-Agent: {HEADERS['User-Agent']}\r\n"
    cmd = [
        'ffmpeg', '-y',
        '-headers', headers_str,
        '-i', m3u8_url,
        '-c:v', 'libx264', '-crf', '26',
        '-preset', 'fast',
        '-maxrate', '1500k', '-bufsize', '3000k',
        '-c:a', 'aac', '-b:a', '128k',
        '-movflags', '+faststart',
        '-loglevel', 'error',
        str(local_path)
    ]
    res = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    return res.returncode == 0

def downscale_to_540p(input_path, output_path):
    """Downscale 720p local file to 540p faststart MP4"""
    cmd = [
        'ffmpeg', '-y', '-i', str(input_path),
        '-vf', 'scale=-2:540',
        '-c:v', 'libx264', '-crf', '28',
        '-preset', 'fast',
        '-c:a', 'aac', '-b:a', '96k',
        '-movflags', '+faststart',
        '-loglevel', 'error',
        str(output_path)
    ]
    res = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    return res.returncode == 0

def r2_upload_file(r2, local_path, key, content_type='video/mp4'):
    """Upload file to Cloudflare R2"""
    r2.upload_file(str(local_path), R2_BUCKET, key, ExtraArgs={
        'ContentType': content_type,
        'CacheControl': 'public, max-age=31536000'
    })
    return f"{R2_PUBLIC}/{key}"

def register_episode_db(drama_db_id, ep_no, url_720, url_540):
    """Register episode in DB"""
    payload = {
        'episodeNumber': ep_no,
        'title': f'Episode {ep_no}',
        'videoUrl': url_720,
        'videoUrl540p': url_540,
        'isVip': False,
        'coinPrice': 0,
        'isActive': True
    }
    r = requests.post(f"{API_BASE}/admin/dramas/{drama_db_id}/episodes", headers=ADMIN_HDR, json=payload, timeout=20)
    if r.ok:
        return r.json().get('id')
    return None

def register_subtitles_db(episode_db_id, r2_sub_url):
    """Register subtitle track in DB"""
    payload = {
        'language': 'id',
        'label': 'Bahasa Indonesia',
        'url': r2_sub_url,
        'isDefault': True
    }
    r = requests.post(f"{API_BASE}/episodes/{episode_db_id}/subtitles", headers=ADMIN_HDR, json=payload, timeout=15)
    return r.ok

def process_single_drama(r2, upstream_id, dry_run=False, limit_eps=None):
    log("-" * 50)
    log(f"Processing Upstream ID: {upstream_id}")
    log("-" * 50)

    # 1. Fetch metadata
    meta_url = f"https://vidrama.asia/api/idrama2/drama/{upstream_id}?lang=id"
    try:
        r = requests.get(meta_url, headers=HEADERS, verify=False, timeout=20)
        if not r.ok:
            log(f"  [ERROR] Failed to fetch metadata. Status: {r.status_code}")
            return False
    except Exception as e:
        log(f"  [ERROR] Metadata request failed: {e}")
        return False
    
    meta = r.json()
    raw_title = meta.get('short_play_name', '').strip()
    if not raw_title:
        log("  [ERROR] Drama title is empty, skipping.")
        return False

    total_eps = meta.get('current_count', 0) or len(meta.get('episode_list', []))
    cover_raw = meta.get('cover_url')

    # Standardize Title Prefix
    if "(Sulih Suara)" in raw_title:
        search_title = raw_title
    else:
        # Check if the metadata contains dubbed tags or categories
        tags = [t.get('tag_local', '').lower() for t in meta.get('content_tag', [])]
        if 'sulih suara' in tags or 'dubbed' in tags or 'dubbing' in tags:
            search_title = f"(Sulih Suara) {raw_title}"
        else:
            search_title = raw_title

    slug = make_slug(search_title)

    log(f"  Title: {search_title}")
    log(f"  Slug: {slug}")
    log(f"  Total Episodes: {total_eps}")
    log(f"  Cover: {cover_raw}")

    # Check DB duplicate
    drama_db_id = get_db_drama_by_title(search_title)
    if drama_db_id:
        log(f"  [OK] Drama already exists in DB. ID: {drama_db_id}")
    elif dry_run:
        log(f"  [DRY RUN] Would register drama: {search_title}")
        drama_db_id = "dry-run-id"
    else:
        # Upload cover
        cover_r2_url = ''
        if cover_raw:
            log("  Uploading cover to R2...")
            try:
                cov_r = requests.get(cover_raw, timeout=20, verify=False)
                if cov_r.ok:
                    cover_key = f"dramas/{slug}/cover.jpg"
                    r2.put_object(Bucket=R2_BUCKET, Key=cover_key, Body=cov_r.content, ContentType='image/jpeg')
                    cover_r2_url = f"{R2_PUBLIC}/{cover_key}"
                    log(f"    [OK] Cover uploaded: {cover_r2_url}")
            except Exception as e:
                log(f"    [WARN] Cover upload failed: {e}")
                cover_r2_url = cover_raw

        # Register drama in DB
        log("  Registering drama in DB (status=Pending)...")
        drama_db_id = register_drama_api(search_title, meta, cover_r2_url)
        if not drama_db_id:
            log("  [ERROR] Failed to register drama. Skipping.")
            return False
        log(f"  [OK] Drama registered! DB ID: {drama_db_id}")

    # 2. Episode loop
    registered_eps = get_registered_episodes(drama_db_id) if not dry_run else set()
    log(f"  Registered episode numbers: {sorted(list(registered_eps))}")

    processed_eps = 0
    for ep_no in range(1, total_eps + 1):
        if ep_no in registered_eps:
            continue

        if limit_eps and processed_eps >= limit_eps:
            log(f"  Reached limit of {limit_eps} episodes for this drama.")
            break

        log(f"  EP {ep_no}/{total_eps}:")

        # Fetch unlock info
        unlock_info = {}
        for attempt in range(5):
            try:
                unlock_info = fetch_episode_unlock_info(upstream_id, ep_no)
                if unlock_info and unlock_info.get('play_url'):
                    break
            except Exception as e:
                log(f"    [WARN] Attempt {attempt+1} failed: {e}")
            if attempt < 4:
                time.sleep(5)

        if not unlock_info or not unlock_info.get('play_url'):
            log(f"    [ERROR] Failed to get play_url for EP {ep_no}")
            continue

        m3u8_url = unlock_info['play_url']

        # Find Indonesian subtitle
        sub_url = None
        sub_lists = []
        if 'screentext_list' in unlock_info and isinstance(unlock_info['screentext_list'], list):
            sub_lists.extend(unlock_info['screentext_list'])
        if 'subtitle_list' in unlock_info and isinstance(unlock_info['subtitle_list'], list):
            sub_lists.extend(unlock_info['subtitle_list'])

        for s in sub_lists:
            lang = s.get('language', '').lower()
            if lang == 'id' and s.get('url'):
                sub_url = s['url']
                break

        if dry_run:
            log(f"    [DRY RUN] Would process EP {ep_no} (has stream, subtitle={bool(sub_url)})")
            processed_eps += 1
            continue

        # Local files paths
        out_720_local = TEMP_DIR / f"{upstream_id}_ep{ep_no:03d}_720p.mp4"
        out_540_local = TEMP_DIR / f"{upstream_id}_ep{ep_no:03d}_540p.mp4"

        try:
            # A. Download & Transcode 720p
            log("    Downloading and transcoding 720p...")
            t0 = time.time()
            if not download_m3u8_stream(m3u8_url, out_720_local):
                log("      [ERROR] Transcoding 720p failed")
                continue
            log(f"      [OK] 720p done: {out_720_local.stat().st_size / 1024 / 1024:.1f}MB (took {time.time()-t0:.1f}s)")

            # B. Downscale to 540p
            log("    Downscaling to 540p...")
            t0 = time.time()
            if not downscale_to_540p(out_720_local, out_540_local):
                log("      [ERROR] Downscaling failed")
                continue
            log(f"      [OK] 540p done: {out_540_local.stat().st_size / 1024 / 1024:.1f}MB (took {time.time()-t0:.1f}s)")

            # C. Upload to R2
            log("    Uploading to R2...")
            key_720 = f"dramas/{slug}/ep{ep_no:03d}_720p.mp4"
            key_540 = f"dramas/{slug}/ep{ep_no:03d}_540p.mp4"
            r2_url_720 = r2_upload_file(r2, out_720_local, key_720)
            r2_url_540 = r2_upload_file(r2, out_540_local, key_540)

            # D. Subtitle Upload
            r2_sub_url = None
            if sub_url:
                log("    Uploading subtitle...")
                try:
                    sub_r = requests.get(sub_url, headers=HEADERS, timeout=15, verify=False)
                    if sub_r.ok:
                        sub_key = f"dramas/{slug}/ep{ep_no:03d}_id.vtt"
                        r2.put_object(Bucket=R2_BUCKET, Key=sub_key, Body=sub_r.content, ContentType='text/vtt')
                        r2_sub_url = f"{R2_PUBLIC}/{sub_key}"
                except Exception as e:
                    log(f"      [WARN] Subtitle upload failed: {e}")

            # E. Register in DB
            ep_db_id = register_episode_db(drama_db_id, ep_no, r2_url_720, r2_url_540)
            if ep_db_id:
                log(f"    [OK] EP {ep_no} registered in DB.")
                if r2_sub_url:
                    register_subtitles_db(ep_db_id, r2_sub_url)
                processed_eps += 1
            else:
                log(f"    [ERROR] EP {ep_no} failed to register in DB.")

        except Exception as e:
            log(f"    [ERROR] EP {ep_no} error: {e}")
        finally:
            # Cleanup temp files
            for p in [out_720_local, out_540_local]:
                if p.exists():
                    try:
                        p.unlink()
                    except: pass

        time.sleep(1.0)

    log(f"Finished Upstream ID: {upstream_id}. Ingested {processed_eps} new episodes.")
    return True

def main():
    parser = argparse.ArgumentParser(description="Batch Scrape 10 dramas from idrama2")
    parser.add_argument('--dry-run', action='store_true', help='Validate metadata and loop structure without transcoding')
    parser.add_argument('--limit-episodes', type=int, default=None, help='Limit number of episodes per drama for testing')
    args = parser.parse_args()

    # Clear/Initialize Log
    with open(LOG_FILE, 'w', encoding='utf-8') as f:
        f.write(f"--- BATCH SCRAPE START (DRY_RUN={args.dry_run}) ---\n")

    log("============================================================")
    log("BATCH SCRAPING PIPELINE STARTED")
    log("============================================================")

    # List of Upstream IDs provided by user
    drama_ids = [
        '160000641572',  # Istriku Bisa Bunuh Dewa
        '160000641860',  # Aku Terlahir Terlalu Patuh
        '160000641817',  # Suamiku Bos Besar Kukira Tukang Loak
        '160000641753',  # Duke Jadi Senjata Dendamku
        '161001641437',  # Kembalinya Sang Master
        '161001640083',  # Jejak Cinta Manis
        '160000642054',  # Peraturan Terlarang Wanita Itu Milikku
        '160000641763',  # Sang Pembunuh di Balik Wajah Manja
        '161001640339',  # Cinta Bersemi di Peternakan
        '161001641281',  # Nona Ketua Geng Kembali
    ]

    r2 = None if args.dry_run else get_r2()

    # Clean up temp dir before start
    if not args.dry_run:
        if TEMP_DIR.exists():
            import shutil
            for child in TEMP_DIR.iterdir():
                try:
                    if child.is_file() or child.is_symlink():
                        child.unlink()
                    elif child.is_dir():
                        shutil.rmtree(child)
                except Exception as e:
                    log(f"[WARN] Temp clean error: {e}")

    success_count = 0
    for idx, uid in enumerate(drama_ids, 1):
        log(f"\n[DRAMA {idx}/10]")
        if process_single_drama(r2, uid, dry_run=args.dry_run, limit_eps=args.limit_episodes):
            success_count += 1
        time.sleep(2.0)

    log("\n" + "=" * 60)
    log(f"BATCH PROCESS COMPLETED! Success: {success_count}/{len(drama_ids)}")
    log("=" * 60)

if __name__ == '__main__':
    main()
