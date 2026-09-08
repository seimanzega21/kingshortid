#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
KingShort Vidrama Scraper for ShortMax Provider
================================================
Downloads dramas from shortmax provider on vidrama.asia,
transcodes each episode to 720p and 540p with faststart,
uploads to Cloudflare R2, saves to local backup (D:/Video Drama/Facebook),
and registers to database.
"""
import requests
import boto3
import shutil
import subprocess
import time
import tempfile
import urllib3
import re
import os
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

WEB_HDRS    = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36',
    'Referer': 'https://vidrama.asia/',
}

NEXT_ACTION_EPISODE = '7081ea77aada73681c85542d033db73abd6689d036'

TEMP_DIR = Path(tempfile.gettempdir()) / 'shortmax_scraper'
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
    r2.upload_file(str(local_path), R2_BUCKET, key, ExtraArgs={'ContentType': content_type},
                    Config=boto3.s3.transfer.TransferConfig(multipart_threshold=30*1024*1024, multipart_chunksize=10*1024*1024))
    return f"{R2_PUBLIC}/{key}"

def check_duplicate_in_db(title):
    try:
        r = requests.get(f"{API_BASE}/dramas/search?q={title}", timeout=10)
        dramas = r.json().get('dramas', [])
        for d in dramas:
            if d['title'].lower().strip() == title.lower().strip():
                return d['id']

        # Fallback to check inactive dramas
        r_all = requests.get(f"{API_BASE}/dramas?limit=1000&includeInactive=true", timeout=15)
        if r_all.ok:
            all_dramas = r_all.json()
            if isinstance(all_dramas, dict):
                all_dramas = all_dramas.get('dramas', [])
            for d in all_dramas:
                if d['title'].lower().strip() == title.lower().strip():
                    return d['id']
    except Exception as e:
        print(f"Error checking duplicate for '{title}': {e}")
    return None

def slugify(text):
    text = text.lower()
    slug = re.sub(r'[\W_]+', '-', text).strip('-')
    return slug

def api_get_or_create_drama(detail, slug, cover_url):
    title = detail.get('name') or detail.get('title') or 'Unknown Title'
    genres = ['Drama', 'Romance']
    total_eps = detail.get('episodes') or detail.get('chapterCount') or 0
    summary = detail.get('summary') or detail.get('description') or title

    payload = {
        'title': title,
        'description': summary,
        'cover': cover_url,
        'genres': genres,
        'totalEpisodes': total_eps,
        'isComplete': True,
        'country': 'China',
        'language': 'Indonesia',
        'status': 'completed',
        'isActive': False, # Pending! (Tayang manual lewat admin panel)
    }
    try:
        r = requests.post(f"{API_BASE}/admin/dramas", headers=ADMIN_HDR, json=payload, timeout=20)
        if r.ok:
            return r.json().get('id')
        else:
            print(f"      [ERROR] Failed to create drama in DB. Status: {r.status_code}, Body: {r.text}")
    except Exception as e:
        print(f"      [ERROR] Exception creating drama in DB: {e}")
    return None

def api_mark_active(drama_db_id):
    try:
        r = requests.patch(f"{API_BASE}/admin/dramas/{drama_db_id}",
                           headers=ADMIN_HDR, json={'isActive': True}, timeout=15)
        return r.ok
    except:
        return False

def api_upsert_episode(drama_db_id, ep_no, url_720, url_540=None, sub_url=None):
    payload = {
        'episodeNumber': ep_no,
        'title': f'Episode {ep_no}',
        'videoUrl': url_720,
        'isActive': True
    }
    if url_540:
        payload['videoUrl540p'] = url_540

    try:
        r = requests.post(f"{API_BASE}/admin/dramas/{drama_db_id}/episodes", headers=ADMIN_HDR, json=payload, timeout=20)
        if not r.ok:
            print(f"      [WARN] DB Episode upsert failed. Status: {r.status_code}")
            return None
        ep_id = r.json().get('id')
        if ep_id and sub_url:
            sub_payload = {
                'language': 'indonesia',
                'label': 'Indonesia',
                'url': sub_url,
                'isDefault': True
            }
            requests.post(f"{API_BASE}/episodes/{ep_id}/subtitles", headers=ADMIN_HDR, json=sub_payload, timeout=10)
        return ep_id
    except Exception as e:
        print(f"      [ERROR] DB Episode upsert exception: {e}")
    return None

def encode_720_and_540(inp, out_720, out_540):
    cmd_720 = [
        'ffmpeg', '-y', '-i', str(inp),
        '-c:v', 'libx264', '-crf', '26', '-maxrate', '1500k', '-bufsize', '3000k',
        '-c:a', 'aac', '-b:a', '128k', '-movflags', '+faststart',
        '-loglevel', 'error', str(out_720)
    ]
    res_720 = subprocess.run(cmd_720, timeout=600)
    if res_720.returncode != 0:
        return False

    cmd_540 = [
        'ffmpeg', '-y', '-i', str(out_720),
        '-vf', 'scale=-2:540',
        '-c:v', 'libx264', '-crf', '28', '-preset', 'fast',
        '-c:a', 'aac', '-b:a', '96k', '-movflags', '+faststart',
        '-loglevel', 'error', str(out_540)
    ]
    return subprocess.run(cmd_540, timeout=600).returncode == 0

def get_shortmax_episode_stream(movie_id, ep_no, slug_hint='cinta-di-antara-spesies'):
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36',
        'Referer': f'https://vidrama.asia/watch/{slug_hint}--{movie_id}/{ep_no}?provider=shortmax&lang=id',
        'Next-Action': NEXT_ACTION_EPISODE,
        'Content-Type': 'text/plain;charset=UTF-8',
        'Accept': 'text/x-component'
    }
    body = json.dumps([str(movie_id), int(ep_no), "id"])
    url = f'https://vidrama.asia/watch/{slug_hint}--{movie_id}/{ep_no}?provider=shortmax&lang=id'

    for attempt in range(3):
        try:
            r = requests.post(url, headers=headers, data=body, timeout=20, verify=False)
            if r.status_code == 200:
                lines = r.text.strip().split('\n')
                for line in lines:
                    if line.startswith('1:'):
                        data = json.loads(line[2:])
                        qualities = data.get('qualities', {})
                        # Choose best stream: 720 or 1080
                        m3u8_url = qualities.get('video_720') or qualities.get('video_1080') or qualities.get('video_480')
                        subs = data.get('subtitles') or []
                        return m3u8_url, subs
            time.sleep(2)
        except Exception as e:
            time.sleep(2)
    return None, []

def scrape_shortmax_drama(r2, movie_id, is_test_run=False):
    # 1. Fetch details from Shortmax API
    detail_url = f"https://vidrama.asia/api/shortmax/detail/{movie_id}"
    print(f"Fetching details from API: {detail_url}")
    try:
        r = requests.get(detail_url, headers=WEB_HDRS, timeout=15, verify=False)
        if not r.ok:
            print(f"[ERROR] Failed to fetch drama details. Status: {r.status_code}")
            return False
        res_json = r.json()
        detail = res_json.get('data', {})
    except Exception as e:
        print(f"[ERROR] Exception fetching drama details: {e}")
        return False

    title = detail.get('name') or detail.get('title') or 'Unknown Title'
    slug = slugify(title)
    prefix = f"shortmax/{slug}"

    safe_title = re.sub(r'[<>:"/\\|?*]', ' ', title).strip()
    local_save_dir = Path("D:/Video Drama/Facebook") / safe_title
    local_save_dir.mkdir(parents=True, exist_ok=True)

    print(f"\nProcessing drama: '{title}' (ID: {movie_id}, Slug: {slug})")

    db_id = None
    newly_created = False

    try:
        # Check duplicate in database
        db_id = check_duplicate_in_db(title)
        if db_id:
            print(f"  -> Title already exists in database (ID: {db_id}). Skipping creation.")
        else:
            # Create cover JPEG URL
            cover_key = f"{prefix}/cover_hq.jpg"
            r2_cover_url = f"{R2_PUBLIC}/{cover_key}"

            # Register in database
            db_id = api_get_or_create_drama(detail, slug, r2_cover_url)
            if not db_id:
                print("  -> [ERROR] Failed to register drama in DB.")
                return False
            newly_created = True
            print(f"  -> [DB] Created drama entry (ID: {db_id})")

            # Upload Cover to R2
            if not r2_exists(r2, cover_key):
                try:
                    cover_src = detail.get('cover')
                    if cover_src:
                        cov_res = requests.get(cover_src, timeout=30, verify=False)
                        if cov_res.ok:
                            p = TEMP_DIR / f"{slug}_cover_raw.tmp"
                            p.write_bytes(cov_res.content)

                            p_jpg = TEMP_DIR / f"{slug}_cover_hq.jpg"
                            cmd = ['ffmpeg', '-y', '-i', str(p), '-update', '1', '-loglevel', 'error', str(p_jpg)]
                            if subprocess.run(cmd).returncode == 0:
                                r2_upload(r2, p_jpg, cover_key, 'image/jpeg')
                                print("  -> [R2] Cover uploaded successfully (JPEG)")
                                p_jpg.unlink()
                            else:
                                r2_upload(r2, p, cover_key, 'image/jpeg')
                                print("  -> [R2] Cover uploaded successfully (raw fallback)")
                            p.unlink()
                except Exception as e:
                    print(f"  -> [WARN] Failed to upload cover to R2: {e}")

        total_eps = detail.get('episodes') or 15
        eps_to_process = list(range(1, total_eps + 1))

        if is_test_run:
            print("  -> TEST RUN: Processing Episode 1 only.")
            eps_to_process = [1]

        print(f"  -> Total Episodes to process: {len(eps_to_process)} / {total_eps}")

        success_count = 0
        failed_count = 0
        skipped_count = 0

        for ep_no in eps_to_process:
            k720 = f"{prefix}/ep{ep_no:03d}.mp4"
            k540 = f"{prefix}/ep{ep_no:03d}_540p.mp4"

            # If both 720p and 540p exist in R2, skip download/transcode
            if r2_exists(r2, k720) and r2_exists(r2, k540):
                print(f"    ep{ep_no:03d}: already exists in R2. Linking to DB...", end="", flush=True)
                u720 = f"{R2_PUBLIC}/{k720}"
                u540 = f"{R2_PUBLIC}/{k540}"
                api_upsert_episode(db_id, ep_no, u720, u540)

                local_file = local_save_dir / f"ep{ep_no:03d}.mp4"
                if not local_file.exists():
                    try:
                        print(f" [INFO] Downloading ep{ep_no:03d} to local backup...", end="", flush=True)
                        r_dl = requests.get(u720, stream=True, timeout=60)
                        if r_dl.ok:
                            with open(local_file, 'wb') as f:
                                for chunk in r_dl.iter_content(chunk_size=1024*1024):
                                    if chunk: f.write(chunk)
                    except Exception as e:
                        print(f" [WARN] Failed local save: {e}", end="")

                print(" LINKED")
                success_count += 1
                continue

            print(f"    ep{ep_no:03d}: resolving stream... ", end="", flush=True)
            m3u8_url, _ = get_shortmax_episode_stream(movie_id, ep_no, slug)

            if not m3u8_url:
                print("ERROR (Stream URL not found)")
                failed_count += 1
                continue

            raw_path = TEMP_DIR / f"{slug}_raw_{ep_no}.mp4"
            o720_path = TEMP_DIR / f"{slug}_720_{ep_no}.mp4"
            o540_path = TEMP_DIR / f"{slug}_540_{ep_no}.mp4"

            download_success = False
            headers_str = f"User-Agent: Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36\r\nReferer: https://vidrama.asia/\r\n"
            cmd = [
                'ffmpeg', '-y',
                '-headers', headers_str,
                '-i', m3u8_url,
                '-c', 'copy',
                '-loglevel', 'error',
                str(raw_path)
            ]
            try:
                res = subprocess.run(cmd, timeout=300)
                if res.returncode == 0 and raw_path.exists() and raw_path.stat().st_size > 50*1024:
                    download_success = True
            except Exception as e:
                pass

            if not download_success:
                print("ERROR (Download failed)")
                failed_count += 1
                if raw_path.exists():
                    raw_path.unlink()
                continue

            # Transcode & Upload
            try:
                print("encoding & uploading... ", end="", flush=True)
                if encode_720_and_540(raw_path, o720_path, o540_path):
                    u720 = r2_upload(r2, o720_path, k720)
                    u540 = r2_upload(r2, o540_path, k540)
                    api_upsert_episode(db_id, ep_no, u720, u540)

                    try:
                        shutil.copy2(o720_path, local_save_dir / f"ep{ep_no:03d}.mp4")
                    except Exception as e:
                        print(f" [WARN] Local save error: {e}", end="")

                    print("SUCCESS")
                    success_count += 1
                else:
                    print("ERROR (Encoding failed)")
                    failed_count += 1
            except Exception as e:
                print(f"ERROR (Upload/DB failed: {e})")
                failed_count += 1
            finally:
                for p in [raw_path, o720_path, o540_path]:
                    if p.exists():
                        try: p.unlink()
                        except: pass

        print(f"\nCompleted '{title}': Success={success_count}, Failed={failed_count}, Skipped={skipped_count}")
        # Note: Dibiarkan status Pending (isActive=False) sesuai permintaan user
        return success_count > 0
    except Exception as e:
        print(f"[FATAL] Error scraping drama: {e}")
        return False

if __name__ == '__main__':
    r2 = get_r2()
    targets = ['859525', '858108', '863857', '863622', '856528']

    if len(sys.argv) > 1:
        if sys.argv[1] == '--test':
            scrape_shortmax_drama(r2, targets[0], is_test_run=True)
            sys.exit(0)
        elif sys.argv[1] == '--all':
            pass
        else:
            targets = [sys.argv[1]]

    print(f"=== Memulai Batch Scraper ShortMax: {len(targets)} Drama ===")
    for idx, mid in enumerate(targets, 1):
        print(f"\n[{idx}/{len(targets)}] Scraping drama ID: {mid}...")
        scrape_shortmax_drama(r2, mid, is_test_run=False)
        time.sleep(3)
    print("\n=== SEMUA BATCH SELESAI ===")

