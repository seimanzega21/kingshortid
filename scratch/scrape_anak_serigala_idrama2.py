# -*- coding: utf-8 -*-
"""
Scraper and Ingestion Script for "Aku Lahirkan Anak Serigala Presiden"
Provider: idrama2
Upstream ID: 160001641891
- Fetches metadata and unlocks episodes 1 to 39.
- Downloads M3U8 streams using FFmpeg.
- Transcodes to 720p and downscales to 540p faststart MP4.
- Uploads to Cloudflare R2.
- Ingests into Database with Pending status (isActive = False).
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

# ─── CONFIG ─────────────────────────────────────────────────────────────────
DRAMA_UPSTREAM_ID = '160001641891'
SLUG = 'aku-lahirkan-anak-serigala-presiden'

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
TEMP_DIR = WORKSPACE_DIR / 'temp_serigala'
TEMP_DIR.mkdir(exist_ok=True)

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
        print(f"  ⚠ DB duplicate check failed: {e}")
    return None

def register_drama_api(meta, cover_r2_url):
    """Register drama in admin panel as Pending (isActive=False)"""
    payload = {
        'title': 'Aku Lahirkan Anak Serigala Presiden (Sulih Suara)',
        'description': meta.get('introduction', ''),
        'cover': cover_r2_url,
        'genres': [],
        'totalEpisodes': meta.get('current_count', 39),
        'status': 'ongoing',
        'country': 'China',
        'language': 'Indonesia',
        'isActive': False,  # Pending
        'isVip': False,
    }
    r = requests.post(f"{API_BASE}/admin/dramas", headers=ADMIN_HDR, json=payload, timeout=30)
    if r.ok:
        return r.json().get('id')
    print(f"  ✗ Failed to register drama in DB. Status: {r.status_code}, Body: {r.text[:200]}")
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

def fetch_episode_unlock_info(ep_no):
    """Call unlock API for the episode"""
    url = f"https://vidrama.asia/api/idrama2/unlock/{DRAMA_UPSTREAM_ID}/{ep_no}?lang=id"
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

def main():
    parser = argparse.ArgumentParser(description="Scrape and ingest Aku Lahirkan Anak Serigala Presiden from idrama2")
    parser.add_argument('--dry-run', action='store_true', help='Validate endpoints and metadata without processing')
    parser.add_argument('--limit-episodes', type=int, default=None, help='Limit number of episodes to process for testing')
    args = parser.parse_args()

    print("=" * 60)
    print("STARTING PIPELINE: Aku Lahirkan Anak Serigala Presiden")
    print("=" * 60)

    if args.dry_run:
        print("!!! DRY RUN MODE ACTIVE !!!")
        print("=" * 60)
    else:
        # Cleanup temp directory
        if TEMP_DIR.exists():
            import shutil
            print("Cleaning up temp directory...")
            for child in TEMP_DIR.iterdir():
                try:
                    if child.is_file() or child.is_symlink():
                        child.unlink()
                    elif child.is_dir():
                        shutil.rmtree(child)
                except Exception as e:
                    print(f"  ⚠ Cleanup temp file failed for {child.name}: {e}")

    r2 = None if args.dry_run else get_r2()

    # 1. Fetch metadata
    print("Fetching drama metadata from Vidrama...")
    meta_url = f"https://vidrama.asia/api/idrama2/drama/{DRAMA_UPSTREAM_ID}?lang=id"
    r = requests.get(meta_url, headers=HEADERS, verify=False, timeout=20)
    if not r.ok:
        print(f"Failed to fetch metadata. Status: {r.status_code}")
        return
    
    meta = r.json()
    title = meta.get('short_play_name', 'Aku Lahirkan Anak Serigala Presiden').strip()
    total_eps = meta.get('current_count', 39)
    cover_raw = meta.get('cover_url')
    print(f"Drama: {title}")
    print(f"Total Episodes: {total_eps}")
    print(f"Cover URL: {cover_raw}")

    # Check database duplicate
    search_title = f"{title} (Sulih Suara)"
    drama_db_id = get_db_drama_by_title(search_title)

    if drama_db_id:
        print(f"✓ Drama already exists in DB. ID: {drama_db_id}")
    elif args.dry_run:
        print(f"[DRY RUN] Would register drama: {search_title}")
        drama_db_id = "dry-run-drama-id"
    else:
        # Upload cover to R2
        cover_r2_url = ''
        if cover_raw:
            print("Uploading cover to R2...")
            try:
                cov_r = requests.get(cover_raw, timeout=20, verify=False)
                if cov_r.ok:
                    cover_key = f"dramas/{SLUG}/cover.jpg"
                    r2.put_object(Bucket=R2_BUCKET, Key=cover_key, Body=cov_r.content, ContentType='image/jpeg')
                    cover_r2_url = f"{R2_PUBLIC}/{cover_key}"
                    print(f"  ✓ Cover uploaded: {cover_r2_url}")
            except Exception as e:
                print(f"  ⚠ Failed to upload cover: {e}")
                cover_r2_url = cover_raw # fallback

        # Register drama
        print("Registering drama in database (status=Pending)...")
        drama_db_id = register_drama_api(meta, cover_r2_url)
        if not drama_db_id:
            print("Failed to register drama. Exiting.")
            return
        print(f"✓ Drama registered! DB ID: {drama_db_id}")

    # 2. Episode loop
    registered_eps = get_registered_episodes(drama_db_id) if not args.dry_run else set()
    print("Registered episode numbers:", sorted(list(registered_eps)))

    processed = 0
    for ep_no in range(1, total_eps + 1):
        if ep_no in registered_eps:
            print(f"  ✓ EP {ep_no} already registered. Skipping.")
            continue

        if args.limit_episodes and processed >= args.limit_episodes:
            print(f"\nLimit of {args.limit_episodes} episodes reached. Stopping loop.")
            break

        print(f"\n📹 Processing Episode {ep_no}/{total_eps}:")
        
        # A. Fetch unlock info
        unlock_info = {}
        for attempt in range(5):
            try:
                unlock_info = fetch_episode_unlock_info(ep_no)
                if unlock_info and unlock_info.get('play_url'):
                    break
            except Exception as e:
                print(f"    ⚠ Attempt {attempt+1} failed: {e}")
            if attempt < 4:
                print(f"    Waiting 5 seconds before retry...")
                time.sleep(5)

        if not unlock_info or not unlock_info.get('play_url'):
            print(f"    ✗ Failed to get play_url for EP {ep_no}")
            continue

        m3u8_url = unlock_info['play_url']
        print(f"    HLS M3U8 stream URL found.")

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

        if sub_url:
            print(f"    Indonesian subtitle track found: {sub_url[:70]}...")
        else:
            print(f"    ⚠ No Indonesian subtitle track found for EP {ep_no}")

        if args.dry_run:
            print(f"    [DRY RUN] Would download and process EP {ep_no}")
            processed += 1
            continue

        # Paths
        out_720_local = TEMP_DIR / f"ep{ep_no:03d}_720p.mp4"
        out_540_local = TEMP_DIR / f"ep{ep_no:03d}_540p.mp4"

        try:
            # B. Download & Transcode 720p
            print("    ⬇ Downloading and transcoding 720p...", end='', flush=True)
            t0 = time.time()
            if download_m3u8_stream(m3u8_url, out_720_local):
                print(f" ✓ {out_720_local.stat().st_size / 1024 / 1024:.1f}MB (took {time.time()-t0:.1f}s)")
            else:
                print(" ✗ Transcoding failed")
                continue

            # C. Downscale to 540p
            print("    ⚙ Downscaling to 540p...", end='', flush=True)
            t0 = time.time()
            if downscale_to_540p(out_720_local, out_540_local):
                print(f" ✓ {out_540_local.stat().st_size / 1024 / 1024:.1f}MB (took {time.time()-t0:.1f}s)")
            else:
                print(" ✗ Downscale failed")
                continue

            # D. Upload to R2
            print("    ⬆ Uploading videos to R2...", end='', flush=True)
            key_720 = f"dramas/{SLUG}/ep{ep_no:03d}_720p.mp4"
            key_540 = f"dramas/{SLUG}/ep{ep_no:03d}_540p.mp4"
            r2_url_720 = r2_upload_file(r2, out_720_local, key_720)
            r2_url_540 = r2_upload_file(r2, out_540_local, key_540)
            print(" ✓ Done")

            # E. Upload Subtitle to R2
            r2_sub_url = None
            if sub_url:
                print("    ⬆ Uploading subtitle to R2...", end='', flush=True)
                try:
                    sub_r = requests.get(sub_url, headers=HEADERS, timeout=15, verify=False)
                    if sub_r.ok:
                        sub_key = f"dramas/{SLUG}/ep{ep_no:03d}_id.vtt"
                        r2.put_object(Bucket=R2_BUCKET, Key=sub_key, Body=sub_r.content, ContentType='text/vtt')
                        r2_sub_url = f"{R2_PUBLIC}/{sub_key}"
                        print(" ✓ Done")
                    else:
                        print(f" ✗ Download failed (HTTP {sub_r.status_code})")
                except Exception as e:
                    print(f" ✗ Error: {e}")

            # F. Register in Database
            ep_db_id = register_episode_db(drama_db_id, ep_no, r2_url_720, r2_url_540)
            if ep_db_id:
                print(f"    ✓ EP {ep_no} registered in DB.")
                if r2_sub_url:
                    sub_reg = register_subtitles_db(ep_db_id, r2_sub_url)
                    if sub_reg:
                        print("    ✓ Subtitle registered in DB.")
                    else:
                        print("    ✗ Failed to register subtitle in DB.")
                processed += 1
            else:
                print(f"    ✗ Failed to register EP {ep_no} in DB.")

        except Exception as e:
            print(f"    ✗ Error: {e}")
        finally:
            # Cleanup temp files
            for p in [out_720_local, out_540_local]:
                if p.exists():
                    try:
                        p.unlink()
                    except: pass

        time.sleep(1.0)

    print("\n" + "=" * 60)
    print(f"PIPELINE COMPLETED! Processed {processed} new episodes.")
    print("=" * 60)

if __name__ == '__main__':
    main()
