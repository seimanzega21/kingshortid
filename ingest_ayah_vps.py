# -*- coding: utf-8 -*-
"""
VPS-BASED PIPELINE: Dubbing Apa Ayahku Ternyata Orang Besar (ID: 845471)
Provider: shortmax
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
DRAMA_ID_WEB = '845471'
DRAMA_SLUG   = 'dubbing-apa-ayahku-ternyata-orang-besar'
GENRES       = ['Drama', 'Keluarga', 'Wuxia']

# Use localhost since it runs directly on the VPS
API_BASE     = 'http://localhost:3000'
ADMIN_KEY    = '00ca04e3e2702be565d7bf44e783255247708289bce9b2fb6187a2e117f87fd14'
ADMIN_HDR    = {'x-admin-key': ADMIN_KEY, 'Content-Type': 'application/json'}

R2_ENDPOINT  = 'https://a142d3b29a5d64943cb251157e25eaf3.r2.cloudflarestorage.com'
R2_KEY_ID    = '07c99c897986ea52703c1285308d5e2c'
R2_SECRET    = '44788d376ffb216e1e73784b6fe1ff1423607928898a87c50819b52cdfc12e44'
R2_BUCKET    = 'shortlovers'
R2_PUBLIC    = 'https://stream.shortlovers.id'

TEMP_DIR     = '/tmp/temp_ayah'
os.makedirs(TEMP_DIR, exist_ok=True)

# ─── HELPERS ───────────────────────────────────────────────────────────────
def get_r2():
    return boto3.client(
        's3', endpoint_url=R2_ENDPOINT,
        aws_access_key_id=R2_KEY_ID, aws_secret_access_key=R2_SECRET,
        config=Config(signature_version='s3v4'), region_name='auto'
    )

def fetch_drama_details(mid):
    """Fetch drama metadata and full episode list via Next.js Server Action"""
    action_id = '60d082460fd19212e46371444b136af44119ce6a25'
    url = f'https://vidrama.asia/en/watch/slug--{mid}/1?provider=shortmax'
    
    hdrs = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36',
        'Referer': url,
        'Accept': 'text/x-component',
        'Content-Type': 'text/plain;charset=UTF-8',
        'next-action': action_id
    }
    
    print(f"   🌐 Fetching details for drama ID {mid}...")
    for attempt in range(1, 6):
        try:
            r = requests.post(url, headers=hdrs, data=json.dumps([mid, "id"]), timeout=20, verify=False)
            if r.ok:
                metadata = {}
                episodes = []
                for line in r.text.split('\n'):
                    line = line.strip()
                    if not line or ':' not in line:
                        continue
                    try:
                        idx, content = line.split(':', 1)
                        obj = json.loads(content)
                        if isinstance(obj, dict) and 'title' in obj:
                            metadata = obj
                            if 'list' in obj and isinstance(obj['list'], list):
                                episodes = obj['list']
                    except Exception:
                        pass
                
                if metadata:
                    return metadata, episodes
            else:
                print(f"      ⚠ HTTP {r.status_code} (attempt {attempt}/5)")
        except Exception as e:
            print(f"      ⚠ Connection error (attempt {attempt}/5): {e}")
        time.sleep(3)
    return None, []

def fetch_episode_url(mid, ep_no):
    """Fetch episode stream url via Next.js Server Action"""
    action_id = '700a88bb402f0a83f0ac8d827995d0ad3ac3d56b53'
    url = f'https://vidrama.asia/en/watch/slug--{mid}/{ep_no}?provider=shortmax'
    
    hdrs = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36',
        'Referer': url,
        'Accept': 'text/x-component',
        'Content-Type': 'text/plain;charset=UTF-8',
        'next-action': action_id
    }
    
    for attempt in range(1, 6):
        try:
            r = requests.post(url, headers=hdrs, data=json.dumps([mid, ep_no, "id"]), timeout=20, verify=False)
            if r.ok:
                for line in r.text.split('\n'):
                    line = line.strip()
                    if not line or ':' not in line:
                        continue
                    try:
                        idx, content = line.split(':', 1)
                        obj = json.loads(content)
                        if isinstance(obj, dict) and ('videoUrl' in obj or 'url' in obj):
                            qualities = obj.get('qualities') or {}
                            m3u8 = qualities.get('video_720') or qualities.get('video_1080') or obj.get('videoUrl') or obj.get('url')
                            if m3u8:
                                if 'proxy?url=' in m3u8:
                                    import urllib.parse
                                    parsed = urllib.parse.urlparse(m3u8)
                                    query = urllib.parse.parse_qs(parsed.query)
                                    m3u8 = query.get('url', [m3u8])[0]
                                return m3u8
                    except Exception:
                        pass
            else:
                print(f"      ⚠ Ep HTTP {r.status_code} (attempt {attempt}/5)")
        except Exception as e:
            print(f"      ⚠ Ep Connection error (attempt {attempt}/5): {e}")
        time.sleep(2)
    return None

def download_and_transcode(m3u8_url, ep_no):
    local_720 = os.path.join(TEMP_DIR, f"ep{ep_no:03d}_720p.mp4")
    local_540 = os.path.join(TEMP_DIR, f"ep{ep_no:03d}_540p.mp4")
    
    for f in [local_720, local_540]:
        if os.path.exists(f): os.remove(f)
        
    headers_str = (
        "User-Agent: Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
        "(KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36\r\n"
        "Referer: https://vidrama.asia/\r\n"
    )
    
    # 720p stream copy
    success_720 = False
    for attempt in range(1, 4):
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
            break
        else:
            print(f"      ⚠ 720p Attempt {attempt} failed: {res.stderr.strip()[-200:]}")
            if attempt < 3: time.sleep(5)
            
    if not success_720:
        return None, None
        
    # 540p transcode
    success_540 = False
    for attempt in range(1, 4):
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
            break
        else:
            print(f"      ⚠ 540p Attempt {attempt} failed: {res.stderr.strip()[-200:]}")
            if attempt < 3: time.sleep(5)
            
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
    title = metadata.get('title')
    
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
    cover_url = metadata.get('cover') or metadata.get('image') or ''
    cover_r2 = upload_cover(r2, cover_url)
    
    # Register new drama
    payload = {
        'title': title,
        'description': metadata.get('description') or metadata.get('introduction') or '',
        'cover': cover_r2,
        'genres': GENRES,
        'totalEpisodes': metadata.get('chapterCount') or 56,
        'status': 'pending',  # pending
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
    
    # 1. Fetch metadata and episodes
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
        ep_no = int(ep.get('episodeNumber') or ep.get('episodeNo', 0))
        if not ep_no:
            continue
            
        print(f"\n   📺 Episode {ep_no}/{len(eps_list)}:")
        
        if ep_no in done_eps:
            print("      ✓ Already registered, skipping.")
            success_count += 1
            continue
            
        # Fetch stream url dynamically
        m3u8_url = fetch_episode_url(DRAMA_ID_WEB, ep_no)
        if not m3u8_url:
            print(f"      ❌ Failed to fetch stream URL for EP {ep_no}")
            fail_count += 1
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
            local_720, local_540 = download_and_transcode(m3u8_url, ep_no)
            if not local_720:
                print(f"      ❌ Download/transcode failed for EP {ep_no}")
                fail_count += 1
                continue
                
            url_720 = upload_to_r2(r2, local_720, r2_key_720)
            if local_540:
                url_540 = upload_to_r2(r2, local_540, r2_key_540)
                
            # Cleanup
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
