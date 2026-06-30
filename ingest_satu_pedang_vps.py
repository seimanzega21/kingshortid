# -*- coding: utf-8 -*-
"""
VPS-BASED PIPELINE: Satu Pedang, Tebas Raja Neraka
This script runs directly on the VPS to bypass local network timeouts.
It calls Next.js Server Actions directly to fetch m3u8 URLs, downloads them with 1ms latency,
transcodes via FFmpeg, uploads to R2, and registers in the admin database.
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
DRAMA_TITLE  = 'Satu Pedang, Tebas Raja Neraka'
DRAMA_SLUG   = 'satu-pedang-tebas-raja-neraka'
DRAMA_ID_WEB = '19820'
PROVIDER     = 'stardusttv'
TOTAL_EPS    = 69

COVER_URL    = 'https://assets.stardusttv.cc/uploadfile/20260624/928399303650660352.jpg'
DESCRIPTION  = (
    "Yarden yang dikenal sebagai pemuda berandal ternyata adalah Dewa Pedang, "
    "pendekar legendaris yang pernah mengalahkan Delapan Yama. Demi membalas "
    "dendam untuk ibunya, ia menyembunyikan identitasnya selama bertahun-tahun. "
    "Saat para Yama kembali mengacaukan Negeri Yan, Yarden akhirnya menunjukkan "
    "kekuatan sejati dan bangkit melawan musuh bebuyutannya."
)
GENRES       = ['Action', 'Fantasy', 'Drama', 'Wuxia']

# Use localhost since it runs directly on the VPS
API_BASE     = 'http://localhost:3000'
ADMIN_KEY    = '00ca04e3e2702be565d7bf44e783255247708289bce9b2fb6187a2e117f87fd14'
ADMIN_HDR    = {'x-admin-key': ADMIN_KEY, 'Content-Type': 'application/json'}

R2_ENDPOINT  = 'https://a142d3b29a5d64943cb251157e25eaf3.r2.cloudflarestorage.com'
R2_KEY_ID    = '07c99c897986ea52703c1285308d5e2c'
R2_SECRET    = '44788d376ffb216e1e73784b6fe1ff1423607928898a87c50819b52cdfc12e44'
R2_BUCKET    = 'shortlovers'
R2_PUBLIC    = 'https://stream.shortlovers.id'

TEMP_DIR     = '/tmp/temp_raja'
os.makedirs(TEMP_DIR, exist_ok=True)

# Progress file for auto-resume
PROGRESS_FILE = os.path.join(TEMP_DIR, 'progress.json')

# ─── HELPERS ───────────────────────────────────────────────────────────────
def get_r2():
    return boto3.client(
        's3', endpoint_url=R2_ENDPOINT,
        aws_access_key_id=R2_KEY_ID, aws_secret_access_key=R2_SECRET,
        config=Config(signature_version='s3v4'), region_name='auto'
    )

def load_progress():
    if os.path.exists(PROGRESS_FILE):
        try:
            with open(PROGRESS_FILE, 'r') as f:
                return json.load(f)
        except Exception:
            pass
    return {'drama_id': None, 'done_episodes': []}

def save_progress(progress):
    with open(PROGRESS_FILE, 'w') as f:
        json.dump(progress, f, indent=2)

def download_and_transcode(m3u8_url, ep_no):
    """Download HLS → 720p stream copy → 540p transcode, both with faststart"""
    local_720 = os.path.join(TEMP_DIR, f"ep{ep_no:03d}_720p.mp4")
    local_540 = os.path.join(TEMP_DIR, f"ep{ep_no:03d}_540p.mp4")
    
    # Clean up
    for f in [local_720, local_540]:
        if os.path.exists(f): os.remove(f)
    
    headers_str = (
        "User-Agent: Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
        "(KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36\r\n"
        "Referer: https://vidrama.asia/\r\n"
    )
    
    # 720p stream copy with faststart (3 retries)
    success_720 = False
    for attempt in range(1, 4):
        print(f"      🎥 Stream copy HLS → 720p (Attempt {attempt}/3)...")
        cmd = [
            'ffmpeg', '-y',
            '-headers', headers_str,
            '-i', m3u8_url,
            '-c', 'copy',
            '-movflags', '+faststart',
            '-loglevel', 'warning',
            local_720
        ]
        res = subprocess.run(cmd, capture_output=True, text=True, errors='ignore', timeout=300)
        if res.returncode == 0 and os.path.exists(local_720) and os.path.getsize(local_720) > 50000:
            success_720 = True
            size_mb = os.path.getsize(local_720) / (1024*1024)
            print(f"      ✓ 720p done ({size_mb:.1f} MB)")
            break
        else:
            print(f"      ⚠ Attempt {attempt} failed: {res.stderr.strip()[-200:]}")
            if attempt < 3: time.sleep(5)
    
    if not success_720:
        print(f"      ❌ 720p failed entirely")
        return None, None
    
    # 540p transcode from 720p (3 retries)
    success_540 = False
    for attempt in range(1, 4):
        print(f"      🎥 Transcode 720p → 540p (Attempt {attempt}/3)...")
        cmd = [
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
        res = subprocess.run(cmd, capture_output=True, text=True, errors='ignore', timeout=300)
        if res.returncode == 0 and os.path.exists(local_540) and os.path.getsize(local_540) > 50000:
            success_540 = True
            size_mb = os.path.getsize(local_540) / (1024*1024)
            print(f"      ✓ 540p done ({size_mb:.1f} MB)")
            break
        else:
            print(f"      ⚠ Attempt {attempt} failed: {res.stderr.strip()[-200:]}")
            if attempt < 3: time.sleep(5)
    
    if not success_540:
        print(f"      ⚠ 540p failed, will use 720p only")
        return local_720, None
    
    return local_720, local_540

def upload_to_r2(r2, local_path, r2_key):
    print(f"      ⬆ Uploading {os.path.basename(r2_key)}...", end='', flush=True)
    try:
        size_mb = os.path.getsize(local_path) / (1024*1024)
        with open(local_path, 'rb') as f:
            r2.upload_fileobj(
                f, R2_BUCKET, r2_key,
                ExtraArgs={'ContentType': 'video/mp4', 'CacheControl': 'public, max-age=31536000'}
            )
        print(f" ✓ ({size_mb:.1f} MB)")
        return f"{R2_PUBLIC}/{r2_key}"
    except Exception as e:
        print(f" ✗ Error: {e}")
        return None

def upload_cover():
    r2 = get_r2()
    key = f"dramas/{DRAMA_SLUG}/cover.jpg"
    try:
        r2.head_object(Bucket=R2_BUCKET, Key=key)
        url = f"{R2_PUBLIC}/{key}"
        print(f"  ✓ Cover already in R2: {url}")
        return url
    except Exception:
        pass
    
    print(f"  🖼 Downloading cover...")
    try:
        r = requests.get(COVER_URL, timeout=30, verify=False)
        if r.ok:
            r2.upload_fileobj(
                io.BytesIO(r.content), R2_BUCKET, key,
                ExtraArgs={'ContentType': 'image/jpeg', 'CacheControl': 'public, max-age=31536000'}
            )
            url = f"{R2_PUBLIC}/{key}"
            print(f"  ✓ Cover uploaded: {url}")
            return url
    except Exception as e:
        print(f"  ⚠ Cover upload failed: {e}")
    return COVER_URL

def register_drama(cover_r2_url):
    payload = {
        'title': DRAMA_TITLE,
        'description': DESCRIPTION,
        'cover': cover_r2_url,
        'genres': GENRES,
        'totalEpisodes': TOTAL_EPS,
        'status': 'ongoing',
        'country': 'China',
        'language': 'Indonesia',
        'isActive': False,  # pending = not active
        'isVip': False,
    }
    print(f"\n📋 Registering drama in admin panel...")
    r = requests.post(f"{API_BASE}/api/admin/dramas", headers=ADMIN_HDR, json=payload, timeout=30)
    if r.ok:
        resp = r.json()
        drama_id = resp.get('id') or resp.get('drama', {}).get('id')
        print(f"  ✓ Drama registered! ID: {drama_id}")
        return drama_id
    else:
        print(f"  ✗ Failed: {r.status_code} {r.text[:300]}")
        return None

def get_or_create_drama():
    progress = load_progress()
    if progress.get('drama_id'):
        print(f"  ✓ Resuming with existing drama ID: {progress['drama_id']}")
        return progress['drama_id']
    
    # Search in admin
    r = requests.get(f"{API_BASE}/api/dramas", params={"search": DRAMA_TITLE}, timeout=15)
    if r.ok:
        data = r.json()
        dramas = data if isinstance(data, list) else data.get('dramas', [])
        for d in dramas:
            if DRAMA_TITLE.lower() in d.get('title', '').lower():
                print(f"  ✓ Found existing drama: {d['id']}")
                return d['id']
    
    # Create new
    print(f"\n🖼 Uploading cover to R2...")
    cover_r2 = upload_cover()
    return register_drama(cover_r2)

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
        # Try update if already exists
        r2 = requests.put(
            f"{API_BASE}/api/admin/dramas/{drama_id}/episodes/{ep_no}",
            headers=ADMIN_HDR, json=payload, timeout=20
        )
        if r2.ok:
            return r2.json().get('id') or 'updated'
    return None

# ─── NEXT.JS SERVER ACTION FETCHER ─────────────────────────────────────────
def get_m3u8_for_episode(ep_no):
    """Call Next.js Server Action to get stardusttv stream details"""
    action_id = '701fda472c36d458ba0a5efdba67386467d16aba38'
    url = f'https://vidrama.asia/en/watch/{DRAMA_SLUG}--{DRAMA_ID_WEB}/1?provider={PROVIDER}'
    
    hdrs = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36',
        'Referer': url,
        'Accept': 'text/x-component',
        'Content-Type': 'text/plain;charset=UTF-8',
        'next-action': action_id
    }
    
    body_data = [DRAMA_ID_WEB, ep_no, "id"]
    
    for attempt in range(1, 6):
        try:
            r = requests.post(url, headers=hdrs, data=json.dumps(body_data), timeout=15, verify=False)
            if r.ok:
                # Parse Next.js action response format: '1:{"status":true,"videoUrl":"..."}'
                for line in r.text.split('\n'):
                    if line.strip().startswith('1:') or '"videoUrl"' in line:
                        # Extract the json part after the next.js index
                        content = line[line.find('{'):] if '{' in line else line
                        data = json.loads(content)
                        if data.get('status') and data.get('videoUrl'):
                            return data.get('videoUrl')
            else:
                print(f"      ⚠ Server Action HTTP {r.status_code} (attempt {attempt}/5)")
        except Exception as e:
            print(f"      ⚠ Server Action Error (attempt {attempt}/5): {e}")
        time.sleep(3)
    return None

# ─── MAIN ──────────────────────────────────────────────────────────────────
def main():
    print("=" * 65)
    print(f"🎬 VPS SCRAPER PIPELINE: {DRAMA_TITLE}")
    print(f"   Provider: {PROVIDER} | Episodes: {TOTAL_EPS}")
    print("=" * 65)
    
    r2 = get_r2()
    
    # Step 1: Get or create drama in admin
    print("\n🔍 Checking drama in KingShort DB...")
    drama_id = get_or_create_drama()
    if not drama_id:
        print("❌ Failed to get/create drama! Aborting.")
        return
    
    progress = load_progress()
    progress['drama_id'] = drama_id
    save_progress(progress)
    
    # Step 2: Get already registered episodes
    done_eps = set(progress.get('done_episodes', []))
    print(f"\n🔍 Checking existing registered episodes...")
    er = requests.get(f"{API_BASE}/api/dramas/{drama_id}/episodes", timeout=15)
    if er.ok:
        for ep in er.json():
            done_eps.add(int(ep.get('episodeNumber', 0)))
    print(f"   Already done: {len(done_eps)} episodes")
    
    # Step 3: Process each episode
    success_count = 0
    fail_count = 0
    
    for ep_no in range(1, TOTAL_EPS + 1):
        print(f"\n{'─' * 60}")
        print(f"📺 Episode {ep_no}/{TOTAL_EPS}")
        
        # Check if already done
        if ep_no in done_eps:
            print(f"   ✓ Already registered, skipping.")
            success_count += 1
            continue
        
        r2_key_720 = f"dramas/{DRAMA_SLUG}/ep{ep_no:03d}_720p.mp4"
        r2_key_540 = f"dramas/{DRAMA_SLUG}/ep{ep_no:03d}_540p.mp4"
        
        url_720 = None
        url_540 = None
        
        # Check R2 for existing files
        try:
            r2.head_object(Bucket=R2_BUCKET, Key=r2_key_720)
            url_720 = f"{R2_PUBLIC}/{r2_key_720}"
            print(f"   ✓ 720p already in R2")
        except Exception:
            pass
        
        try:
            r2.head_object(Bucket=R2_BUCKET, Key=r2_key_540)
            url_540 = f"{R2_PUBLIC}/{r2_key_540}"
            print(f"   ✓ 540p already in R2")
        except Exception:
            pass
        
        # If not in R2, download
        if not url_720:
            print(f"   🌐 Fetching m3u8 URL via Next.js Server Action...")
            m3u8_url = get_m3u8_for_episode(ep_no)
            
            if not m3u8_url:
                print(f"   ❌ Failed to get m3u8 URL for EP {ep_no}, skipping.")
                fail_count += 1
                continue
            
            print(f"   🔗 M3U8: {m3u8_url[-80:]}")
            
            # Download & transcode
            local_720, local_540 = download_and_transcode(m3u8_url, ep_no)
            if not local_720:
                print(f"   ❌ Download/transcode failed for EP {ep_no}")
                fail_count += 1
                continue
            
            # Upload to R2
            url_720 = upload_to_r2(r2, local_720, r2_key_720)
            if local_540:
                url_540 = upload_to_r2(r2, local_540, r2_key_540)
            
            # Cleanup temp files
            for f in [local_720, local_540]:
                if f and os.path.exists(f):
                    os.remove(f)
            
            if not url_720:
                print(f"   ❌ R2 upload failed for EP {ep_no}")
                fail_count += 1
                continue
        
        # Register episode in admin
        print(f"   📋 Registering episode in admin panel...")
        ep_id = register_episode(drama_id, ep_no, url_720, url_540)
        if ep_id:
            print(f"   ✅ Done! ID: {ep_id}")
            success_count += 1
            done_eps.add(ep_no)
            progress['done_episodes'] = list(done_eps)
            save_progress(progress)
        else:
            print(f"   ❌ Failed to register EP {ep_no} in admin")
            fail_count += 1
        
        # Small delay to avoid rate limiting
        time.sleep(1)
    
    print("\n" + "=" * 65)
    print(f"✅ PIPELINE COMPLETED!")
    print(f"   Drama: {DRAMA_TITLE}")
    print(f"   Drama ID: {drama_id}")
    print(f"   Success: {success_count}/{TOTAL_EPS}")
    print(f"   Failed:  {fail_count}/{TOTAL_EPS}")
    print(f"   Status:  PENDING (isActive=False)")
    print("=" * 65)

if __name__ == '__main__':
    main()
