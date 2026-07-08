# -*- coding: utf-8 -*-
"""
VPS-BASED PIPELINE: Sequential Queue for 5 Netshort Dramas
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
API_BASE     = 'http://localhost:3000'
ADMIN_KEY    = '00ca04e3e2702be565d7bf44e783255247708289bce9b2fb6187a2e117f87fd14'
ADMIN_HDR    = {'x-admin-key': ADMIN_KEY, 'Content-Type': 'application/json'}

R2_ENDPOINT  = 'https://a142d3b29a5d64943cb251157e25eaf3.r2.cloudflarestorage.com'
R2_KEY_ID    = '07c99c897986ea52703c1285308d5e2c'
R2_SECRET    = '44788d376ffb216e1e73784b6fe1ff1423607928898a87c50819b52cdfc12e44'
R2_BUCKET    = 'shortlovers'
R2_PUBLIC    = 'https://stream.shortlovers.id'

TEMP_DIR     = '/tmp/temp_netshort_queue'
os.makedirs(TEMP_DIR, exist_ok=True)

DRAMAS = [
    {"id": "2073601289130450945", "slug": "kini-saatnya-menjaga-negara", "genres": ["Drama", "Aksi", "Militer"]},
    {"id": "2073323232624738306", "slug": "putri-ikan-bangkit-dari-darah-naga", "genres": ["Drama", "Wuxia", "Fantasi"]},
    {"id": "2073963764476649474", "slug": "tato-terbuka-rahasia-terungkap", "genres": ["Drama", "Misteri", "Romansa"]},
    {"id": "2073253378811068418", "slug": "ikatan-manis-dengan-pengawal", "genres": ["Drama", "Romansa", "Aksi"]},
    {"id": "2073980117816287234", "slug": "peluru-pencari-keadilan", "genres": ["Drama", "Aksi", "Misteri"]},
    {"id": "2072199002440175617", "slug": "ambisi-adalah-racun", "genres": ["Drama", "Romansa", "Aksi"]},
    {"id": "2071861523530862594", "slug": "sup-pedasku-kalahkan-chef-hebat", "genres": ["Drama", "Kuliner", "Romansa"]},
    {"id": "2059539265339858946", "slug": "memasak-aku-tak-pernah-kalah", "genres": ["Drama", "Kuliner", "Romansa"]},
    {"id": "2072569902616489986", "slug": "kebangkitan-tabib-perempuan", "genres": ["Drama", "Wuxia", "Medis"]},
    {"id": "2071838112737865730", "slug": "legenda-balap-yang-dipuja", "genres": ["Drama", "Aksi", "Olahraga"]}
]

# ─── HELPERS ───────────────────────────────────────────────────────────────
def get_r2():
    return boto3.client(
        's3', endpoint_url=R2_ENDPOINT,
        aws_access_key_id=R2_KEY_ID, aws_secret_access_key=R2_SECRET,
        config=Config(signature_version='s3v4'), region_name='auto'
    )

def fetch_drama_details(mid):
    url = f"https://netshort.goodbos.online/api/drama/{mid}?lang=in"
    print(f"   🌐 Fetching details for drama ID {mid}...")
    hdrs = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36',
        'Referer': 'https://vidrama.asia/',
    }
    for attempt in range(1, 6):
        try:
            r = requests.get(url, headers=hdrs, timeout=20)
            if r.ok:
                res = r.json()
                if 'data' in res:
                    data = res['data']
                    episodes = data.get('shortPlayEpisodeList') or []
                    return data, episodes
            else:
                print(f"      ⚠ Detail HTTP {r.status_code} (attempt {attempt}/5)")
        except Exception as e:
            print(f"      ⚠ Detail Connection error (attempt {attempt}/5): {e}")
        time.sleep(3)
    return None, []

def fetch_episode_url(mid, ep_no):
    url = f"https://vidrama.asia/api/netshort/api/watch/{mid}/{ep_no}?lang=in"
    hdrs = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36',
        'Referer': f'https://vidrama.asia/movie/slug--{mid}?provider=netshort&lang=in',
    }
    for attempt in range(1, 6):
        try:
            r = requests.get(url, headers=hdrs, verify=False, timeout=20)
            if r.ok:
                res = r.json()
                if res.get('success') and 'data' in res:
                    data = res['data']
                    return data.get('videoUrl'), data.get('subtitles') or []
            else:
                print(f"      ⚠ Ep Watch HTTP {r.status_code} (attempt {attempt}/5)")
        except Exception as e:
            print(f"      ⚠ Ep Watch Connection error (attempt {attempt}/5): {e}")
        time.sleep(2)
    return None, []

def download_and_transcode(mp4_url, ep_no):
    local_source = os.path.join(TEMP_DIR, f"source_ep{ep_no:03d}.mp4")
    local_720 = os.path.join(TEMP_DIR, f"ep{ep_no:03d}_720p.mp4")
    local_540 = os.path.join(TEMP_DIR, f"ep{ep_no:03d}_540p.mp4")
    
    for f in [local_source, local_720, local_540]:
        if os.path.exists(f): os.remove(f)
        
    hdrs = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36',
        'Referer': 'https://vidrama.asia/',
    }
    
    # 1. Download source MP4
    success_dl = False
    for attempt in range(1, 4):
        try:
            r = requests.get(mp4_url, headers=hdrs, verify=False, stream=True, timeout=120)
            if r.ok:
                with open(local_source, 'wb') as f:
                    for chunk in r.iter_content(chunk_size=1024*1024):
                        if chunk:
                            f.write(chunk)
                if os.path.exists(local_source) and os.path.getsize(local_source) > 1024*1024:
                    success_dl = True
                    break
            else:
                print(f"      ⚠ Source DL HTTP {r.status_code} (attempt {attempt}/3)")
        except Exception as e:
            print(f"      ⚠ Source DL Connection error (attempt {attempt}/3): {e}")
        time.sleep(3)
        
    if not success_dl:
        return None, None
        
    # 2. 720p copy & faststart
    success_720 = False
    for attempt in range(1, 4):
        cmd = [
            'ffmpeg', '-y',
            '-i', local_source,
            '-c', 'copy',
            '-movflags', '+faststart',
            '-loglevel', 'warning',
            local_720
        ]
        res = subprocess.run(cmd, capture_output=True, text=True, errors='ignore', timeout=180)
        if res.returncode == 0 and os.path.exists(local_720) and os.path.getsize(local_720) > 1024*1024:
            success_720 = True
            break
        else:
            print(f"      ⚠ 720p Attempt {attempt} failed: {res.stderr.strip()[-200:]}")
            if attempt < 3: time.sleep(3)
            
    if not success_720:
        if os.path.exists(local_source): os.remove(local_source)
        return None, None
        
    # 3. 540p scale & transcode
    success_540 = False
    for attempt in range(1, 4):
        cmd = [
            'ffmpeg', '-y',
            '-i', local_source,
            '-vf', 'scale=-2:540',
            '-c:v', 'libx264', '-crf', '26', '-preset', 'fast',
            '-maxrate', '1200k', '-bufsize', '2400k',
            '-c:a', 'aac', '-b:a', '96k',
            '-movflags', '+faststart',
            '-loglevel', 'warning',
            local_540
        ]
        res = subprocess.run(cmd, capture_output=True, text=True, errors='ignore', timeout=180)
        if res.returncode == 0 and os.path.exists(local_540) and os.path.getsize(local_540) > 500000:
            success_540 = True
            break
        else:
            print(f"      ⚠ 540p Attempt {attempt} failed: {res.stderr.strip()[-200:]}")
            if attempt < 3: time.sleep(3)
            
    # Cleanup source file
    if os.path.exists(local_source):
        os.remove(local_source)
        
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

def upload_cover(r2, cover_url, slug):
    key = f"dramas/{slug}/cover.jpg"
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

def get_or_register_drama(metadata, total_eps, slug, genres):
    title = metadata.get('shortPlayName')
    
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
    cover_url = metadata.get('shortPlayCover') or ''
    cover_r2 = upload_cover(r2, cover_url, slug)
    
    # Register new drama
    payload = {
        'title': title,
        'description': metadata.get('shortPlayDesc') or '',
        'cover': cover_r2,
        'genres': genres,
        'totalEpisodes': total_eps,
        'status': 'pending',
        'country': 'China',
        'language': 'Indonesia',
        'isActive': False,
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

def process_subtitles(r2, ep_id, ep_no, subtitles_list, slug):
    if not subtitles_list:
        return
        
    for sub in subtitles_list:
        lang = sub.get('lang') or sub.get('language') or ''
        raw_url = sub.get('url') or sub.get('src') or ''
        if not lang or not raw_url:
            continue
            
        # We prioritize id_ID / id
        if lang in ['id_ID', 'id']:
            db_lang = 'id'
            db_label = 'Bahasa Indonesia'
            is_default = True
        elif lang in ['en_US', 'en']:
            db_lang = 'en'
            db_label = 'English'
            is_default = False
        else:
            db_lang = lang.split('_')[0].lower()
            db_label = lang
            is_default = False
            
        r2_key = f"dramas/{slug}/ep{ep_no:03d}_{db_lang}.vtt"
        
        # Download raw subtitle content
        success_dl = False
        sub_content = None
        for attempt in range(1, 4):
            try:
                r = requests.get(raw_url, headers={'User-Agent': 'Mozilla/5.0'}, timeout=15, verify=False)
                if r.ok:
                    sub_content = r.content
                    success_dl = True
                    break
            except Exception as e:
                pass
            time.sleep(2)
            
        if not success_dl or not sub_content:
            print(f"      ❌ Failed to download subtitle for lang {lang}")
            continue
            
        # Upload to R2
        try:
            r2.put_object(Bucket=R2_BUCKET, Key=r2_key, Body=sub_content, ContentType='text/vtt')
            r2_url = f"{R2_PUBLIC}/{r2_key}"
            print(f"      ✓ Uploaded subtitle: {os.path.basename(r2_key)}")
            
            # Register in DB
            payload = {
                'language': db_lang,
                'label': db_label,
                'url': r2_url,
                'isDefault': is_default
            }
            r_sub = requests.post(f"{API_BASE}/api/episodes/{ep_id}/subtitles", headers=ADMIN_HDR, json=payload, timeout=15)
            if r_sub.ok:
                print(f"      ✓ Subtitle registered: {db_lang}")
            else:
                print(f"      ✗ Subtitle registration failed for {db_lang}: {r_sub.status_code} {r_sub.text}")
        except Exception as e:
            print(f"      ✗ Subtitle upload/DB register error: {e}")

def process_drama(r2, d):
    print("\n" + "=" * 65)
    print(f"🎬 STARTING INGESTION: {d['slug']} (ID: {d['id']})")
    print("=" * 65)
    
    # 1. Fetch metadata and episodes
    meta, eps_list = fetch_drama_details(d['id'])
    if not meta or not eps_list:
        print(f"❌ Failed to fetch drama details for {d['slug']}! Skipping.")
        return False
        
    total_eps = len(eps_list)
    print(f"   Drama Title: {meta.get('shortPlayName')}")
    print(f"   Total Episodes: {total_eps}")
    
    # 2. Get or Register Drama
    drama_id = get_or_register_drama(meta, total_eps, d['slug'], d['genres'])
    if not drama_id:
        print(f"❌ Failed to register drama {d['slug']}! Skipping.")
        return False
        
    # 3. Get existing episodes in DB
    done_eps = {}
    er = requests.get(f"{API_BASE}/api/dramas/{drama_id}/episodes", timeout=15)
    if er.ok:
        for ep in er.json():
            done_eps[int(ep.get('episodeNumber', 0))] = ep.get('id')
    print(f"   Already done in DB: {len(done_eps)} episodes")
    
    # 4. Ingest each episode
    success_count = 0
    fail_count = 0
    
    for ep in eps_list:
        ep_no = int(ep.get('episodeNo', 0))
        if not ep_no:
            continue
            
        print(f"\n   📺 Episode {ep_no}/{total_eps}:")
        
        # Fetch stream url and subtitles dynamically
        mp4_url, subs_list = fetch_episode_url(d['id'], ep_no)
        if not mp4_url:
            print(f"      ❌ Failed to fetch stream URL for EP {ep_no}")
            fail_count += 1
            continue
            
        if ep_no in done_eps:
            print("      ✓ Video already registered, checking subtitles...")
            ep_id = done_eps[ep_no]
            process_subtitles(r2, ep_id, ep_no, subs_list, d['slug'])
            success_count += 1
            continue
            
        r2_key_720 = f"dramas/{d['slug']}/ep{ep_no:03d}_720p.mp4"
        r2_key_540 = f"dramas/{d['slug']}/ep{ep_no:03d}_540p.mp4"
        
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
            local_720, local_540 = download_and_transcode(mp4_url, ep_no)
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
            print(f"      ✅ Video Done! ID: {ep_id}")
            process_subtitles(r2, ep_id, ep_no, subs_list, d['slug'])
            success_count += 1
            done_eps[ep_no] = ep_id
        else:
            print(f"      ❌ DB Registration failed for EP {ep_no}")
            fail_count += 1
            
        time.sleep(0.5)
        
    print("\n" + "=" * 65)
    print(f"🏁 INGESTION COMPLETE FOR {meta.get('shortPlayName')}!")
    print(f"   Success: {success_count}/{total_eps}")
    print(f"   Failed:  {fail_count}/{total_eps}")
    print("=" * 65)
    return True

def main():
    print("=" * 65)
    print("STARTING NETSHORT QUEUE PIPELINE")
    print(f"   Dramas to process: {len(DRAMAS)}")
    print("=" * 65)
    
    r2 = get_r2()
    
    for d in DRAMAS:
        try:
            process_drama(r2, d)
        except Exception as e:
            print(f"❌ Error processing drama {d['slug']}: {e}")
            
    print("\nALL NETSHORT DRAMAS IN QUEUE PROCESSED!")

if __name__ == '__main__':
    main()
