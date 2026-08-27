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

API_BASE     = 'http://141.11.160.187:3000'
ADMIN_KEY    = '00ca04e3e2702be565d7bf44e783255247708289bce9b2fb6187a2e117f87fd14'
ADMIN_HDR    = {'x-admin-key': ADMIN_KEY, 'Content-Type': 'application/json'}

R2_ENDPOINT  = 'https://a142d3b29a5d64943cb251157e25eaf3.r2.cloudflarestorage.com'
R2_KEY_ID    = '07c99c897986ea52703c1285308d5e2c'
R2_SECRET    = '44788d376ffb216e1e73784b6fe1ff1423607928898a87c50819b52cdfc12e44'
R2_BUCKET    = 'shortlovers'
R2_PUBLIC    = 'https://stream.shortlovers.id'

TEMP_DIR     = 'd:/kingshortid/temp_netshort_queue'
os.makedirs(TEMP_DIR, exist_ok=True)

def get_r2():
    return boto3.client(
        's3', endpoint_url=R2_ENDPOINT,
        aws_access_key_id=R2_KEY_ID, aws_secret_access_key=R2_SECRET,
        config=Config(signature_version='s3v4'), region_name='auto'
    )

def fetch_episode_url(mid, ep_no):
    url = f"https://vidrama.asia/api/netshort/api/watch/{mid}/{ep_no}?lang=in"
    hdrs = {'User-Agent': 'Mozilla/5.0'}
    for attempt in range(1, 6):
        try:
            r = requests.get(url, headers=hdrs, timeout=20, verify=False)
            if r.ok:
                res = r.json()
                if res.get('success') and 'data' in res:
                    data = res['data']
                    return data.get('videoUrl'), data.get('subtitles') or []
        except Exception as e:
            pass
        time.sleep(2)
    return None, []

def process_subtitles(r2, ep_id, ep_no, subtitles_list, slug):
    if not subtitles_list: return
    for sub in subtitles_list:
        lang = sub.get('lang') or sub.get('language') or ''
        raw_url = sub.get('url') or sub.get('src') or ''
        if not lang or not raw_url: continue
        
        db_lang, db_label, is_default = ('id', 'Indonesian', True)
        r2_key = f"dramas/{slug}/ep{ep_no:03d}_{db_lang}.vtt"
        
        sub_content = None
        for attempt in range(1, 4):
            try:
                r = requests.get(raw_url, headers={'User-Agent': 'Mozilla/5.0'}, timeout=15, verify=False)
                if r.ok:
                    sub_content = r.content
                    break
            except Exception:
                time.sleep(2)
        
        if not sub_content: continue
        
        try:
            r2.put_object(Bucket=R2_BUCKET, Key=r2_key, Body=sub_content, ContentType='text/vtt')
            r2_url = f"{R2_PUBLIC}/{r2_key}"
            
            payload = {
                'language': db_lang,
                'label': db_label,
                'url': r2_url,
                'isDefault': is_default
            }
            requests.post(f"{API_BASE}/api/episodes/{ep_id}/subtitles", headers=ADMIN_HDR, json=payload, timeout=15)
        except Exception:
            pass

def register_episode(drama_id, ep_no, url_720, url_540):
    payload = {
        'episodeNumber': ep_no,
        'title': f'Episode {ep_no}',
        'videoUrl': url_720 or url_540 or '',
        'videoUrl540p': url_540 or '',
        'isVip': False,
        'coinPrice': 0,
        'isActive': False,
    }
    r = requests.post(f"{API_BASE}/api/admin/dramas/{drama_id}/episodes", headers=ADMIN_HDR, json=payload, timeout=20)
    if r.ok: return r.json().get('id')
    r2 = requests.put(f"{API_BASE}/api/admin/dramas/{drama_id}/episodes/{ep_no}", headers=ADMIN_HDR, json=payload, timeout=20)
    if r2.ok: return r2.json().get('id') or 'updated'
    return None

def upload_to_r2(r2, local_path, r2_key):
    try:
        size_mb = os.path.getsize(local_path) / (1024*1024)
        with open(local_path, 'rb') as f:
            r2.upload_fileobj(f, R2_BUCKET, r2_key, ExtraArgs={'ContentType': 'video/mp4', 'CacheControl': 'public, max-age=31536000'})
        print(f"      Upload OK: {os.path.basename(r2_key)} ({size_mb:.1f} MB)")
        return f"{R2_PUBLIC}/{r2_key}"
    except Exception as e:
        print(f"      Upload failed: {e}")
        return None

def ingest_ep(r2, drama_id, slug, ep_no, force_reencode=False):
    print(f"\n   📺 Episode {ep_no}:")
    mp4_url, subs_list = fetch_episode_url(drama_id, ep_no)
    if not mp4_url:
        print(f"      ❌ Failed to fetch stream URL for EP {ep_no}")
        return False
        
    local_source = f"{TEMP_DIR}/source_ep{ep_no:03d}.mp4"
    local_720 = f"{TEMP_DIR}/ep{ep_no:03d}_720p.mp4"
    local_540 = f"{TEMP_DIR}/ep{ep_no:03d}_540p.mp4"
    r2_key_720 = f"dramas/{slug}/ep{ep_no:03d}_720p.mp4"
    r2_key_540 = f"dramas/{slug}/ep{ep_no:03d}_540p.mp4"
    
    # Download source
    success_dl = False
    for attempt in range(1, 4):
        try:
            r = requests.get(mp4_url, stream=True, timeout=30, verify=False)
            if r.ok:
                with open(local_source, 'wb') as f:
                    for chunk in r.iter_content(chunk_size=1024*1024):
                        if chunk: f.write(chunk)
                if os.path.getsize(local_source) > 100000:
                    success_dl = True
                    break
        except Exception:
            time.sleep(2)
            
    if not success_dl:
        print(f"      ❌ Failed to download source.")
        return False
        
    # ENCODE 720p with forced monotonic timestamps to fix looping/stuck
    print(f"      Encoding 720p...")
    cmd_720 = [
        'ffmpeg', '-y', '-i', local_source,
        '-vf', 'scale=720:-2', '-c:v', 'libx264', '-crf', '23', '-preset', 'fast',
        '-fps_mode', 'cfr', '-af', 'aresample=async=1', # Fix for looping/PTS errors
        '-maxrate', '1500k', '-bufsize', '3000k', '-c:a', 'aac', '-b:a', '128k',
        '-movflags', '+faststart', '-loglevel', 'warning', local_720
    ]
    subprocess.run(cmd_720)
    
    # ENCODE 540p
    print(f"      Encoding 540p...")
    cmd_540 = [
        'ffmpeg', '-y', '-i', local_source,
        '-vf', 'scale=540:-2', '-c:v', 'libx264', '-crf', '26', '-preset', 'fast',
        '-fps_mode', 'cfr', '-af', 'aresample=async=1',
        '-maxrate', '1000k', '-bufsize', '2000k', '-c:a', 'aac', '-b:a', '96k',
        '-movflags', '+faststart', '-loglevel', 'warning', local_540
    ]
    subprocess.run(cmd_540)
    
    # Upload
    url_720 = upload_to_r2(r2, local_720, r2_key_720)
    url_540 = upload_to_r2(r2, local_540, r2_key_540)
    
    # Register DB
    ep_id = register_episode('b1j1pw8qv6v2rdgrln9pmsz3', ep_no, url_720, url_540)
    if ep_id:
        print(f"      ✅ Video Done! ID: {ep_id}")
        process_subtitles(r2, ep_id, ep_no, subs_list, slug)
        
        # Cleanup
        for f in [local_source, local_720, local_540]:
            if os.path.exists(f): os.remove(f)
        return True
    else:
        print(f"      ❌ DB Registration failed.")
        return False

r2 = get_r2()
slug = 'master-pemancing'
drama_id = '2085184454048923649' # from vidrama

# 1. FIX EPISODE 9 (Re-encode and replace)
print("RE-ENCODING EPISODE 9 TO FIX LOOPING BUG...")
ingest_ep(r2, drama_id, slug, 9, force_reencode=True)

# 2. RESUME FROM EPISODE 52 TO 65
print("RESUMING EPISODES 52-65...")
for ep_no in range(52, 66):
    ingest_ep(r2, drama_id, slug, ep_no)

print("ALL DONE!")
