# -*- coding: utf-8 -*-
"""
Scraper for "Singgasana Bayangan (Sulih Suara)"
Book ID: 41000106419
- Checks if drama already exists in DB to prevent duplicates.
- Generates R2 folder and registers empty genres [].
- Saves 720p faststart locally to the D: drive custom folder.
- Uploads both 720p and 540p faststart to R2 and registers to DB.
- Merges 720p files in groups of 3 to the gabungan subfolder.
"""
import requests
import boto3
import sys
import json
import time
import os
import io
import subprocess
import urllib3
from pathlib import Path
from botocore.config import Config

urllib3.disable_warnings()
sys.stdout.reconfigure(encoding='utf-8')

# ─── CONFIG ─────────────────────────────────────────────────────────────────
BOOK_ID = '41000106419'
BOOK_SLUG = 'singgasana-bayangan-sulih-suara'

API_BASE = 'https://api.shortlovers.id/api'
ADMIN_KEY = '00ca04e3e2702be565d7bf44e783255247708289bce9b2fb6187a2e117f87fd14'
ADMIN_HDR = {'x-admin-key': ADMIN_KEY, 'Content-Type': 'application/json'}

R2_ENDPOINT = 'https://a142d3b29a5d64943cb251157e25eaf3.r2.cloudflarestorage.com'
R2_KEY_ID = '07c99c897986ea52703c1285308d5e2c'
R2_SECRET = '44788d376ffb216e1e73784b6fe1ff1423607928898a87c50819b52cdfc12e44'
R2_BUCKET = 'shortlovers'
R2_PUBLIC = 'https://stream.shortlovers.id'

COOKIE = '_fbp=fb.1.1770653154777.876935444165455244; _tt_enable_cookie=1; _ttp=01KH1JE0K4H648BY6E3FQ6EXRZ_.tt.1; _ga=GA1.1.1826262121.1771037718; HstCfa5004644=1772873251576; c_ref_5004644=https%3A%2F%2Fwww.google.com%2F; __dtsu=4C301774685394D291D3AB624E4AA57E; _pubcid=8a5abbf9-164b-422f-b349-0e1ba702ea69; _cc_id=a4a99f9a552125d19ea447bfafb9c63b; global_ui_lang=id; HstCmu5004644=1779384259258; vidrama_chat_anon=45cc06417e3a261dc8f368a8; HstCnv5004644=48; cf_clearance=N5A.kyHMnJ7RBK3hOyqybB6KddOTpRsZyEiE.fgp5kM-1779713242-1.2.1.1-9YHMfsNOniF6J54T1_JEaJY6mYbVJWOz8Kkm0raJacrpotGOYzyN_gG.Kxb7kfPxOO1wYdSenqFW0HIUwqQ57F5gqyjRbwvS8_r8rLFxIbYHNWMAahrr.iKy0dsa1krg8mVhzXDilHK71X.Iszvd8uo_CwVzbHiVUurJ8eF1DyguF2fK1vFa68H3Z5HFzZhBvVaIle1tEW3443.tH9TYjQX.7HKB9SBI2ZHkNto2vDQ2F77XP3cLmCp7GPXINCG8mrZf6l5xsxuh_xyqNp1bIRyxkUhz9IooxQKp3yV9Crri9TFW9II5q0M50yOlhCROGsKwa0AkIkKtWi.pNc5ATg; HstCla5004644=1779713242621; HstPn5004644=2; HstPt5004644=93; HstCns5004644=54; panoramaId_expiry=1779799644224'

VIDRAMA_HDR = {
    'accept': '*/*',
    'accept-language': 'id-ID,id;q=0.9,en-US;q=0.8,en;q=0.7',
    'cookie': COOKIE,
    'priority': 'u=1, i',
    'referer': f'https://vidrama.asia/watch/singgasana-bayangan--{BOOK_ID}/1?provider=dramabox3&lang=in',
    'user-agent': 'Mozilla/5.0 (Linux; Android 6.0; Nexus 5 Build/MRA58N) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/148.0.0.0 Mobile Safari/537.36'
}

# Directories
WORKSPACE_DIR = Path(__file__).resolve().parent.parent
TEMP_DIR = WORKSPACE_DIR / 'temp_singgasana'
TEMP_DIR.mkdir(exist_ok=True)

# User defined local path
LOCAL_SAVE_DIR = Path(r"D:\video drama\upload facebook\2. singgasana-bayangan-sulih-suara")
LOCAL_SAVE_DIR.mkdir(parents=True, exist_ok=True)

LOCAL_MERGED_DIR = LOCAL_SAVE_DIR / "gabungan"
LOCAL_MERGED_DIR.mkdir(parents=True, exist_ok=True)

def get_r2():
    return boto3.client(
        's3', endpoint_url=R2_ENDPOINT,
        aws_access_key_id=R2_KEY_ID, aws_secret_access_key=R2_SECRET,
        config=Config(signature_version='s3v4'), region_name='auto'
    )

def get_drama_metadata():
    """Get drama details from vidrama API"""
    url = f'https://vidrama.asia/api/dramabox3/drama/{BOOK_ID}?lang=in'
    r = requests.get(url, headers=VIDRAMA_HDR, timeout=30, verify=False)
    if r.ok:
        return r.json().get('data', {})
    return {}

def get_episode_data(ep_no):
    """Get stream URLs + subtitles for an episode"""
    url = f'https://vidrama.asia/api/dramabox3/watch?bookId={BOOK_ID}&episode={ep_no}&lang=in'
    try:
        r = requests.get(url, headers=VIDRAMA_HDR, timeout=30, verify=False)
        if r.ok:
            data = r.json()
            if data.get('success'):
                urls = {}
                for q in data.get('availableQualities', []):
                    urls[q['label']] = q['url']
                subtitles = data.get('subtitles', [])
                return urls, subtitles
            else:
                print(f"      ⚠ API returned success=False: {data}")
        else:
            print(f"      ⚠ HTTP error {r.status_code}: {r.text[:200]}")
    except Exception as e:
        print(f"      ⚠ Request exception: {e}")
    return {}, []

def download_file(url, local_path):
    """Download file to local disk"""
    with requests.get(url, headers=VIDRAMA_HDR, stream=True, timeout=60, verify=False) as r:
        if r.status_code == 200:
            with open(local_path, 'wb') as f:
                for chunk in r.iter_content(chunk_size=2*1024*1024):
                    if chunk:
                        f.write(chunk)
            return True
    return False

def r2_upload_file(r2, local_path, key, content_type='video/mp4'):
    """Upload local file to R2"""
    r2.upload_file(str(local_path), R2_BUCKET, key, ExtraArgs={
        'ContentType': content_type,
        'CacheControl': 'public, max-age=31536000'
    })
    return f"{R2_PUBLIC}/{key}"

def encode_faststart_720p(input_path, output_path):
    """Encode video to 720p x264 with faststart flags"""
    cmd = [
        'ffmpeg', '-y', '-i', str(input_path),
        '-c:v', 'libx264', '-crf', '26',
        '-maxrate', '1500k', '-bufsize', '3000k',
        '-c:a', 'aac', '-b:a', '128k',
        '-movflags', '+faststart',
        '-loglevel', 'error',
        str(output_path)
    ]
    res = subprocess.run(cmd)
    return res.returncode == 0

def downscale_faststart_540p(input_path, output_path):
    """Downscale a faststart 720p video to 540p with faststart"""
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
    res = subprocess.run(cmd)
    return res.returncode == 0

def register_drama_api(meta, cover_r2_url):
    """Register drama in admin panel with empty genres []"""
    payload = {
        'title': meta.get('bookName', 'Singgasana Bayangan (Sulih Suara)').strip(),
        'description': meta.get('introduction', ''),
        'cover': cover_r2_url,
        'genres': [],  # Empty genres
        'totalEpisodes': meta.get('chapterCount', 0),
        'status': 'ongoing',
        'country': 'China',
        'language': 'Indonesia',
        'isActive': False,  # Pending
        'isVip': False,
    }
    r = requests.post(f"{API_BASE}/admin/dramas", headers=ADMIN_HDR, json=payload, timeout=30)
    if r.ok:
        res = r.json()
        return res.get('id')
    return None

def check_drama_duplicate(title):
    """Check if drama title already exists in the database and return ID"""
    try:
        url = f"{API_BASE}/dramas/search?q={requests.utils.quote(title)}"
        r = requests.get(url, timeout=15)
        if r.ok:
            data = r.json()
            dramas = data if isinstance(data, list) else data.get('dramas', [])
            for d in dramas:
                if d.get('title', '').lower().strip() == title.lower().strip():
                    return d.get('id')
    except Exception as e:
        print(f"  ⚠ Failed to check duplicates in DB: {e}")
    return None

def register_episode(drama_id, ep_no, url_720, url_540):
    """Register episode in admin panel"""
    payload = {
        'episodeNumber': ep_no,
        'title': f'Episode {ep_no}',
        'videoUrl': url_720,
        'videoUrl540p': url_540,
        'isVip': False,
        'coinPrice': 0,
        'isActive': True
    }
    r = requests.post(f"{API_BASE}/admin/dramas/{drama_id}/episodes", headers=ADMIN_HDR, json=payload, timeout=20)
    if r.ok:
        return r.json().get('id')
    return None

def register_subtitles(episode_id, subtitles_list, r2, ep_no):
    """Download, upload to R2 and register subtitles if any"""
    count = 0
    for sub in subtitles_list:
        lang = sub.get('language') or sub.get('lang', '')
        label = sub.get('label') or sub.get('languageDisplayName', lang)
        url = sub.get('url') or sub.get('src', '')
        is_default = sub.get('default', False)
        if not url or not lang:
            continue
        
        # Download subtitle
        sub_key = f"dramas/{BOOK_SLUG}/ep{ep_no:03d}_{lang}.vtt"
        try:
            sub_r = requests.get(url, timeout=15, verify=False)
            if sub_r.ok:
                r2.put_object(Bucket=R2_BUCKET, Key=sub_key, Body=sub_r.content, ContentType='text/vtt')
                final_sub_url = f"{R2_PUBLIC}/{sub_key}"
                
                # Register in database
                payload = {'language': lang, 'label': label, 'url': final_sub_url, 'isDefault': is_default}
                db_r = requests.post(f"{API_BASE}/episodes/{episode_id}/subtitles", headers=ADMIN_HDR, json=payload, timeout=15)
                if db_r.ok:
                    count += 1
        except Exception as e:
            print(f"      ⚠ Failed to process subtitle {lang}: {e}")
    return count

def get_registered_episodes(drama_id):
    """Fetch list of already registered episode numbers for this drama"""
    url = f"{API_BASE}/dramas/{drama_id}/episodes?includeInactive=true"
    r = requests.get(url, timeout=15)
    if r.ok:
        eps = r.json()
        ep_list = eps if isinstance(eps, list) else eps.get('episodes', eps.get('data', []))
        return {e.get('episodeNumber') for e in ep_list}
    return set()

def merge_episodes(output_dir, file_list, merged_filename):
    """Stitch list of local video files using ffmpeg concat demuxer"""
    print(f"\nStitching {len(file_list)} videos -> {merged_filename}...")
    
    # Create temporary list file
    list_path = TEMP_DIR / 'concat_list.txt'
    with open(list_path, 'w', encoding='utf-8') as f:
        for filepath in file_list:
            cleaned_path = str(filepath).replace('\\', '/')
            f.write(f"file '{cleaned_path}'\n")
            
    # Output path
    out_path = output_dir / merged_filename
    
    cmd = [
        'ffmpeg', '-y', '-f', 'concat', '-safe', '0',
        '-i', str(list_path),
        '-c', 'copy',
        str(out_path)
    ]
    res = subprocess.run(cmd)
    
    # Clean up list file
    if list_path.exists():
        list_path.unlink()
        
    if res.returncode == 0:
        print(f"  ✓ Merged successfully: {out_path} ({out_path.stat().st_size / 1024 / 1024:.1f}MB)")
        return True
    else:
        print(f"  ✗ Merge failed for {merged_filename}")
        return False

def main():
    print("=" * 60)
    print("SINGGASANA BAYANGAN FULL PIPELINE SCRAPER")
    print("=" * 60)
    
    r2 = get_r2()
    
    # 1. Fetch metadata
    print("Fetching drama metadata from Vidrama...")
    meta = get_drama_metadata()
    if not meta:
        print("Failed to fetch drama metadata. Exiting.")
        return
        
    title = meta.get('bookName', 'Singgasana Bayangan (Sulih Suara)').strip()
    total_eps = meta.get('chapterCount', 0)
    cover_raw = meta.get('bookCover')
    print(f"Title: {title}")
    print(f"Total Episodes: {total_eps}")
    print(f"Raw Cover: {cover_raw}")
    
    # Check duplicate in database first
    drama_db_id = check_drama_duplicate(title)
    
    if drama_db_id:
        print(f"✓ Drama already exists in database! DB ID: {drama_db_id}")
    else:
        # Upload cover to R2
        cover_r2_url = ''
        if cover_raw:
            print("Uploading cover to R2...")
            try:
                cov_r = requests.get(cover_raw, timeout=20, verify=False)
                if cov_r.ok:
                    cover_key = f"dramas/{BOOK_SLUG}/cover.jpg"
                    r2.put_object(Bucket=R2_BUCKET, Key=cover_key, Body=cov_r.content, ContentType='image/jpeg')
                    cover_r2_url = f"{R2_PUBLIC}/{cover_key}"
                    print(f"  ✓ Cover uploaded: {cover_r2_url}")
            except Exception as e:
                print(f"  ✗ Failed to upload cover: {e}")
                cover_r2_url = cover_raw # fallback
                
        # Register drama in database
        print("Registering drama in database...")
        drama_db_id = register_drama_api(meta, cover_r2_url)
        if not drama_db_id:
            print("Failed to register drama. Exiting.")
            return
        print(f"✓ Drama registered! DB ID: {drama_db_id}")
    
    # Get currently registered episodes to avoid re-uploading
    print("Fetching registered episodes from database...")
    registered_eps = get_registered_episodes(drama_db_id)
    print("Registered episode numbers:", sorted(list(registered_eps)))
    
    # Scrape and process all episodes
    success_count = len(registered_eps)
    
    for ep_no in range(1, total_eps + 1):
        print(f"\n📹 Episode {ep_no}/{total_eps}:")
        
        # Local final destination path for 720p
        local_720_dest = LOCAL_SAVE_DIR / f"ep{ep_no:03d}_720p.mp4"
        
        # If episode already registered in DB
        if ep_no in registered_eps:
            print("    Already registered in database.")
            if not local_720_dest.exists():
                r2_720_url = f"{R2_PUBLIC}/dramas/{BOOK_SLUG}/ep{ep_no:03d}_720p.mp4"
                print(f"    ⬇ Downloading 720p from R2 to local folder...", end='', flush=True)
                if download_file(r2_720_url, local_720_dest):
                    print(f" ✓ {local_720_dest.stat().st_size / 1024 / 1024:.1f}MB")
                else:
                    print(" ✗ Download from R2 failed")
            else:
                print("    ✓ Local 720p file already exists.")
            continue
        
        # Get stream urls
        stream_urls = {}
        subtitles_list = []
        for attempt in range(5):
            try:
                stream_urls, subtitles_list = get_episode_data(ep_no)
                if stream_urls:
                    break
            except Exception as e:
                print(f"    ⚠ Attempt {attempt+1} failed: {e}")
            if not stream_urls and attempt < 4:
                print(f"    Waiting 8 seconds before attempt {attempt+2}/5...")
                time.sleep(8)
                
        if not stream_urls:
            print(f"    ✗ No stream URLs found for EP {ep_no} after all retries, skipping")
            # Wait longer on final failure to clear rate limit
            time.sleep(15)
            continue
            
        raw_video_url = stream_urls.get('720p') or stream_urls.get('1080p') or stream_urls.get('540p')
        if not raw_video_url:
            print(f"    ✗ No appropriate qualities for EP {ep_no}")
            continue
            
        print(f"    Selected stream quality: {list(stream_urls.keys())}")
        
        # Local temp paths
        raw_local = TEMP_DIR / f"raw_ep{ep_no:03d}.mp4"
        out_720_local = TEMP_DIR / f"ep{ep_no:03d}_720p.mp4"
        out_540_local = TEMP_DIR / f"ep{ep_no:03d}_540p.mp4"
        
        try:
            # A. Download raw video
            print(f"    ⬇ Downloading raw stream...", end='', flush=True)
            dl_ok = False
            for dl_attempt in range(2):
                if download_file(raw_video_url, raw_local):
                    dl_ok = True
                    break
                time.sleep(2)
            if not dl_ok:
                print(" ✗ Download failed")
                continue
            print(f" ✓ {raw_local.stat().st_size / 1024 / 1024:.1f}MB")
            
            # B. Encode to 720p faststart
            print(f"    ⚙ Encoding 720p faststart...", end='', flush=True)
            t0 = time.time()
            if not encode_faststart_720p(raw_local, out_720_local):
                print(" ✗ Failed")
                continue
            print(f" ✓ {out_720_local.stat().st_size / 1024 / 1024:.1f}MB (took {time.time()-t0:.1f}s)")
            
            # C. Downscale to 540p faststart
            print(f"    ⚙ Downscaling to 540p faststart...", end='', flush=True)
            t0 = time.time()
            if not downscale_faststart_540p(out_720_local, out_540_local):
                print(" ✗ Failed")
                continue
            print(f" ✓ {out_540_local.stat().st_size / 1024 / 1024:.1f}MB (took {time.time()-t0:.1f}s)")
            
            # D. Upload to R2
            print("    ⬆ Uploading videos to R2...", end='', flush=True)
            key_720 = f"dramas/{BOOK_SLUG}/ep{ep_no:03d}_720p.mp4"
            key_540 = f"dramas/{BOOK_SLUG}/ep{ep_no:03d}_540p.mp4"
            
            r2_url_720 = r2_upload_file(r2, out_720_local, key_720)
            r2_url_540 = r2_upload_file(r2, out_540_local, key_540)
            print(" ✓ Done")
            
            # E. Register Episode in DB
            ep_id = register_episode(drama_db_id, ep_no, r2_url_720, r2_url_540)
            if ep_id:
                sub_count = register_subtitles(ep_id, subtitles_list, r2, ep_no)
                print(f"    ✓ EP {ep_no} registered | {sub_count} subtitle(s) registered")
                
                # F. Copy 720p local file to final folder (Permanent Local Save)
                import shutil
                shutil.copy(str(out_720_local), str(local_720_dest))
                print(f"    ✓ Local 720p file saved: {local_720_dest}")
                success_count += 1
            else:
                print(f"    ✗ EP {ep_no} failed to register in DB")
                
        except Exception as e:
            print(f"    ✗ Error processing EP {ep_no}: {e}")
        finally:
            # Cleanup local temp files
            for path in [raw_local, out_720_local, out_540_local]:
                if path.exists():
                    try:
                        path.unlink()
                    except: pass
                    
        time.sleep(2.0)

    # ─── CONCATENATION PROCESS ────────────────────────────────────────────────
    print("\n" + "=" * 60)
    print("ALL EPISODES PROCESSED. STARTING CONCATENATION LOOP PER 3 EPISODES...")
    print("=" * 60)
    
    # Loop over episodes in groups of 3
    concat_success = 0
    concat_fail = 0
    
    for start in range(1, total_eps + 1, 3):
        end = min(start + 2, total_eps)
        file_group = []
        all_exist = True
        
        # Build file list
        for ep in range(start, end + 1):
            filepath = LOCAL_SAVE_DIR / f"ep{ep:03d}_720p.mp4"
            if filepath.exists():
                file_group.append(filepath)
            else:
                all_exist = False
                print(f"  [WARN] File missing for ep{ep:03d}: {filepath}")
                
        if not all_exist or not file_group:
            print(f"Skipping merge {start}-{end} due to missing source files.")
            concat_fail += 1
            continue
            
        merged_filename = f"singgasana-bayangan-ep{start:02d}-ep{end:02d}.mp4"
        if merge_episodes(LOCAL_MERGED_DIR, file_group, merged_filename):
            concat_success += 1
        else:
            concat_fail += 1

    print("\n" + "=" * 60)
    print("PIPELINE COMPLETED!")
    print(f"Total Local 720p files: {success_count} / {total_eps}")
    print(f"Successfully Merged Packages (per 3 Eps): {concat_success}")
    if concat_fail > 0:
        print(f"Failed/Skipped Merges: {concat_fail}")
    print(f"All outputs saved to: {LOCAL_SAVE_DIR}")
    print("=" * 60)

if __name__ == '__main__':
    main()
