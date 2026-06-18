# -*- coding: utf-8 -*-
"""
Scraper & Ingester for "Mari Berkultivasi Sekeluarga"
Provider: dramaboxa
HLS Download -> FFmpeg Transcode (720p/540p faststart) -> Upload R2 -> Register Admin
With Auto-Resume support
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
from botocore.config import Config

urllib3.disable_warnings()
sys.stdout.reconfigure(encoding='utf-8')

# ─── CONFIG ─────────────────────────────────────────────────────────────────
BOOK_ID     = '42000014163'
BOOK_SLUG   = 'mari-berkultivasi-sekeluarga'
PROVIDER    = 'dramaboxa'

API_BASE    = 'https://api.shortlovers.id'
ADMIN_KEY   = '00ca04e3e2702be565d7bf44e783255247708289bce9b2fb6187a2e117f87fd14'
ADMIN_HDR   = {'x-admin-key': ADMIN_KEY, 'Content-Type': 'application/json'}

R2_ENDPOINT = 'https://a142d3b29a5d64943cb251157e25eaf3.r2.cloudflarestorage.com'
R2_KEY_ID   = '07c99c897986ea52703c1285308d5e2c'
R2_SECRET   = '44788d376ffb216e1e73784b6fe1ff1423607928898a87c50819b52cdfc12e44'
R2_BUCKET   = 'shortlovers'
R2_PUBLIC   = 'https://stream.shortlovers.id'

VIDRAMA_HDR = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36',
    'Referer': f'https://vidrama.asia/watch/mari-berkultivasi-sekeluarga--{BOOK_ID}/1?provider=dramaboxa&lang=in',
}

HEADERS_FFMPEG = (
    "User-Agent: Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36\r\n"
    "Referer: https://vidrama.asia/\r\n"
)

# Create a local temp directory for transcode files
TEMP_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'temp_transcode')
os.makedirs(TEMP_DIR, exist_ok=True)

# ─── HELPERS ─────────────────────────────────────────────────────────────────
def get_r2():
    return boto3.client(
        's3', endpoint_url=R2_ENDPOINT,
        aws_access_key_id=R2_KEY_ID, aws_secret_access_key=R2_SECRET,
        config=Config(signature_version='s3v4'), region_name='auto'
    )

def download_and_transcode_ffmpeg(m3u8_url, ep_no):
    """Download HLS stream and transcode to 720p and 540p MP4 with faststart (High Quality & Retries)"""
    local_720 = os.path.join(TEMP_DIR, f"ep{ep_no:03d}_720p.mp4")
    local_540 = os.path.join(TEMP_DIR, f"ep{ep_no:03d}_540p.mp4")
    
    # Remove existing temp files if any
    for f in [local_720, local_540]:
        if os.path.exists(f):
            os.remove(f)
            
    # Download 720p with up to 3 retries (stream copy to preserve exact source quality)
    success_720 = False
    for attempt in range(1, 4):
        print(f"      🎥 Stream copying HLS -> 720p MP4 (Attempt {attempt}/3)...")
        cmd720 = [
            'ffmpeg', '-y',
            '-headers', HEADERS_FFMPEG,
            '-i', m3u8_url,
            '-c', 'copy',
            '-movflags', '+faststart',
            '-loglevel', 'warning',
            local_720
        ]
        
        res720 = subprocess.run(cmd720, capture_output=True, text=True, errors='ignore')
        if res720.returncode == 0:
            success_720 = True
            break
        else:
            print(f"      ⚠ Attempt {attempt} failed: {res720.stderr.strip()[-300:]}")
            if attempt < 3:
                time.sleep(5)
                
    if not success_720:
        print(f"      ❌ FFmpeg 720p failed entirely.")
        return None, None
        
    # Transcode to 540p with up to 3 retries
    success_540 = False
    for attempt in range(1, 4):
        print(f"      🎥 Transcoding 720p -> 540p MP4 (Attempt {attempt}/3)...")
        cmd540 = [
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
        
        res540 = subprocess.run(cmd540, capture_output=True, text=True, errors='ignore')
        if res540.returncode == 0:
            success_540 = True
            break
        else:
            print(f"      ⚠ Attempt {attempt} failed: {res540.stderr.strip()[-300:]}")
            if attempt < 3:
                time.sleep(5)
                
    if not success_540:
        print(f"      ❌ FFmpeg 540p failed, using only 720p.")
        return local_720, None
        
    return local_720, local_540

def upload_file_to_r2(r2, local_path, r2_key, content_type='video/mp4'):
    """Upload local file to Cloudflare R2"""
    print(f"      ⬆ Uploading to R2: {r2_key}...", end='', flush=True)
    try:
        size_mb = os.path.getsize(local_path) / (1024*1024)
        with open(local_path, 'rb') as f:
            r2.upload_fileobj(f, R2_BUCKET, r2_key,
                              ExtraArgs={'ContentType': content_type, 'CacheControl': 'public, max-age=31536000'})
        print(f" ✓ {size_mb:.1f}MB")
        return f"{R2_PUBLIC}/{r2_key}"
    except Exception as e:
        print(f" ✗ Error: {e}")
        return None

def upload_cover_to_r2(r2, cover_url):
    """Download and upload cover image to R2"""
    clean_cover_url = cover_url.split('@')[0]
    print(f"  🖼 Cover URL: {clean_cover_url}")
    try:
        r = requests.get(clean_cover_url, timeout=30, verify=False)
        if not r.ok:
            r = requests.get(cover_url, timeout=30, verify=False)
            
        if r.ok:
            key = f"dramas/{BOOK_SLUG}/cover.jpg"
            r2.upload_fileobj(io.BytesIO(r.content) if hasattr(r, 'content') else io.BytesIO(r.read()), R2_BUCKET, key,
                              ExtraArgs={'ContentType': 'image/jpeg', 'CacheControl': 'public, max-age=31536000'})
            url = f"{R2_PUBLIC}/{key}"
            print(f"  ✓ Cover uploaded to R2: {url}")
            return url
    except Exception as e:
        print(f"  ⚠ Failed to upload cover: {e}")
    return cover_url  # fallback to original URL

def get_drama_metadata():
    """Get drama details from vidrama API"""
    for attempt in range(1, 6):
        try:
            r = requests.get(
                f'https://vidrama.asia/api/{PROVIDER}/drama/{BOOK_ID}?lang=in',
                headers=VIDRAMA_HDR, timeout=30, verify=False
            )
            if r.ok:
                d = r.json().get('data', {})
                return d
            else:
                print(f"  ⚠ Metadata fetch HTTP {r.status_code} (attempt {attempt}/5)")
        except Exception as e:
            print(f"  ⚠ Metadata fetch error (attempt {attempt}/5): {e}")
        time.sleep(5)
    return {}

def get_episode_stream_url(ep_no):
    """Get watch stream endpoint for an episode (with retries)"""
    for attempt in range(1, 6):
        try:
            r = requests.get(
                f'https://vidrama.asia/api/{PROVIDER}/watch?bookId={BOOK_ID}&episode={ep_no}&lang=in',
                headers=VIDRAMA_HDR, timeout=30, verify=False
            )
            if r.ok:
                data = r.json()
                if data.get('success'):
                    rel_url = data.get('videoUrl')
                    if rel_url:
                        return f"https://vidrama.asia{rel_url}"
                else:
                    print(f"   ⚠ Watch API returned success=False (attempt {attempt}/5): {data.get('error')}")
            else:
                print(f"   ⚠ Watch API HTTP {r.status_code} (attempt {attempt}/5)")
        except Exception as e:
            print(f"   ⚠ Watch API error (attempt {attempt}/5): {e}")
        time.sleep(5)
    return None

def register_drama_in_admin(metadata, cover_r2_url):
    """Create drama entry in KingShort admin panel with status pending"""
    book_info = metadata.get('bookInfo', {})
    
    genres = ['Drama'] # Default
    
    payload = {
        'title': "Mari Berkultivasi Sekeluarga",
        'description': book_info.get('introduction', ''),
        'cover': cover_r2_url,
        'genres': genres,
        'totalEpisodes': book_info.get('chapterCount', 60),
        'status': 'completed',
        'country': 'Indonesia',
        'language': 'Indonesia',
        'isActive': False,  # pending = not active yet
        'isVip': False,
    }
    
    print(f"\n📋 Registering drama in admin panel...")
    print(f"   Title: {payload['title']}")
    print(f"   Total Episodes: {payload['totalEpisodes']}")
    
    r = requests.post(f"{API_BASE}/api/admin/dramas", headers=ADMIN_HDR, json=payload, timeout=30)
    if r.ok:
        resp = r.json()
        drama_id = resp.get('id') or resp.get('drama', {}).get('id')
        print(f"   ✓ Drama registered! ID: {drama_id}")
        return drama_id
    else:
        print(f"   ✗ Failed: {r.status_code} {r.text[:200]}")
        return None

def register_episode(drama_id, ep_no, video_url_720, video_url_540):
    """Register episode in admin panel, returns episode ID if successful"""
    # Use current time as a dynamic cache buster to force CDN/browser to fetch the latest file
    t_buster = int(time.time())
    v_url_720 = f"{video_url_720}?v={t_buster}" if video_url_720 else ""
    v_url_540 = f"{video_url_540}?v={t_buster}" if video_url_540 else ""
    
    payload = {
        'episodeNumber': ep_no,
        'title': f'Episode {ep_no}',
        'videoUrl': v_url_720 or v_url_540 or '',
        'videoUrl540p': v_url_540 or '',
        'isVip': False,
        'coinPrice': 0,
        'isActive': True,
    }
    r = requests.post(
        f"{API_BASE}/api/admin/dramas/{drama_id}/episodes",
        headers=ADMIN_HDR, json=payload, timeout=20
    )
    if r.ok:
        resp = r.json()
        return resp.get('id')
    return None

# ─── MAIN ────────────────────────────────────────────────────────────────────
def main():
    print("=" * 60)
    print(f"SCRAPER & INGESTER: Mari Berkultivasi Sekeluarga")
    print(f"Book ID: {BOOK_ID} | Provider: {PROVIDER}")
    print("=" * 60)
    
    r2 = get_r2()
    
    # 1. Fetch metadata
    print("\n🔍 Fetching drama metadata...")
    metadata = get_drama_metadata()
    book_info = metadata.get('bookInfo', {})
    if not book_info:
        print("❌ Failed to fetch metadata! Exiting.")
        return
        
    total_episodes = book_info.get('chapterCount', 60)
    cover_url = book_info.get('cover', '')
    print(f"   Title: {book_info.get('bookName')}")
    print(f"   Total Episodes: {total_episodes}")
    
    # 2. Check if drama already exists
    drama_id = None
    print("\n🔍 Checking if drama already exists in KingShort DB...")
    r = requests.get(f"{API_BASE}/api/dramas", params={"search": "Mari Berkultivasi Sekeluarga"}, timeout=15)
    if r.ok:
        dramas_list = r.json()
        dramas = dramas_list if isinstance(dramas_list, list) else dramas_list.get('dramas', [])
        for d in dramas:
            if d.get('title') == "Mari Berkultivasi Sekeluarga":
                drama_id = d.get('id')
                print(f"   ✓ Found existing drama! ID: {drama_id}")
                break
                
    # 3. If not found, upload cover & register drama
    if not drama_id:
        print("\n🖼 Uploading cover to R2...")
        cover_r2_url = upload_cover_to_r2(r2, cover_url)
        drama_id = register_drama_in_admin(metadata, cover_r2_url)
        if not drama_id:
            print("❌ Failed to register drama in admin panel! Exiting.")
            return
            
    # 4. Fetch list of already registered episodes
    existing_episodes = set()
    print("\n🔍 Fetching list of already registered episodes...")
    er = requests.get(f"{API_BASE}/api/dramas/{drama_id}/episodes", timeout=15)
    if er.ok:
        ep_list = er.json()
        for ep in ep_list:
            existing_episodes.add(int(ep.get('episodeNumber')))
        print(f"   ✓ Found {len(existing_episodes)} already registered episodes.")
        
    # 5. Start episode processing loop
    success_count = 0
    fail_count = 0
    
    for ep_no in range(1, total_episodes + 1):
        print(f"\n────────────────── Episode {ep_no}/{total_episodes} ──────────────────")
        
        # FORCE RE-PROCESSING for HD Bening Update (set to True to overwrite blurry videos)
        FORCE_REPROCESS = True
        
        # Check if already registered
        if ep_no in existing_episodes and not FORCE_REPROCESS:
            print(f"   ✓ Episode {ep_no} already registered, skipping.")
            success_count += 1
            continue
            
        # Get watch URL
        m3u8_url = get_episode_stream_url(ep_no)
        if not m3u8_url:
            print(f"   ✗ Failed to get HLS stream URL for EP {ep_no}, skipping.")
            fail_count += 1
            continue
            
        print(f"   HLS URL: {m3u8_url}")
        
        # Download and transcode via FFmpeg
        local_720, local_540 = download_and_transcode_ffmpeg(m3u8_url, ep_no)
        if not local_720:
            print(f"   ✗ Transcoding failed for EP {ep_no}, skipping.")
            fail_count += 1
            continue
            
        # Upload 720p to R2
        r2_key_720 = f"dramas/{BOOK_SLUG}/ep{ep_no:03d}_720p.mp4"
        video_720_r2 = upload_file_to_r2(r2, local_720, r2_key_720)
        
        # Upload 540p to R2
        video_540_r2 = None
        if local_540:
            r2_key_540 = f"dramas/{BOOK_SLUG}/ep{ep_no:03d}_540p.mp4"
            video_540_r2 = upload_file_to_r2(r2, local_540, r2_key_540)
            
        if not video_720_r2 and not video_540_r2:
            print(f"   ✗ All R2 uploads failed for EP {ep_no}, skipping.")
            fail_count += 1
            # Clean up temp files
            for f in [local_720, local_540]:
                if f and os.path.exists(f): os.remove(f)
            continue
            
        # Register episode in admin panel
        print(f"   📋 Registering episode EP {ep_no} in admin panel...")
        episode_id = register_episode(drama_id, ep_no, video_720_r2, video_540_r2)
        if episode_id:
            print(f"   ✓ Registered successfully! ID: {episode_id}")
            success_count += 1
        else:
            print(f"   ✗ Failed to register episode EP {ep_no} in admin.")
            fail_count += 1
            
        # Clean up local temp files
        for f in [local_720, local_540]:
            if f and os.path.exists(f):
                os.remove(f)
                
        # Sleep 2.0 seconds between episodes to avoid rate limiting
        time.sleep(2.0)
        
    print("\n" + "=" * 60)
    print(f"✅ PIPELINE COMPLETED!")
    print(f"   Drama ID: {drama_id}")
    print(f"   Success: {success_count}/{total_episodes}")
    print(f"   Failed:  {fail_count}/{total_episodes}")
    print(f"   Status:  PENDING (isActive=False)")
    print("=" * 60)

if __name__ == '__main__':
    main()
