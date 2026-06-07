#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
KingShort Vidrama Scraper for DramaWave Provider
================================================
Downloads dramas from DramaWave provider on vidrama.asia using Detail API,
transcodes each episode to 720p and 540p with faststart,
uploads to Cloudflare R2, and registers to database with status Pending.
"""
import requests
import boto3
import subprocess
import time
import tempfile
import urllib3
import re
import os
import sys
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
    'User-Agent': 'Mozilla/5.0 (Linux; Android 6.0; Nexus 5 Build/MRA58N) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/148.0.0.0 Mobile Safari/537.36',
    'Referer': 'https://vidrama.asia/watch/penyembuhnya-istrinya--ahTFgKtAU6/1?provider=dramawave&lang=id-ID',
    'Cookie': '_fbp=fb.1.1770653154777.876935444165455244; _tt_enable_cookie=1; _ttp=01KH1JE0K4H648BY6E3FQ6EXRZ_.tt.1; _ga=GA1.1.1826262121.1771037718; HstCfa5004644=1772873251576; c_ref_5004644=https%3A%2F%2Fwww.google.com%2F; __dtsu=4C301774685394D291D3AB624E4AA57E; _pubcid=8a5abbf9-164b-422f-b349-0e1ba702ea69; _cc_id=a4a99f9a552125d19ea447bfafb9c63b; global_ui_lang=id; HstCmu5004644=1779384259258; vidrama_chat_anon=45cc06417e3a261dc8f368a8; cf_clearance=J8QFuJs0er_WIP38vGy8bjQfQaQL7sFTKyEKgGeK3VA-1780795517-1.2.1.1-Obw73xI.dqmiSQdVtDuHFyZsbOD__sHZFc41Z7WuSJ_1XtPMHcVP7WGAmZM8UgRkfx1RmvPS8Mw6RV1Mxfy8nk9u5mLxnsCPd5XkJDAuQt5e1ZGXCvwfimrkbxXEBc0HLaV.tjy8GFC4chNPLXWwIu4XnAHluPvijjp6AziSEihvKlcO8S0gch2..hjZ.VvlLPFiQbKEWQd199XmWcHUjSlN1UbWgD9KtCXDZbIrrDBBDMAs874kQ6SiYfvaMVnn6MnmPE8TK1BVmFSj7tZDw.BioSjkB.O90BCUGYiLXLNnyCCnQCK4EiOE3hE7YmiOB08mCTr7Kh7ZZrGjyJQQaA; HstCnv5004644=64; HstCns5004644=86; panoramaId_expiry=1780881920064; HstCla5004644=1780795871370; HstPn5004644=2; HstPt5004644=159; ttcsid=1780795518124::qxBtmNAk35AwC3LWSvED.147.1780796502041.0::1.983569.353633::983547.23.360.812::604689.184.0; ttcsid_D5SNQPRC77UDQTF8A5EG=1780795518124::Zbl64-bTTugcPcmu7xs9.128.1780796502041.1; _ga_HCQQPKGEVH=GS2.1.s1780795517$o130$g1$t1780796502$j60$l0$h0'
}

TEMP_DIR = Path(tempfile.gettempdir()) / 'dramawave_scraper'
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
    except Exception as e:
        print(f"Error checking duplicate for '{title}': {e}")
    return None

def slugify(text):
    text = text.lower()
    slug = re.sub(r'[\W_]+', '-', text).strip('-')
    return slug

def srt_to_vtt(srt_content):
    if srt_content.strip().startswith("WEBVTT"):
        return srt_content
        
    lines = srt_content.replace('\r\n', '\n').split('\n')
    vtt_lines = ["WEBVTT\n"]
    
    timestamp_re = re.compile(r'(\d{2}:\d{2}:\d{2}),(\d{3})\s*-->\s*(\d{2}:\d{2}:\d{2}),(\d{3})')
    
    for line in lines:
        match = timestamp_re.search(line)
        if match:
            new_line = timestamp_re.sub(r'\1.\2 --> \3.\4', line)
            vtt_lines.append(new_line)
        else:
            vtt_lines.append(line)
            
    return "\n".join(vtt_lines)

def sanitize_vtt(vtt_content):
    # Remove absolute font-size styling from ::cue styles
    sanitized = re.sub(r'font-size\s*:\s*\d+px\s*;?', '', vtt_content, flags=re.IGNORECASE)
    return sanitized

def api_get_or_create_drama(detail, slug, cover_url):
    title = detail.get('title') or detail.get('name') or 'Unknown Title'
    payload = {
        'title': title,
        'description': detail.get('description') or detail.get('introduction') or title,
        'cover': cover_url,
        'genres': detail.get('tags', ['Drama']) or ['Drama'],
        'totalEpisodes': detail.get('chapterCount', 0),
        'isComplete': True,
        'country': 'China', 
        'language': 'Indonesia',
        'status': 'completed',
        'isActive': False, # Pending!
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

def scrape_single_drama(r2, movie_id, is_test_run=False):
    # 1. Fetch details from API
    url = f"https://vidrama.asia/api/dramawave?action=detail&id={movie_id}"
    print(f"Fetching details from API: {url}")
    try:
        r = requests.get(url, headers=WEB_HDRS, timeout=15, verify=False)
        if not r.ok:
            print(f"[ERROR] Failed to fetch drama details. Status: {r.status_code}")
            return False
        res_json = r.json()
        if not res_json.get('success'):
            print(f"[ERROR] API returned success=false: {res_json}")
            return False
        detail = res_json.get('data', {})
    except Exception as e:
        print(f"[ERROR] Exception fetching drama details: {e}")
        return False
        
    title = detail.get('title') or detail.get('name') or 'Unknown Title'
    slug = slugify(title)
    prefix = f"dramawave/{slug}"
    
    print(f"\nProcessing drama: '{title}' (ID: {movie_id}, Slug: {slug})")
    
    db_id = None
    newly_created = False
    
    try:
        # Check duplicate in database
        db_id = check_duplicate_in_db(title)
        if db_id:
            print(f"  -> Title already exists in database (ID: {db_id}). Skipping creation.")
        else:
            # Create cover WebP URL
            cover_key = f"{prefix}/cover.webp"
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
                    cover_src = detail.get('cover') or detail.get('image')
                    if cover_src:
                        cov_res = requests.get(cover_src, timeout=30, verify=False)
                        if cov_res.ok:
                            p = TEMP_DIR / f"{slug}_cover.jpg"
                            p.write_bytes(cov_res.content)
                            
                            # Convert to webp using ffmpeg
                            p_webp = TEMP_DIR / f"{slug}_cover.webp"
                            cmd = ['ffmpeg', '-y', '-i', str(p), '-loglevel', 'error', str(p_webp)]
                            if subprocess.run(cmd).returncode == 0:
                                r2_upload(r2, p_webp, cover_key, 'image/webp')
                                print("  -> [R2] Cover uploaded successfully")
                                p_webp.unlink()
                            else:
                                # Fallback direct upload if webp conversion fails
                                r2_upload(r2, p, cover_key, 'image/jpeg')
                                print("  -> [R2] Cover uploaded successfully (fallback jpeg)")
                            p.unlink()
                except Exception as e:
                    print(f"  -> [WARN] Failed to upload cover to R2: {e}")
                    
        # Process episodes
        eps = detail.get('list', [])
        if not eps:
            print("  -> [WARN] No episodes found in detail list.")
            if newly_created and db_id:
                print(f"  -> [DB] Cleaning up empty drama (ID: {db_id})...")
                requests.delete(f"{API_BASE}/dramas/{db_id}", headers=ADMIN_HDR, timeout=20)
            return False
            
        if is_test_run:
            print("  -> TEST RUN: Processing Episode 1 only.")
            eps = eps[:1]
            
        total_eps = len(eps)
        print(f"  -> Total Episodes to process: {total_eps}")
        
        success_count = 0
        failed_count = 0
        skipped_count = 0
        
        for ep in eps:
            ep_no = ep.get('episodeNo')
            if ep_no is None:
                continue
                
            k720 = f"{prefix}/ep{ep_no:03d}.mp4"
            k540 = f"{prefix}/ep{ep_no:03d}_540p.mp4"
            ksub = f"{prefix}/ep{ep_no:03d}.vtt"
            
            # If both 720p and 540p exist in R2, skip download/transcode
            if r2_exists(r2, k720) and r2_exists(r2, k540):
                print(f"    ep{ep_no:03d}: already exists in R2. Linking to DB...", end="", flush=True)
                u720 = f"{R2_PUBLIC}/{k720}"
                u540 = f"{R2_PUBLIC}/{k540}"
                
                # Check, sanitize and re-upload subtitle anyway to ensure font size is fixed!
                sub_url = None
                subtitles = ep.get('subtitles', [])
                id_sub_url = None
                id_sub_is_vtt = False
                for s in subtitles:
                    lang = s.get('language', '').lower()
                    if lang in ['id-id', 'id_id']:
                        if s.get('vtt'):
                            id_sub_url = s.get('vtt')
                            id_sub_is_vtt = True
                        else:
                            id_sub_url = s.get('subtitle')
                            id_sub_is_vtt = False
                        break
                if id_sub_url:
                    try:
                        sub_res = requests.get(id_sub_url, headers={'Referer': 'https://mydramawave.com/'}, timeout=10)
                        if sub_res.ok:
                            content = sub_res.content.decode('utf-8', errors='ignore')
                            if not id_sub_is_vtt:
                                content = srt_to_vtt(content)
                            content = sanitize_vtt(content)
                            r2.put_object(Bucket=R2_BUCKET, Key=ksub, Body=content.encode('utf-8'), ContentType='text/vtt')
                            sub_url = f"{R2_PUBLIC}/{ksub}"
                    except Exception as e:
                        pass
                if not sub_url and r2_exists(r2, ksub):
                    sub_url = f"{R2_PUBLIC}/{ksub}"
                    
                api_upsert_episode(db_id, ep_no, u720, u540, sub_url)
                print(" LINKED")
                success_count += 1
                continue
                
            print(f"    ep{ep_no:03d}: processing... ", end="", flush=True)
            
            # Extract video URL
            vurl = ep.get('videoPath')
            if not vurl:
                print("SKIPPED (No video path)")
                skipped_count += 1
                continue
                
            # Extract Indonesian subtitle (.vtt or .srt)
            subtitles = ep.get('subtitles', [])
            id_sub_url = None
            id_sub_is_vtt = False
            
            # Search for id-ID or id_ID subtitle
            for s in subtitles:
                lang = s.get('language', '').lower()
                if lang in ['id-id', 'id_id']:
                    # Prefer vtt URL if available
                    if s.get('vtt'):
                        id_sub_url = s.get('vtt')
                        id_sub_is_vtt = True
                    else:
                        id_sub_url = s.get('subtitle')
                        id_sub_is_vtt = False
                    break
                    
            # Download and upload subtitle if exists
            final_sub_r2 = None
            if id_sub_url:
                try:
                    # Subtitles can be fetched directly using Referer header
                    sub_res = requests.get(id_sub_url, headers={'Referer': 'https://mydramawave.com/'}, timeout=10)
                    if sub_res.ok:
                        content = sub_res.content.decode('utf-8', errors='ignore')
                        if not id_sub_is_vtt:
                            content = srt_to_vtt(content)
                        content = sanitize_vtt(content)
                        r2.put_object(Bucket=R2_BUCKET, Key=ksub, Body=content.encode('utf-8'), ContentType='text/vtt')
                        final_sub_r2 = f"{R2_PUBLIC}/{ksub}"
                except Exception as e:
                    print(f"(Subtitle error: {e}) ", end="")
                    
            # Download video files
            raw_path = TEMP_DIR / f"{slug}_raw_{ep_no}.mp4"
            o720_path = TEMP_DIR / f"{slug}_720_{ep_no}.mp4"
            o540_path = TEMP_DIR / f"{slug}_540_{ep_no}.mp4"
            
            download_success = False
            headers_str = "Referer: https://mydramawave.com/\r\n"
            cmd = [
                'ffmpeg', '-y',
                '-headers', headers_str,
                '-i', vurl,
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
                    api_upsert_episode(db_id, ep_no, u720, u540, final_sub_r2)
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
    
    movie_id = "ahTFgKtAU6"
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
