#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
KingShort Vidrama Scraper for ReelShort Provider - Queue Processor
===================================================================
Reads scripts/reelshort_queue.json, processes the next pending drama,
transcodes episodes to 720p/540p faststart, uploads to R2, links to DB (Pending),
and updates the queue status.
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

WEB_HDRS    = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36',
    'Referer': 'https://vidrama.asia/',
}

QUEUE_PATH = Path(__file__).parent / 'reelshort_queue.json'
TEMP_DIR = Path(tempfile.gettempdir()) / 'reelshort_queue_scraper'
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
    return re.sub(r'[\W_]+', '-', text).strip('-')

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

def api_get_or_create_drama(detail, slug, cover_url):
    title = detail.get('title') or 'Unknown Title'
    title = title.replace("(Sulih Suara)", "[Versi Dub]")
    title = title.replace("[Dubbing]", "[Versi Dub]")
    title = title.replace("[Dijuluki]", "[Versi Dub]")
    payload = {
        'title': title,
        'description': detail.get('desc') or detail.get('description') or title,
        'cover': cover_url,
        'genres': detail.get('tags') or detail.get('theme') or ['Drama'],
        'totalEpisodes': detail.get('chapters') or 70,
        'isComplete': detail.get('isCompleted') == 1 or True,
        'country': 'China', 
        'language': 'Indonesia',
        'status': 'completed',
        'provider': 'reelshort',
        'isActive': False, # Pending!
    }
    try:
        r = requests.post(f"{API_BASE}/admin/dramas", headers=ADMIN_HDR, json=payload, timeout=20)
        if r.ok:
            return r.json().get('id')
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
        '-c:v', 'libx264', '-crf', '26', '-preset', 'fast', '-maxrate', '1500k', '-bufsize', '3000k',
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

def scrape_drama(r2, vid_id, test_mode=False):
    # Fetch Metadata Details
    url = f"https://vidrama.asia/api/reelshort/detail?id={vid_id}"
    try:
        r = requests.get(url, headers=WEB_HDRS, timeout=20, verify=False)
        if not r.ok:
            print(f"[ERROR] Failed to fetch metadata. HTTP: {r.status_code}")
            return False
        data = r.json()
        if not data.get('success'):
            print(f"[ERROR] API returned success=False")
            return False
        detail = data.get('detail', {})
        chapters = data.get('chapters', [])
    except Exception as e:
        print(f"[ERROR] Exception fetching metadata: {e}")
        return False

    title = detail.get('title', 'Unknown Title')
    title = title.replace("(Sulih Suara)", "[Versi Dub]")
    title = title.replace("[Dubbing]", "[Versi Dub]")
    title = title.replace("[Dijuluki]", "[Versi Dub]")
    slug = slugify(title)
    prefix = f"netshortv2/{slug}"
    
    print(f"\nProcessing drama: '{title}' (ID: {vid_id}, Slug: {slug})")
    
    db_id = check_duplicate_in_db(title)
    newly_created = False
    
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
                cover_src = detail.get('cover') or detail.get('pic')
                if cover_src:
                    cov_res = requests.get(cover_src, headers=WEB_HDRS, timeout=30, verify=False)
                    if cov_res.ok:
                        p = TEMP_DIR / f"{slug}_cover.webp"
                        p.write_bytes(cov_res.content)
                        r2_upload(r2, p, cover_key, 'image/webp')
                        p.unlink()
                        print("  -> [R2] Cover uploaded successfully")
            except Exception as e:
                print(f"  -> [WARN] Failed to upload cover to R2: {e}")

    # Process chapters
    total_eps = len(chapters)
    print(f"  -> Total Episodes to process: {total_eps}")
    if test_mode:
        print("  -> [TEST MODE] Only processing Episode 1")
        chapters = chapters[:1]

    success_count = 0
    failed_count = 0
    skipped_count = 0

    for ch in chapters:
        ep_no = ch.get('index')
        if ep_no is None:
            continue
            
        k720 = f"{prefix}/ep{ep_no:03d}.mp4"
        k540 = f"{prefix}/ep{ep_no:03d}_540p.mp4"
        ksub = f"{prefix}/ep{ep_no:03d}.vtt"
        
        # If both exist in R2, link to DB and skip
        if r2_exists(r2, k720) and r2_exists(r2, k540):
            print(f"    ep{ep_no:03d}: already exists in R2. Linking to DB...", end="", flush=True)
            u720 = f"{R2_PUBLIC}/{k720}"
            u540 = f"{R2_PUBLIC}/{k540}"
            sub_url = f"{R2_PUBLIC}/{ksub}" if r2_exists(r2, ksub) else None
            api_upsert_episode(db_id, ep_no, u720, u540, sub_url)
            print(" LINKED")
            success_count += 1
            continue
            
        print(f"    ep{ep_no:03d}: processing... ", end="", flush=True)
        
        # Get Video Details (sequentially try lang=id, no lang, and lang=in as fallbacks, with retries)
        vurl = None
        subtitles = []
        max_retries = 3
        for lang_param in ['&lang=id', '', '&lang=in']:
            if vurl:
                break
            for attempt in range(max_retries):
                ep_url = f"https://vidrama.asia/api/reelshort/video?bookId={vid_id}&episode={ep_no}{lang_param}"
                try:
                    er = requests.get(ep_url, headers=WEB_HDRS, timeout=15, verify=False)
                    if er.ok:
                        ep_data = er.json()
                        if ep_data.get('success') and (ep_data.get('rawVideoUrl') or ep_data.get('videoUrl')):
                            vurl = ep_data.get('rawVideoUrl') or ep_data.get('videoUrl')
                            subtitles = ep_data.get('subtitles', [])
                            break
                    time.sleep(2)
                except Exception:
                    time.sleep(2)

        if not vurl:
            print("ERROR (API Failed / No Stream URL)")
            failed_count += 1
            continue
            
        # Parse subtitles if separate
        id_sub_url = None
        for s in subtitles:
            lang = s.get('lang', s.get('language', '')).lower()
            if lang in ['id', 'id_id', 'in', 'in_id', 'indonesia']:
                id_sub_url = s.get('url')
                break
                
        # Download subtitle if separate
        final_sub_r2 = None
        if id_sub_url:
            try:
                sub_res = requests.get(id_sub_url, timeout=10, verify=False)
                if sub_res.ok:
                    content = sub_res.content.decode('utf-8', errors='ignore')
                    vtt_content = srt_to_vtt(content)
                    r2.put_object(Bucket=R2_BUCKET, Key=ksub, Body=vtt_content.encode('utf-8'), ContentType='text/vtt')
                    final_sub_r2 = f"{R2_PUBLIC}/{ksub}"
            except:
                pass

        # If it is absolute proxy path, format it
        if vurl.startswith('/api/'):
            vurl = f"https://vidrama.asia{vurl}"

        raw_path = TEMP_DIR / f"{slug}_raw_{ep_no}.mp4"
        o720_path = TEMP_DIR / f"{slug}_720_{ep_no}.mp4"
        o540_path = TEMP_DIR / f"{slug}_540_{ep_no}.mp4"
        
        headers_str = f"Referer: https://vidrama.asia/\r\nUser-Agent: {WEB_HDRS['User-Agent']}\r\n"
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
                # Transcode & Upload
                if encode_720_and_540(raw_path, o720_path, o540_path):
                    u720 = r2_upload(r2, o720_path, k720)
                    u540 = r2_upload(r2, o540_path, k540)
                    api_upsert_episode(db_id, ep_no, u720, u540, final_sub_r2)
                    print("SUCCESS")
                    success_count += 1
                else:
                    print("ERROR (Transcode failed)")
                    failed_count += 1
            else:
                print("ERROR (Download failed)")
                failed_count += 1
        except Exception as e:
            print(f"ERROR ({e})")
            failed_count += 1
        finally:
            for p in [raw_path, o720_path, o540_path]:
                if p.exists():
                    p.unlink()

        time.sleep(1)

    print(f"  -> Scrape results for '{title}': {success_count} success, {failed_count} failed, {skipped_count} skipped.")
    
    # Deletion logic on failure (only if newly created and there were errors)
    if failed_count > 0 and newly_created:
        print(f"  -> [DB] Cleaning up incomplete drama (ID: {db_id})...")
        requests.delete(f"{API_BASE}/dramas/{db_id}", headers=ADMIN_HDR, timeout=20)
        return False
        
    return failed_count == 0

# ── QUEUE MANAGEMENT ─────────────────────────────────────────────────────────
def load_queue():
    if not QUEUE_PATH.exists():
        return []
    try:
        with open(QUEUE_PATH, 'r', encoding='utf-8') as f:
            return json.load(f)
    except Exception as e:
        print(f"[ERROR] Failed to load queue: {e}")
        sys.exit(1)

def save_queue(queue):
    try:
        with open(QUEUE_PATH, 'w', encoding='utf-8') as f:
            json.dump(queue, f, indent=2, ensure_ascii=False)
    except Exception as e:
        print(f"[ERROR] Failed to save queue: {e}")

def main():
    test_mode = "--test" in sys.argv
    queue = load_queue()
    
    # Find pending drama
    pending_drama = None
    for item in queue:
        if item.get('status') == 'pending':
            pending_drama = item
            break
            
    if not pending_drama:
        print("=== NO PENDING DRAMAS FOUND IN QUEUE ===")
        return
        
    print(f"=== PROCESSING QUEUE ITEM ===")
    print(f"ID: {pending_drama['id']}")
    print(f"Title: {pending_drama['title']}")
    print(f"Status: {pending_drama['status']}")
    if test_mode:
        print("Running in TEST MODE (only Episode 1 will be processed).")
        
    r2 = get_r2()
    success = scrape_drama(r2, pending_drama['id'], test_mode=test_mode)
    
    # Reload queue to prevent overwriting modifications
    queue = load_queue()
    for item in queue:
        if item['id'] == pending_drama['id']:
            if success:
                item['status'] = 'completed'
            else:
                item['status'] = 'failed'
            item['processedAt'] = time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())
            break
            
    save_queue(queue)
    
    if success:
        print(f"\nSuccessfully processed and marked '{pending_drama['title']}' as completed.")
    else:
        print(f"\nFailed to process '{pending_drama['title']}'. Marked as failed.")
        sys.exit(1)

if __name__ == "__main__":
    main()
