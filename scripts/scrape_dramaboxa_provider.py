#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
KingShort Vidrama Scraper for Dramaboxa Provider
==================================================
Downloads dramas from dramaboxa provider on vidrama.asia,
transcodes each episode to 720p and 540p with faststart,
uploads to Cloudflare R2, and registers to database with status Pending.
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
import urllib.parse
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

TEMP_DIR = Path(tempfile.gettempdir()) / 'dramaboxa_scraper'
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
    title = detail.get('bookName') or 'Unknown Title'
    
    payload = {
        'title': title,
        'description': detail.get('introduction') or title,
        'cover': cover_url,
        'genres': ['Romance', 'Drama'], # Dramaboxa API doesn't provide explicit genres in bookInfo, setting defaults
        'totalEpisodes': detail.get('chapterCount', 0),
        'isComplete': True, # Dramaboxa API doesn't indicate completion status clearly, default true
        'country': 'China', 
        'language': 'Indonesia',
        'status': 'completed',
        'isActive': True,
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
        r = requests.post(f"{API_BASE}/admin/dramas/{drama_db_id}/episodes", headers=ADMIN_HDR, json=payload, timeout=20)
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

def scrape_single_drama(r2, movie_id, is_test_run=False):
    # 1. Fetch details from API
    url = f"https://vidrama.asia/api/dramaboxa/drama/{movie_id}?lang=en"
    print(f"Fetching details from API: {url}")
    try:
        r = requests.get(url, headers=WEB_HDRS, timeout=15, verify=False)
        if not r.ok:
            print(f"[ERROR] Failed to fetch drama details. Status: {r.status_code}")
            return False
        res_json = r.json()
        
        detail = res_json.get('data', {}).get('bookInfo')
        if not detail:
            print("[ERROR] No bookInfo found in API response.")
            return False
            
    except Exception as e:
        print(f"[ERROR] Exception fetching drama details: {e}")
        return False
        
    title = detail.get('bookName') or 'Unknown Title'
    slug = slugify(title)
    prefix = f"dramaboxa/{slug}"
    
    local_save_dir = Path("D:/Video Drama/Facebook") / title.replace(":", " ").replace("/", " ")
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
            print(f"  -> [DB] Created drama entry (ID: {db_id}, status: Pending)")
            
            # Upload Cover to R2
            if not r2_exists(r2, cover_key):
                try:
                    cover_src = detail.get('cover')
                    if cover_src:
                        cov_res = requests.get(cover_src, timeout=30, verify=False)
                        if cov_res.ok:
                            p = TEMP_DIR / f"{slug}_cover_raw.tmp"
                            p.write_bytes(cov_res.content)
                            
                            # Convert to jpeg using ffmpeg -update 1
                            p_jpg = TEMP_DIR / f"{slug}_cover_hq.jpg"
                            cmd = ['ffmpeg', '-y', '-i', str(p), '-update', '1', '-loglevel', 'error', str(p_jpg)]
                            if subprocess.run(cmd).returncode == 0:
                                r2_upload(r2, p_jpg, cover_key, 'image/jpeg')
                                print("  -> [R2] Cover uploaded successfully (JPEG Murni)")
                                p_jpg.unlink()
                            else:
                                # Fallback direct upload
                                r2_upload(r2, p, cover_key, 'image/jpeg')
                                print("  -> [R2] Cover uploaded successfully (fallback raw)")
                            p.unlink()
                except Exception as e:
                    print(f"  -> [WARN] Failed to upload cover to R2: {e}")
                    
        # Process episodes
        total_eps = detail.get('chapterCount', 0)
        if not total_eps:
            print("  -> [WARN] No episodes found in detail list.")
            if newly_created and db_id:
                print(f"  -> [DB] Cleaning up empty drama (ID: {db_id})...")
                requests.delete(f"{API_BASE}/dramas/{db_id}", headers=ADMIN_HDR, timeout=20)
            return False
            
        eps_to_process = list(range(1, total_eps + 1))
        
        if is_test_run:
            print("  -> TEST RUN: Processing Episode 1 only.")
            eps_to_process = [1]
            
        print(f"  -> Total Episodes to process: {total_eps}")
        
        success_count = 0
        failed_count = 0
        skipped_count = 0
        
        for ep_no in eps_to_process:
            ep_id = f"{movie_id}_{ep_no}" 
                
            k720 = f"{prefix}/ep{ep_no:03d}.mp4"
            k540 = f"{prefix}/ep{ep_no:03d}_540p.mp4"
            
            # If both 720p and 540p exist in R2, skip download/transcode
            if r2_exists(r2, k720) and r2_exists(r2, k540):
                print(f"    ep{ep_no:03d}: already exists in R2. Linking to DB...", end="", flush=True)
                u720 = f"{R2_PUBLIC}/{k720}"
                u540 = f"{R2_PUBLIC}/{k540}"
                    
                api_upsert_episode(db_id, ep_no, u720, u540)
                
                # Cek apakah file 720p sudah ada di lokal, jika belum, download dari R2
                local_file = local_save_dir / f"ep{ep_no:03d}.mp4"
                if not local_file.exists():
                    try:
                        print(f" [INFO] Mengunduh ulang ep{ep_no:03d} dari R2 ke lokal...", end="", flush=True)
                        r_dl = requests.get(u720, stream=True, timeout=60)
                        if r_dl.ok:
                            with open(local_file, 'wb') as f:
                                for chunk in r_dl.iter_content(chunk_size=1024*1024):
                                    if chunk: f.write(chunk)
                    except Exception as e:
                        print(f" [WARN] Gagal download ke lokal: {e}", end="")
                        
                print(" LINKED")
                success_count += 1
                continue
                
            print(f"    ep{ep_no:03d}: processing... ", end="", flush=True)
            
            # Direct Stream URL via Dramaboxa Watch API
            raw_vurl = f"https://vidrama.asia/api/dramaboxa/watch?bookId={movie_id}&episode={ep_no}&lang=en&mode=stream"
            
            # Download video files
            raw_path = TEMP_DIR / f"{slug}_raw_{ep_no}.mp4"
            o720_path = TEMP_DIR / f"{slug}_720_{ep_no}.mp4"
            o540_path = TEMP_DIR / f"{slug}_540_{ep_no}.mp4"
            
            download_success = False
            
            headers_str = f"User-Agent: Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36\r\nReferer: https://vidrama.asia/\r\n"
            cmd = [
                'ffmpeg', '-y',
                '-headers', headers_str,
                '-i', raw_vurl,
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
                if encode_720_and_540(raw_path, o720_path, o540_path):
                    u720 = r2_upload(r2, o720_path, k720)
                    u540 = r2_upload(r2, o540_path, k540)
                    api_upsert_episode(db_id, ep_no, u720, u540)
                    
                    try:
                        shutil.copy2(o720_path, local_save_dir / f"ep{ep_no:03d}.mp4")
                    except Exception as e:
                        print(f" [WARN] Gagal simpan lokal: {e}", end="")
                        
                    print("SUCCESS")
                    success_count += 1
                else:
                    print("ERROR (Transcode failed)")
                    failed_count += 1
            except Exception as e:
                print(f"ERROR ({e})")
                failed_count += 1
            finally:
                for p in [raw_path, o720_path, o540_path]:
                    if p.exists():
                        p.unlink()
                        
            time.sleep(2)
            
        print(f"  -> Scrape results for '{title}': {success_count} success, {failed_count} failed, {skipped_count} skipped.")
        
        # Deletion logic on failure (only if it was newly created and has failures)
        if failed_count > 0 and not is_test_run:
            print(f"  -> [ERROR] Drama '{title}' has {failed_count} failed episodes.")
            if newly_created and db_id:
                print(f"  -> [DB] Deleting incomplete newly created drama entry (ID: {db_id})...")
                r_del = requests.delete(f"{API_BASE}/dramas/{db_id}", headers=ADMIN_HDR, timeout=20)
                if r_del.ok:
                    print(f"  -> [DB] Deleted incomplete drama entry (ID: {db_id})")
                else:
                    print(f"  -> [DB] Failed to delete drama entry (Status: {r_del.status_code})")
            return False
            
        return True
        
    except (Exception, KeyboardInterrupt) as e:
        print(f"\n  -> [ERROR] Aborting/Error processing drama '{title}': {e}")
        if newly_created and db_id and not is_test_run:
            print(f"  -> [DB] Deleting incomplete newly created drama entry (ID: {db_id})...")
            r_del = requests.delete(f"{API_BASE}/dramas/{db_id}", headers=ADMIN_HDR, timeout=20)
            if r_del.ok:
                print(f"  -> [DB] Deleted incomplete drama entry (ID: {db_id})")
            else:
                print(f"  -> [DB] Failed to delete drama entry (Status: {r_del.status_code})")
        if isinstance(e, KeyboardInterrupt):
            print("  -> Interrupted by user. Exiting.")
            raise e
        return False

# ── MAIN ─────────────────────────────────────────────────────────────────────
def main():
    r2 = get_r2()
    
    movie_id = "42000019332"
    is_test_run = False
    
    if len(sys.argv) > 1:
        if sys.argv[1] == '--test':
            is_test_run = True
        else:
            movie_id = sys.argv[1]
            if len(sys.argv) > 2 and sys.argv[2] == '--test':
                is_test_run = True
                
    scrape_single_drama(r2, movie_id, is_test_run=is_test_run)

if __name__ == "__main__":
    main()
