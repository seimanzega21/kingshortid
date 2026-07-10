# -*- coding: utf-8 -*-
"""
VPS-BASED PIPELINE: Sequential Queue for iDrama2 new dramas
"""
import requests
import boto3
import sys
import json
import time
import os
import re
import subprocess
import urllib3
from pathlib import Path
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

TEMP_DIR     = '/tmp/temp_idrama2_queue'
os.makedirs(TEMP_DIR, exist_ok=True)

def get_r2():
    return boto3.client(
        's3', endpoint_url=R2_ENDPOINT,
        aws_access_key_id=R2_KEY_ID, aws_secret_access_key=R2_SECRET,
        config=Config(signature_version='s3v4'), region_name='auto'
    )

def make_slug(title):
    s = title.strip().lower()
    s = s.replace("(dubbing)", "")
    s = s.replace("(sulih suara)", "")
    s = re.sub(r'[^\w\s-]', '', s)
    s = re.sub(r'[-\s]+', '-', s)
    return s.strip('-')

def srt_to_vtt(srt_text):
    if srt_text.strip().startswith('WEBVTT'):
        return srt_text
    lines = srt_text.splitlines()
    vtt_lines = ['WEBVTT', '']
    timestamp_re = re.compile(r'(\d{2}:\d{2}:\d{2}),(\d{3})\s*-->\s*(\d{2}:\d{2}:\d{2}),(\d{3})')
    for line in lines:
        match = timestamp_re.search(line)
        if match:
            formatted_line = line.replace(',', '.')
            vtt_lines.append(formatted_line)
        else:
            vtt_lines.append(line)
    return '\n'.join(vtt_lines)

def upload_cover_to_r2(r2, cover_url, slug):
    if not cover_url:
        return ""
    # We must convert the cover to JPEG murni as per user rule
    local_raw = os.path.join(TEMP_DIR, f"{slug}_cover_raw")
    local_jpg = os.path.join(TEMP_DIR, f"{slug}_cover_hq.jpg")
    try:
        # Download
        r = requests.get(cover_url, headers=HEADERS, timeout=20, verify=False)
        if not r.ok:
            return ""
        with open(local_raw, 'wb') as f:
            f.write(r.content)
            
        # Convert using ffmpeg -update 1
        cmd = ["ffmpeg", "-y", "-i", local_raw, "-update", "1", local_jpg]
        subprocess.run(cmd, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        
        # Upload
        r2_key = f"dramas/covers/{slug}_cover_hq.jpg"
        r2.upload_file(local_jpg, R2_BUCKET, r2_key, ExtraArgs={
            'ContentType': 'image/jpeg',
            'CacheControl': 'public, max-age=31536000'
        })
        
        # Cleanup
        for p in [local_raw, local_jpg]:
            if os.path.exists(p):
                os.remove(p)
                
        return f"{R2_PUBLIC}/{r2_key}"
    except Exception as e:
        print(f"      ⚠ Cover processing failed: {e}")
        return ""

def get_or_register_drama(r2, upstream_id, title, genres, meta):
    # Check if exists by title
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
                    # Make sure it is active as per user rule
                    if not d.get('isActive'):
                        requests.post(f"{API_BASE}/admin/dramas", headers=ADMIN_HDR, json={'id': db_id, 'isActive': True}, timeout=10)
                    return db_id
    except Exception as e:
        print(f"      ⚠ DB duplicate check failed: {e}")

    # Process cover art
    cover_raw = meta.get('cover_url')
    slug = make_slug(title)
    r2_cover = upload_cover_to_r2(r2, cover_raw, slug)
    
    # Register in DB
    payload = {
        'title': title,
        'description': meta.get('introduction', '') or 'No description available',
        'cover': r2_cover,
        'genres': genres,
        'totalEpisodes': meta.get('current_count', 0) or len(meta.get('episode_list', [])),
        'status': 'ongoing',
        'country': 'China',
        'language': 'Indonesia',
        'isActive': True,  # MUST BE TRUE as per user rule!
        'isVip': False
    }
    
    try:
        r = requests.post(f"{API_BASE}/admin/dramas", headers=ADMIN_HDR, json=payload, timeout=30)
        if r.ok:
            return r.json().get('id')
        else:
            print(f"      ❌ Failed to register drama. Status: {r.status_code}, Body: {r.text[:200]}")
    except Exception as e:
        print(f"      ❌ Drama registration exception: {e}")
        
    return None

def download_m3u8_stream(m3u8_url, local_path):
    headers_str = f"Referer: https://vidrama.asia/\r\nUser-Agent: {HEADERS['User-Agent']}\r\n"
    cmd = [
        'ffmpeg', '-y',
        '-headers', headers_str,
        '-i', m3u8_url,
        '-c:v', 'libx264', '-crf', '26',
        '-preset', 'fast',
        '-maxrate', '1500k', '-bufsize', '3000k',
        '-c:a', 'aac', '-b:a', '128k',
        '-movflags', '+faststart',
        '-loglevel', 'error',
        str(local_path)
    ]
    res = subprocess.run(cmd, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    return res.returncode == 0

def downscale_to_540p(input_path, output_path):
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
    res = subprocess.run(cmd, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    return res.returncode == 0

def process_drama(r2, drama):
    upstream_id = drama['id']
    title = drama['title']
    genres = drama['genres']
    
    print("\n" + "=" * 60)
    print(f"🎬 STARTING INGESTION: {title} (ID: {upstream_id})")
    print("=" * 60)
    
    # 1. Fetch details
    meta_url = f"https://vidrama.asia/api/idrama2/drama/{upstream_id}?lang=id"
    meta = None
    for attempt in range(1, 6):
        try:
            r = requests.get(meta_url, headers=HEADERS, verify=False, timeout=20)
            if r.ok:
                meta = r.json()
                break
        except Exception as e:
            print(f"   ⚠ Metadata fetch error (attempt {attempt}/5): {e}")
        time.sleep(2)
        
    if not meta:
        print("   ❌ Failed to fetch metadata. Skipping.")
        return False
        
    # Standardize Title
    raw_title = meta.get('short_play_name', '').strip()
    if "(Sulih Suara)" in raw_title:
        search_title = raw_title
    else:
        tags = [t.get('tag_local', '').lower() for t in meta.get('content_tag', [])]
        if 'sulih suara' in tags or 'dubbed' in tags or 'dubbing' in tags:
            search_title = f"(Sulih Suara) {raw_title}"
        else:
            search_title = raw_title
            
    slug = make_slug(search_title)
    
    # 2. Get or register drama
    drama_db_id = get_or_register_drama(r2, upstream_id, search_title, genres, meta)
    if not drama_db_id:
        print("   ❌ Failed to get/register drama in DB. Skipping.")
        return False
        
    print(f"   ✅ Drama registered in DB: {drama_db_id}")
    
    # Get registered episodes
    done_eps = set()
    try:
        url = f"{API_BASE}/dramas/{drama_db_id}/episodes?includeInactive=true"
        r_eps = requests.get(url, timeout=15)
        if r_eps.ok:
            eps_list = r_eps.json()
            done_eps = {e.get('episodeNumber') for e in eps_list}
    except Exception as e:
        print(f"   ⚠ Failed to fetch registered episodes: {e}")
        
    print(f"   Already done: {len(done_eps)} episodes")
    
    episode_list = meta.get('episode_list') or []
    
    for ep in episode_list:
        ep_no = ep.get('episode_order') or 1
        if ep_no in done_eps:
            # Skip video, just verify if active
            continue
            
        print(f"\n   ▶ Episode {ep_no}/{len(episode_list)}:")
        
        # Call unlock API to get HLS stream URL and subtitles
        unlock_url = f"https://vidrama.asia/api/idrama2/unlock/{upstream_id}/{ep_no}?lang=id"
        unlock_info = None
        for attempt in range(1, 6):
            try:
                r_ul = requests.get(unlock_url, headers=HEADERS, verify=False, timeout=20)
                if r_ul.ok:
                    unlock_info = r_ul.json().get('target_ep_info') or {}
                    break
            except Exception as e:
                print(f"      ⚠ Unlock API error (attempt {attempt}/5): {e}")
            time.sleep(2)
            
        if not unlock_info:
            print(f"      ❌ Failed to get unlock info for Ep {ep_no}. Skipping.")
            continue
            
        m3u8_url = unlock_info.get('play_url')
        if not m3u8_url:
            print(f"      ❌ No stream URL found for Ep {ep_no}. Skipping.")
            continue
            
        # Check subtitles
        subs = unlock_info.get('subtitle_list') or unlock_info.get('screentext_list') or []
        sub_url = None
        for s in subs:
            if s.get('language') == 'id':
                sub_url = s.get('url')
                break
                
        # Download and transcode
        out_720_local = os.path.join(TEMP_DIR, f"{slug}_ep{ep_no:03d}_720.mp4")
        out_540_local = os.path.join(TEMP_DIR, f"{slug}_ep{ep_no:03d}_540.mp4")
        
        # Download/transcode HLS to 720p local file
        print("      📥 Downloading and transcoding HLS to 720p...")
        success_dl = False
        for attempt in range(1, 4):
            if download_m3u8_stream(m3u8_url, out_720_local):
                if os.path.exists(out_720_local) and os.path.getsize(out_720_local) > 1024*1024:
                    success_dl = True
                    break
            print(f"         ⚠ 720p download attempt {attempt} failed.")
            time.sleep(3)
            
        if not success_dl:
            print("      ❌ Failed to download/transcode 720p MP4. Skipping.")
            continue
            
        # Get duration
        duration = 0
        try:
            cmd_dur = [
                "ffprobe", "-v", "error", "-show_entries", "format=duration",
                "-of", "default=noprint_wrappers=1:nokey=1", out_720_local
            ]
            duration_str = subprocess.check_output(cmd_dur).decode('utf-8').strip()
            duration = int(round(float(duration_str)))
        except Exception as e:
            print(f"      ⚠ Duration check failed: {e}")
            
        # Transcode 540p
        print("      ⚡ Transcoding 540p...")
        success_540 = False
        for attempt in range(1, 4):
            if downscale_to_540p(out_720_local, out_540_local):
                if os.path.exists(out_540_local) and os.path.getsize(out_540_local) > 500000:
                    success_540 = True
                    break
            print(f"         ⚠ 540p transcode attempt {attempt} failed.")
            time.sleep(3)
            
        if not success_540:
            print("      ❌ Failed to transcode 540p MP4. Skipping.")
            if os.path.exists(out_720_local): os.remove(out_720_local)
            continue
            
        # Upload to R2
        r2_key_720 = f"dramas/netshort/{slug}/ep{ep_no:03d}.mp4"
        r2_key_540 = f"dramas/netshort/{slug}/ep{ep_no:03d}_540p.mp4"
        
        print(f"      📤 Uploading 720p: {r2_key_720}")
        try:
            r2.upload_file(out_720_local, R2_BUCKET, r2_key_720, ExtraArgs={'ContentType': 'video/mp4'})
            os.remove(out_720_local)
        except Exception as e:
            print(f"      ❌ Upload 720p failed: {e}")
            continue
            
        print(f"      📤 Uploading 540p: {r2_key_540}")
        try:
            r2.upload_file(out_540_local, R2_BUCKET, r2_key_540, ExtraArgs={'ContentType': 'video/mp4'})
            os.remove(out_540_local)
        except Exception as e:
            print(f"      ❌ Upload 540p failed: {e}")
            continue
            
        # Download and upload subtitle
        sub_uploaded = False
        r2_key_sub = f"dramas/netshort/{slug}/subs/ep{ep_no:03d}_id.vtt"
        if sub_url:
            print("      📥 Fetching subtitles...")
            try:
                r_sub = requests.get(sub_url, headers=HEADERS, verify=False, timeout=15)
                if r_sub.ok:
                    vtt_text = srt_to_vtt(r_sub.text)
                    r2.put_object(Bucket=R2_BUCKET, Key=r2_key_sub, Body=vtt_text.encode('utf-8'), ContentType='text/vtt')
                    sub_uploaded = True
            except Exception as e:
                print(f"      ⚠ Subtitle fetch/upload failed: {e}")
                
        # Register in DB
        payload_ep = {
            'episodeNumber': ep_no,
            'title': f'Episode {ep_no}',
            'videoUrl': f"{R2_PUBLIC}/{r2_key_720}",
            'videoUrl540p': f"{R2_PUBLIC}/{r2_key_540}",
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
            
        # Register subtitle in DB
        if ep_db_id and sub_uploaded:
            payload_sub = {
                'language': 'id',
                'label': 'Bahasa Indonesia',
                'url': f"{R2_PUBLIC}/{r2_key_sub}",
                'isDefault': True
            }
            for attempt in range(1, 6):
                try:
                    r_sub_reg = requests.post(f"{API_BASE}/episodes/{ep_db_id}/subtitles", headers=ADMIN_HDR, json=payload_sub, timeout=15)
                    if r_sub_reg.ok:
                        print("      ✅ Subtitle registered in DB!")
                        break
                except Exception as e:
                    print(f"      ⚠ Subtitle DB register failed: {e}")
                time.sleep(2)
                
    return True

def main():
    r2 = get_r2()
    
    # Read list of new dramas
    json_path = '/tmp/new_idrama2_dramas.json'
    if not os.path.exists(json_path):
        print(f"Error: {json_path} not found.")
        return
        
    with open(json_path, 'r', encoding='utf-8') as f:
        dramas = json.load(f)
        
    print("=================================================================")
    print(f"STARTING IDRAMA2 QUEUE PIPELINE: {len(dramas)} dramas to process")
    print("=================================================================")
    
    for idx, drama in enumerate(dramas, 1):
        print(f"\nProcessing drama {idx}/{len(dramas)}")
        try:
            process_drama(r2, drama)
        except Exception as e:
            print(f"❌ Uncaught exception for drama {drama.get('title')}: {e}")
            
    print("\n=================================================================")
    print("ALL IDRAMA2 QUEUE PROCESS COMPLETED!")
    print("=================================================================")

if __name__ == '__main__':
    main()
