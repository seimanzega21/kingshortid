# -*- coding: utf-8 -*-
"""
VPS-BASED PIPELINE: Cinta dan Tombak Purba (ID: 7638940406738062389)
Bypasses local machine network limits. Downloads direct HEVC MP4 streams,
transcodes to H.264 (720p & 540p vertical) via FFmpeg, uploads to R2,
and registers in the admin database.
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

# ─── CONFIG ────────────────────────────────────────────────────────────────
DRAMA_ID_WEB = '7638940406738062389'
DRAMA_SLUG   = 'cinta-dan-tombak-purba'
GENRES       = ['Romantis', 'Fantasy', 'Wuxia', 'Drama']

# Use localhost since it runs directly on the VPS
API_BASE     = 'http://localhost:3000'
ADMIN_KEY    = '00ca04e3e2702be565d7bf44e783255247708289bce9b2fb6187a2e117f87fd14'
ADMIN_HDR    = {'x-admin-key': ADMIN_KEY, 'Content-Type': 'application/json'}

R2_ENDPOINT  = 'https://a142d3b29a5d64943cb251157e25eaf3.r2.cloudflarestorage.com'
R2_KEY_ID    = '07c99c897986ea52703c1285308d5e2c'
R2_SECRET    = '44788d376ffb216e1e73784b6fe1ff1423607928898a87c50819b52cdfc12e44'
R2_BUCKET    = 'shortlovers'
R2_PUBLIC    = 'https://stream.shortlovers.id'

TEMP_DIR     = '/tmp/temp_tombak'
os.makedirs(TEMP_DIR, exist_ok=True)

# ─── HELPERS ───────────────────────────────────────────────────────────────
def get_r2():
    return boto3.client(
        's3', endpoint_url=R2_ENDPOINT,
        aws_access_key_id=R2_KEY_ID, aws_secret_access_key=R2_SECRET,
        config=Config(signature_version='s3v4'), region_name='auto'
    )

def fetch_drama_details(mid):
    """Fetch drama metadata and full episode list from melolov3 API"""
    WEB_HDRS = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36',
        'Referer': 'https://vidrama.asia/',
    }
    
    # Fetch detail
    detail_url = f'https://vidrama.asia/api/melolov3/series?id={mid}&lang=id'
    print(f"   🌐 Querying drama detail from: {detail_url}")
    metadata = {}
    try:
        r = requests.get(detail_url, headers=WEB_HDRS, timeout=20, verify=False)
        if r.ok:
            data = r.json()
            if 'series' in data:
                metadata = data['series']
    except Exception as e:
        print(f"      ⚠ Error fetching metadata: {e}")
        
    # Fetch episodes stream list
    episodes = []
    videos_url = f'https://vidrama.asia/api/melolov3/multi-video?id={mid}&lang=id'
    print(f"   🌐 Querying episodes stream list from: {videos_url}")
    try:
        r = requests.get(videos_url, headers=WEB_HDRS, timeout=20, verify=False)
        if r.ok:
            data = r.json()
            if 'episodes' in data:
                episodes = data['episodes']
    except Exception as e:
        print(f"      ⚠ Error fetching episodes: {e}")
        
    return metadata, episodes

def download_source_file(url, local_path):
    WEB_HDRS = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36',
        'Referer': 'https://vidrama.asia/',
    }
    try:
        r = requests.get(url, headers=WEB_HDRS, timeout=45, verify=False, stream=True)
        if r.ok:
            with open(local_path, 'wb') as f:
                for chunk in r.iter_content(chunk_size=1024*1024):
                    if chunk:
                        f.write(chunk)
            return True
    except Exception as e:
        print(f"      ⚠ Download failed: {e}")
    return False

def transcode_to_resolutions(local_source, ep_no):
    local_720 = os.path.join(TEMP_DIR, f"ep{ep_no:03d}_720p.mp4")
    local_540 = os.path.join(TEMP_DIR, f"ep{ep_no:03d}_540p.mp4")
    
    for f in [local_720, local_540]:
        if os.path.exists(f): os.remove(f)
        
    # Transcode 720p (H.264, scale width to 720 vertical, faststart)
    success_720 = False
    for attempt in range(1, 3):
        cmd = [
            'ffmpeg', '-y',
            '-i', local_source,
            '-vf', 'scale=720:-2',
            '-c:v', 'libx264', '-crf', '23', '-preset', 'fast',
            '-maxrate', '1500k', '-bufsize', '3000k',
            '-c:a', 'aac', '-b:a', '128k',
            '-movflags', '+faststart',
            '-loglevel', 'warning',
            local_720
        ]
        res = subprocess.run(cmd, capture_output=True, text=True, errors='ignore', timeout=300)
        if res.returncode == 0 and os.path.exists(local_720) and os.path.getsize(local_720) > 50000:
            success_720 = True
            break
        else:
            print(f"      ⚠ 720p Transcode Attempt {attempt} failed: {res.stderr.strip()[-200:]}")
            if attempt < 2: time.sleep(5)
            
    if not success_720:
        return None, None
        
    # Transcode 540p (H.264, scale width to 540 vertical, faststart)
    success_540 = False
    for attempt in range(1, 3):
        cmd = [
            'ffmpeg', '-y',
            '-i', local_720,
            '-vf', 'scale=540:-2',
            '-c:v', 'libx264', '-crf', '26', '-preset', 'fast',
            '-maxrate', '1000k', '-bufsize', '2000k',
            '-c:a', 'aac', '-b:a', '96k',
            '-movflags', '+faststart',
            '-loglevel', 'warning',
            local_540
        ]
        res = subprocess.run(cmd, capture_output=True, text=True, errors='ignore', timeout=300)
        if res.returncode == 0 and os.path.exists(local_540) and os.path.getsize(local_540) > 50000:
            success_540 = True
            break
        else:
            print(f"      ⚠ 540p Transcode Attempt {attempt} failed: {res.stderr.strip()[-200:]}")
            if attempt < 2: time.sleep(5)
            
    if not success_540:
        return local_720, None
        
    return local_720, local_540

def upload_to_r2(r2, local_path, r2_key):
    try:
        size_mb = os.path.getsize(local_path) / (1024*1024)
        with open(local_path, 'rb') as f:
            r2.upload_fileobj(
                f, R2_BUCKET, r2_key,
                ExtraArgs={'ContentType': 'video/mp4', 'CacheControl': 'public, max-age=31536000'}
            )
        print(f"      ✓ Uploaded {os.path.basename(r2_key)} ({size_mb:.1f} MB)")
        return f"{R2_PUBLIC}/{r2_key}"
    except Exception as e:
        print(f"      ✗ Upload failed: {e}")
        return None

def upload_cover(r2, cover_url):
    key = f"dramas/{DRAMA_SLUG}/cover.jpg"
    try:
        r2.head_object(Bucket=R2_BUCKET, Key=key)
        return f"{R2_PUBLIC}/{key}"
    except Exception:
        pass
        
    try:
        url_to_fetch = cover_url
        if ".heic" in cover_url.lower():
            import urllib.parse
            url_to_fetch = f"https://wsrv.nl/?url={urllib.parse.quote(cover_url)}&output=jpg"
            
        r = requests.get(url_to_fetch, headers={'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64)'}, timeout=30, verify=False)
        if r.ok:
            r2.upload_fileobj(
                io.BytesIO(r.content), R2_BUCKET, key,
                ExtraArgs={'ContentType': 'image/jpeg', 'CacheControl': 'public, max-age=31536000'}
            )
            return f"{R2_PUBLIC}/{key}"
    except Exception as e:
        print(f"      ⚠ Cover upload failed: {e}")
    return cover_url

def get_or_register_drama(metadata):
    title = metadata.get('title') or 'Cinta dan Tombak Purba'
    
    # Check if already exists in DB
    r = requests.get(f"{API_BASE}/api/dramas", params={"search": title}, timeout=15)
    if r.ok:
        data = r.json()
        dramas = data if isinstance(data, list) else data.get('dramas', [])
        for d in dramas:
            if title.lower() in d.get('title', '').lower():
                print(f"   ✓ Drama already registered in DB: {d['id']}")
                return d['id']
                
    # Upload cover first
    print(f"   🖼 Uploading cover image...")
    r2 = get_r2()
    cover_url = metadata.get('cover') or ''
    cover_r2 = upload_cover(r2, cover_url)
    
    # Register new drama
    payload = {
        'title': title,
        'description': metadata.get('intro') or '',
        'cover': cover_r2,
        'genres': GENRES,
        'totalEpisodes': metadata.get('episode_count') or 50,
        'status': 'ongoing',
        'country': 'China',
        'language': 'Indonesia',
        'isActive': False,  # pending = not active
        'isVip': False,
    }
    r = requests.post(f"{API_BASE}/api/admin/dramas", headers=ADMIN_HDR, json=payload, timeout=30)
    if r.ok:
        resp = r.json()
        drama_id = resp.get('id') or resp.get('drama', {}).get('id')
        print(f"   ✓ New drama registered! ID: {drama_id}")
        return drama_id
    else:
        print(f"   ✗ Drama registration failed: {r.status_code} {r.text[:200]}")
        return None

def register_episode(drama_id, ep_no, url_720, url_540):
    payload = {
        'episodeNumber': ep_no,
        'title': f'Episode {ep_no}',
        'videoUrl': url_720 or url_540 or '',
        'videoUrl540p': url_540 or '',
        'isVip': False,
        'coinPrice': 0,
        'isActive': True,
    }
    r = requests.post(
        f"{API_BASE}/api/admin/dramas/{drama_id}/episodes",
        headers=ADMIN_HDR, json=payload, timeout=20
    )
    if r.ok:
        return r.json().get('id')
    else:
        # Try update if exists
        r2 = requests.put(
            f"{API_BASE}/api/admin/dramas/{drama_id}/episodes/{ep_no}",
            headers=ADMIN_HDR, json=payload, timeout=20
        )
        if r2.ok:
            return r2.json().get('id') or 'updated'
    return None

def main():
    print("=" * 65)
    print(f"🎬 PROCESSING SINGLE DRAMA: {DRAMA_SLUG} (ID: {DRAMA_ID_WEB})")
    print("=" * 65)
    
    r2 = get_r2()
    
    # 1. Fetch metadata and stream links
    meta, eps_list = fetch_drama_details(DRAMA_ID_WEB)
    if not meta or not eps_list:
        print("❌ Failed to fetch drama details! Aborting.")
        return
        
    print(f"   Drama Title: {meta.get('title')}")
    print(f"   Total Episodes: {len(eps_list)}")
    
    # 2. Get or Register Drama
    drama_id = get_or_register_drama(meta)
    if not drama_id:
        print("❌ Failed to register drama! Aborting.")
        return
        
    # 3. Get existing episodes in DB
    done_eps = set()
    er = requests.get(f"{API_BASE}/api/dramas/{drama_id}/episodes", timeout=15)
    if er.ok:
        for ep in er.json():
            done_eps.add(int(ep.get('episodeNumber', 0)))
    print(f"   Already done in DB: {len(done_eps)} episodes")
    
    # 4. Ingest each episode
    success_count = 0
    fail_count = 0
    
    for ep in eps_list:
        ep_no = int(ep.get('index') or 0)
        source_mp4_url = ep.get('stream_url')
        
        if not ep_no or not source_mp4_url:
            continue
            
        print(f"\n   📺 Episode {ep_no}/{len(eps_list)}:")
        
        if ep_no in done_eps:
            print("      ✓ Already registered, skipping.")
            success_count += 1
            continue
            
        r2_key_720 = f"dramas/{DRAMA_SLUG}/ep{ep_no:03d}_720p.mp4"
        r2_key_540 = f"dramas/{DRAMA_SLUG}/ep{ep_no:03d}_540p.mp4"
        
        url_720 = None
        url_540 = None
        
        # Check R2
        try:
            r2.head_object(Bucket=R2_BUCKET, Key=r2_key_720)
            url_720 = f"{R2_PUBLIC}/{r2_key_720}"
        except Exception:
            pass
            
        try:
            r2.head_object(Bucket=R2_BUCKET, Key=r2_key_540)
            url_540 = f"{R2_PUBLIC}/{r2_key_540}"
        except Exception:
            pass
            
        # Download, transcode & upload if not in R2
        if not url_720:
            local_source = os.path.join(TEMP_DIR, f"source_ep{ep_no:03d}.mp4")
            if os.path.exists(local_source): os.remove(local_source)
            
            print("      ↓ Downloading source file...")
            if not download_source_file(source_mp4_url, local_source):
                print(f"      ❌ Source download failed for EP {ep_no}")
                fail_count += 1
                continue
                
            print("      ⚙ Transcoding to H.264 (720p & 540p)...")
            local_720, local_540 = transcode_to_resolutions(local_source, ep_no)
            
            # Clean up source file
            if os.path.exists(local_source): os.remove(local_source)
            
            if not local_720:
                print(f"      ❌ Transcoding failed for EP {ep_no}")
                fail_count += 1
                continue
                
            url_720 = upload_to_r2(r2, local_720, r2_key_720)
            if local_540:
                url_540 = upload_to_r2(r2, local_540, r2_key_540)
                
            # Cleanup temp transcoded files
            for f in [local_720, local_540]:
                if f and os.path.exists(f): os.remove(f)
                
            if not url_720:
                print(f"      ❌ R2 upload failed for EP {ep_no}")
                fail_count += 1
                continue
        else:
            print("      ✓ Already in R2")
            
        # Register in DB
        ep_id = register_episode(drama_id, ep_no, url_720, url_540)
        if ep_id:
            print(f"      ✅ Done! ID: {ep_id}")
            success_count += 1
            done_eps.add(ep_no)
        else:
            print(f"      ❌ DB Registration failed for EP {ep_no}")
            fail_count += 1
            
        time.sleep(0.5)
        
    print("\n" + "=" * 65)
    print(f"🏁 INGESTION COMPLETE FOR {meta.get('title')}!")
    print(f"   Success: {success_count}/{len(eps_list)}")
    print(f"   Failed:  {fail_count}/{len(eps_list)}")
    print("=" * 65)

if __name__ == '__main__':
    main()
