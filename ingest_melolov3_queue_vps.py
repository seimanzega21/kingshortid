# -*- coding: utf-8 -*-
"""
VPS-BASED PIPELINE: Sequential Queue for MeloloV3 dramas
"""
import requests
import boto3
import sys
import json
import time
import os
import subprocess
import urllib3
from botocore.config import Config

urllib3.disable_warnings()
sys.stdout.reconfigure(encoding='utf-8')

# ─── CONFIG ────────────────────────────────────────────────────────────────
API_BASE     = 'http://localhost:3000/api'
ADMIN_KEY    = '00ca04e3e2702be565d7bf44e783255247708289bce9b2fb6187a2e117f87fd14'
ADMIN_HDR    = {'x-admin-key': ADMIN_KEY, 'Content-Type': 'application/json'}

R2_ENDPOINT  = 'https://a142d3b29a5d64943cb251157e25eaf3.r2.cloudflarestorage.com'
R2_KEY_ID    = '07c99c897986ea52703c1285308d5e2c'
R2_SECRET    = '44788d376ffb216e1e73784b6fe1ff1423607928898a87c50819b52cdfc12e44'
R2_BUCKET    = 'shortlovers'
R2_PUBLIC    = 'https://stream.shortlovers.id'

HEADERS = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36',
    'Referer': 'https://vidrama.asia/',
}

DRAMAS_QUEUE = [
    {'id': '7657771952576154629', 'slug': 'nikah-habis-turun-gunung', 'genres': ['Aksi', 'Drama', 'Romantis']},
    {'id': '7655568348528249909', 'slug': 'dokter-sakti-kota-jaya', 'genres': ['Drama', 'Pengobatan', 'Aksi']},
    {'id': '7649082391822093317', 'slug': 'dokter-sakti-sang-ceo', 'genres': ['Drama', 'Romantis', 'Pengobatan']},
    {'id': '7654802675023744005', 'slug': 'golok-ajaib-sang-juara', 'genres': ['Aksi', 'Drama', 'Wuxia']},
    {'id': '7651588401602235397', 'slug': 'asistenku-putri-bosku', 'genres': ['Romantis', 'Drama', 'CEO']},
    {'id': '7644788785384786949', 'slug': 'pengasuh-penakluk-bos', 'genres': ['Romantis', 'Drama', 'CEO']},
    {'id': '7653296776832617477', 'slug': 'rezeki-laut-sistem', 'genres': ['Drama', 'Sistem', 'Fantasi']},
    {'id': '7644468792575134773', 'slug': 'warisan-dewa-abadi', 'genres': ['Aksi', 'Drama', 'Dewa']},
    {'id': '7658127601654828085', 'slug': 'penguasa-keadilan', 'genres': ['Aksi', 'Drama', 'Keadilan']},
    {'id': '7647064808411368501', 'slug': 'raja-pemburu-berpesta', 'genres': ['Aksi', 'Drama', 'Petualangan']},
    {'id': '7654132839750831157', 'slug': 'legenda-koki-tua', 'genres': ['Drama', 'Koki', 'Komedi']},
    {'id': '7651858956284857397', 'slug': 'karunia-mata-sakti', 'genres': ['Drama', 'Aksi', 'Mata Sakti']},
    {'id': '7654842920003980293', 'slug': 'naga-sejati', 'genres': ['Aksi', 'Drama', 'Naga']},
]

def get_r2():
    return boto3.client(
        's3', endpoint_url=R2_ENDPOINT,
        aws_access_key_id=R2_KEY_ID, aws_secret_access_key=R2_SECRET,
        config=Config(signature_version='s3v4'), region_name='auto'
    )

def fetch_drama_details(upstream_id):
    detail_url = f'https://vidrama.asia/api/melolov3/series?id={upstream_id}&lang=id'
    videos_url = f'https://vidrama.asia/api/melolov3/multi-video?id={upstream_id}&lang=id'
    
    metadata = {}
    try:
        r = requests.get(detail_url, headers=HEADERS, timeout=20, verify=False)
        if r.ok:
            metadata = r.json().get('series') or {}
    except Exception as e:
        print(f"      ⚠ Error fetching metadata: {e}")
        
    episodes = []
    try:
        r = requests.get(videos_url, headers=HEADERS, timeout=20, verify=False)
        if r.ok:
            data = r.json()
            episodes = data.get('episodes') or data or []
    except Exception as e:
        print(f"      ⚠ Error fetching episodes: {e}")
        
    return metadata, episodes

def upload_cover_to_r2(r2, cover_url, slug, temp_dir):
    if not cover_url:
        return ""
    local_jpg = os.path.join(temp_dir, f"{slug}_cover_hq.jpg")
    try:
        url_to_fetch = cover_url
        if ".heic" in cover_url.lower():
            import urllib.parse
            url_to_fetch = f"https://wsrv.nl/?url={urllib.parse.quote(cover_url)}&output=jpg"
            
        r = requests.get(url_to_fetch, headers={'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64)'}, timeout=30, verify=False)
        if not r.ok:
            print(f"      ⚠ Failed to download cover. Status: {r.status_code}")
            return ""
        with open(local_jpg, 'wb') as f:
            f.write(r.content)
            
        # Upload
        r2_key = f"dramas/covers/{slug}_cover_hq.jpg"
        r2.upload_file(local_jpg, R2_BUCKET, r2_key, ExtraArgs={
            'ContentType': 'image/jpeg',
            'CacheControl': 'public, max-age=31536000'
        })
        
        if os.path.exists(local_jpg):
            os.remove(local_jpg)
            
        return f"{R2_PUBLIC}/{r2_key}"
    except Exception as e:
        print(f"      ⚠ Cover processing failed: {e}")
        return ""

def get_or_register_drama(r2, metadata, slug, genres, temp_dir):
    title = metadata.get('title') or 'Untitled Drama'
    
    # Check if already exists in DB
    try:
        url = f"{API_BASE}/dramas/search?q={requests.utils.quote(title)}"
        r = requests.get(url, timeout=15)
        if r.ok:
            dramas = r.json()
            if isinstance(dramas, dict):
                dramas = dramas.get('dramas', [])
            for d in dramas:
                if d.get('title', '').lower().strip() == title.lower().strip():
                    db_id = d.get('id')
                    print(f"   ✓ Drama already registered in DB: {db_id}")
                    # Ensure it is active
                    if not d.get('isActive'):
                        requests.post(f"{API_BASE}/admin/dramas", headers=ADMIN_HDR, json={'id': db_id, 'isActive': True}, timeout=10)
                    return db_id
    except Exception as e:
        print(f"      ⚠ DB duplicate check failed: {e}")
        
    # Process cover art
    cover_raw = metadata.get('cover') or ''
    cover_r2 = upload_cover_to_r2(r2, cover_raw, slug, temp_dir)
    
    # Register in DB
    payload = {
        'title': title,
        'description': metadata.get('intro') or 'No description available',
        'cover': cover_r2,
        'genres': genres,
        'totalEpisodes': metadata.get('episode_count') or len(metadata.get('episode_list', [])),
        'status': 'ongoing',
        'country': 'China',
        'language': 'Indonesia',
        'isActive': True,  # MUST BE TRUE!
        'isVip': False
    }
    
    try:
        r = requests.post(f"{API_BASE}/admin/dramas", headers=ADMIN_HDR, json=payload, timeout=30)
        if r.ok:
            db_id = r.json().get('id')
            print(f"   ✓ New drama registered! ID: {db_id}")
            return db_id
        else:
            print(f"      ❌ Failed to register drama. Status: {r.status_code}, Body: {r.text[:200]}")
    except Exception as e:
        print(f"      ❌ Drama registration exception: {e}")
        
    return None

def download_source_file(url, local_path):
    try:
        r = requests.get(url, headers=HEADERS, timeout=60, verify=False, stream=True)
        if r.ok:
            with open(local_path, 'wb') as f:
                for chunk in r.iter_content(chunk_size=1024*1024):
                    if chunk:
                        f.write(chunk)
            return True
    except Exception as e:
        print(f"      ⚠ Source download failed: {e}")
    return False

def transcode_to_resolutions(local_source, ep_no, temp_dir):
    local_720 = os.path.join(temp_dir, f"ep{ep_no:03d}_720p.mp4")
    local_540 = os.path.join(temp_dir, f"ep{ep_no:03d}_540p.mp4")
    
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
        res = subprocess.run(cmd, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        if res.returncode == 0 and os.path.exists(local_720) and os.path.getsize(local_720) > 50000:
            success_720 = True
            break
        else:
            print(f"         ⚠ 720p attempt {attempt} failed.")
            if attempt < 2: time.sleep(3)
            
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
        res = subprocess.run(cmd, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        if res.returncode == 0 and os.path.exists(local_540) and os.path.getsize(local_540) > 50000:
            success_540 = True
            break
        else:
            print(f"         ⚠ 540p attempt {attempt} failed.")
            if attempt < 2: time.sleep(3)
            
    if not success_540:
        return local_720, None
        
    return local_720, local_540

def process_drama(r2, item):
    upstream_id = item['id']
    slug = item['slug']
    genres = item['genres']
    
    temp_dir = f"/tmp/temp_melolo_{slug}"
    os.makedirs(temp_dir, exist_ok=True)
    
    print("\n" + "=" * 60)
    print(f"🎬 STARTING INGESTION: {slug} (ID: {upstream_id})")
    print("=" * 60)
    
    # 1. Fetch metadata and video list
    meta, eps_list = fetch_drama_details(upstream_id)
    if not meta or not eps_list:
        print("❌ Failed to fetch metadata or episodes list. Skipping.")
        return
        
    print(f"   Title: {meta.get('title')}")
    print(f"   Episodes: {len(eps_list)}")
    
    # 2. Get or register drama
    drama_db_id = get_or_register_drama(r2, meta, slug, genres, temp_dir)
    if not drama_db_id:
        print("❌ Failed to get/register drama in DB. Skipping.")
        return
        
    # 3. Fetch done episodes
    done_eps = set()
    try:
        url = f"{API_BASE}/dramas/{drama_db_id}/episodes?includeInactive=true"
        r_eps = requests.get(url, timeout=15)
        if r_eps.ok:
            eps_list_db = r_eps.json()
            done_eps = {e.get('episodeNumber') for e in eps_list_db}
    except Exception as e:
        print(f"   ⚠ Failed to fetch registered episodes: {e}")
        
    print(f"   Already done: {len(done_eps)} episodes")
    
    # 4. Process episodes
    for ep in eps_list:
        ep_no = ep.get('index') or 1
        if ep_no in done_eps:
            continue
            
        print(f"\n   ▶ Episode {ep_no}/{len(eps_list)}:")
        stream_url = ep.get('stream_url')
        if not stream_url:
            print(f"      ❌ No stream URL found for Ep {ep_no}. Skipping.")
            continue
            
        local_raw = os.path.join(temp_dir, f"ep{ep_no:03d}_raw.mp4")
        
        # Download
        print("      📥 Downloading source file...")
        if not download_source_file(stream_url, local_raw):
            print(f"      ❌ Failed to download source for Ep {ep_no}. Skipping.")
            continue
            
        # Get duration
        duration = 0
        try:
            cmd_dur = [
                "ffprobe", "-v", "error", "-show_entries", "format=duration",
                "-of", "default=noprint_wrappers=1:nokey=1", local_raw
            ]
            duration_str = subprocess.check_output(cmd_dur).decode('utf-8').strip()
            duration = int(round(float(duration_str)))
        except Exception as e:
            pass
            
        # Transcode
        print("      ⚡ Transcoding to 720p & 540p...")
        local_720, local_540 = transcode_to_resolutions(local_raw, ep_no, temp_dir)
        if os.path.exists(local_raw): os.remove(local_raw)
        
        if not local_720:
            print("      ❌ Transcoding failed. Skipping.")
            continue
            
        # Upload
        r2_key_720 = f"dramas/netshort/{slug}/ep{ep_no:03d}.mp4"
        r2_key_540 = f"dramas/netshort/{slug}/ep{ep_no:03d}_540p.mp4"
        
        r2_url_720 = ""
        r2_url_540 = ""
        
        print(f"      📤 Uploading 720p: {r2_key_720}")
        try:
            r2.upload_file(local_720, R2_BUCKET, r2_key_720, ExtraArgs={'ContentType': 'video/mp4'})
            r2_url_720 = f"{R2_PUBLIC}/{r2_key_720}"
            os.remove(local_720)
        except Exception as e:
            print(f"      ❌ Upload 720p failed: {e}")
            continue
            
        if local_540:
            print(f"      📤 Uploading 540p: {r2_key_540}")
            try:
                r2.upload_file(local_540, R2_BUCKET, r2_key_540, ExtraArgs={'ContentType': 'video/mp4'})
                r2_url_540 = f"{R2_PUBLIC}/{r2_key_540}"
                os.remove(local_540)
            except Exception as e:
                print(f"      ❌ Upload 540p failed: {e}")
                
        # DB Register
        payload_ep = {
            'episodeNumber': ep_no,
            'title': f'Episode {ep_no}',
            'videoUrl': r2_url_720,
            'videoUrl540p': r2_url_540,
            'isVip': False,
            'coinPrice': 0,
            'isActive': True,
            'duration': duration
        }
        
        ep_db_id = None
        for attempt in range(1, 6):
            try:
                r_reg = requests.post(f"{API_BASE}/admin/dramas/{drama_db_id}/episodes", headers=ADMIN_HDR, json=payload_ep, timeout=20)
                if r_reg.ok:
                    ep_db_id = r_reg.json().get('id')
                    print(f"      ✅ Registered! ID: {ep_db_id}")
                    break
            except Exception as e:
                print(f"      ⚠ Ep DB register failed (attempt {attempt}/5): {e}")
            time.sleep(2)
            
    # Cleanup temp directory
    try:
        import shutil
        shutil.rmtree(temp_dir)
    except:
        pass

def main():
    print("=================================================================")
    print(f"STARTING MELOLOV3 QUEUE: {len(DRAMAS_QUEUE)} dramas to process")
    print("=================================================================")
    
    r2 = get_r2()
    
    for idx, item in enumerate(DRAMAS_QUEUE, 1):
        print(f"\nProcessing item {idx}/{len(DRAMAS_QUEUE)}")
        try:
            process_drama(r2, item)
        except Exception as e:
            print(f"❌ Exception processing item {item['slug']}: {e}")
            
    print("\n=================================================================")
    print("ALL MELOLOV3 QUEUE ITEMS COMPLETED!")
    print("=================================================================")

if __name__ == '__main__':
    main()
