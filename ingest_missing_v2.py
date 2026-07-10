# -*- coding: utf-8 -*-
"""
Script to ingest missing netshortv2 episodes (47-59) for Orang yang Kunikahi Ternyata Idolaku.
This script runs on the VPS, scrapes stream URLs and subtitles from vidrama.asia,
downloads, transcodes to 720p/540p, uploads to Cloudflare R2, and registers in DB.
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

# ─── CONFIG ────────────────────────────────────────────────────────────────
API_BASE     = 'http://localhost:3000'
ADMIN_KEY    = '00ca04e3e2702be565d7bf44e783255247708289bce9b2fb6187a2e117f87fd14'
ADMIN_HDR    = {'x-admin-key': ADMIN_KEY, 'Content-Type': 'application/json'}

R2_ENDPOINT  = 'https://a142d3b29a5d64943cb251157e25eaf3.r2.cloudflarestorage.com'
R2_KEY_ID    = '07c99c897986ea52703c1285308d5e2c'
R2_SECRET    = '44788d376ffb216e1e73784b6fe1ff1423607928898a87c50819b52cdfc12e44'
R2_BUCKET    = 'shortlovers'
R2_PUBLIC    = 'https://stream.shortlovers.id'

TEMP_DIR     = '/tmp/temp_ingest_missing'
os.makedirs(TEMP_DIR, exist_ok=True)

DRAMA_ID_DB  = 'wfwqgc6f6scykh032uy5x554'
DRAMA_ID_SRC = '2030826923818483713'
SLUG         = 'orang-yang-kunikahi-ternyata-idolaku'

MISSING_EPS  = list(range(54, 60))

def get_r2():
    return boto3.client(
        's3', endpoint_url=R2_ENDPOINT,
        aws_access_key_id=R2_KEY_ID, aws_secret_access_key=R2_SECRET,
        config=Config(signature_version='s3v4'), region_name='auto'
    )

def fetch_episode_url(ep_no):
    url = f"https://vidrama.asia/api/netshortv2/episode/{DRAMA_ID_SRC}/{ep_no}?lang=id_ID"
    hdrs = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36',
        'Referer': f'https://vidrama.asia/en/watch/slug--{DRAMA_ID_SRC}/{ep_no}?provider=netshortv2',
    }
    for attempt in range(1, 6):
        try:
            r = requests.get(url, headers=hdrs, verify=False, timeout=20)
            if r.ok:
                res = r.json()
                if res.get('code') == 200 and 'data' in res:
                    data = res['data']
                    videos = data.get('videos') or []
                    subtitles = data.get('subtitles') or []
                    # Get the highest quality video URL
                    video_url = None
                    if videos:
                        # Find 720p or 1080p if possible, otherwise use last item
                        video_url = videos[-1].get('url')
                    return video_url, subtitles
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
    
    # 1. Download
    print(f"      📥 Downloading source video...")
    for attempt in range(1, 6):
        try:
            r = requests.get(mp4_url, stream=True, timeout=30, verify=False)
            if r.ok:
                with open(local_source, 'wb') as f:
                    for chunk in r.iter_content(chunk_size=1024*1024):
                        if chunk:
                            f.write(chunk)
                break
            else:
                print(f"         ⚠ Download status {r.status_code} (attempt {attempt}/5)")
        except Exception as e:
            print(f"         ⚠ Download exception (attempt {attempt}/5): {e}")
        time.sleep(3)
    else:
        print("      ❌ Failed to download source file after 5 attempts.")
        return None, None, 0
        
    # 2. Get duration
    duration = 0
    try:
        cmd_dur = [
            "ffprobe", "-v", "error", "-show_entries", "format=duration",
            "-of", "default=noprint_wrappers=1:nokey=1", local_source
        ]
        duration_str = subprocess.check_output(cmd_dur).decode('utf-8').strip()
        duration = int(round(float(duration_str)))
        print(f"      ⏱ Video duration: {duration} seconds")
    except Exception as e:
        print(f"      ⚠ Failed to get duration using ffprobe: {e}")
        duration = 0
        
    # 3. Transcode 720p (copy mux with faststart)
    print(f"      ⚡ Transcoding to 720p...")
    cmd_720 = [
        "ffmpeg", "-y", "-i", local_source,
        "-c", "copy", "-movflags", "+faststart", local_720
    ]
    try:
        subprocess.check_call(cmd_720, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    except Exception as e:
        print(f"      ⚠ copy-transcode failed, falling back to slow encoding: {e}")
        cmd_720_fallback = [
            "ffmpeg", "-y", "-i", local_source,
            "-c:v", "libx264", "-preset", "fast", "-crf", "22",
            "-c:a", "aac", "-b:a", "128k", "-movflags", "+faststart", local_720
        ]
        subprocess.check_call(cmd_720_fallback, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        
    # 4. Transcode 540p (scale to 540p width)
    print(f"      ⚡ Transcoding to 540p...")
    cmd_540 = [
        "ffmpeg", "-y", "-i", local_source,
        "-vf", "scale=-2:540", "-c:v", "libx264", "-preset", "fast", "-crf", "24",
        "-c:a", "aac", "-b:a", "96k", "-movflags", "+faststart", local_540
    ]
    try:
        subprocess.check_call(cmd_540, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    except Exception as e:
        print(f"      ❌ Failed to transcode 540p: {e}")
        return None, None, 0
        
    # Cleanup source
    if os.path.exists(local_source):
        os.remove(local_source)
        
    return local_720, local_540, duration

def download_subtitle(sub_url, ep_no):
    local_sub = os.path.join(TEMP_DIR, f"ep{ep_no:03d}_id_ID.vtt")
    for attempt in range(1, 6):
        try:
            r = requests.get(sub_url, timeout=15, verify=False)
            if r.ok:
                with open(local_sub, 'wb') as f:
                    f.write(r.content)
                return local_sub
        except Exception as e:
            print(f"         ⚠ Subtitle download exception (attempt {attempt}/5): {e}")
        time.sleep(2)
    return None

def main():
    r2 = get_r2()
    print("=================================================================")
    print(f"STARTING INGESTION FOR MISSING EPISODES OF: {SLUG}")
    print(f"Drama ID DB: {DRAMA_ID_DB}")
    print(f"Missing episodes: {MISSING_EPS}")
    print("=================================================================")
    
    for ep in MISSING_EPS:
        print(f"\n▶ Episode {ep}/{MISSING_EPS[-1]}:")
        
        # 1. Fetch source URLs
        video_url, subs = fetch_episode_url(ep)
        if not video_url:
            print(f"   ❌ Episode {ep} watch URL not found. Skipping.")
            continue
            
        print(f"   🔗 Source Video URL found: {video_url[:80]}...")
        
        # Find Indonesian subtitle URL
        sub_url = None
        for s in subs:
            if s.get('language') == 'id_ID':
                sub_url = s.get('url')
                break
                
        if sub_url:
            print(f"   🔗 Source Subtitle URL found: {sub_url[:80]}...")
            
        # 2. Download and transcode videos
        res_720, res_540, duration = download_and_transcode(video_url, ep)
        if not res_720 or not res_540:
            print(f"   ❌ Failed transcoding videos for Ep {ep}. Skipping DB registration.")
            continue
            
        # 3. Upload videos to R2
        r2_key_720 = f"dramas/netshort/{SLUG}/ep{ep:03d}.mp4"
        r2_key_540 = f"dramas/netshort/{SLUG}/ep{ep:03d}_540p.mp4"
        
        print(f"   📤 Uploading 720p to R2: {r2_key_720}")
        try:
            r2.upload_file(res_720, R2_BUCKET, r2_key_720)
            os.remove(res_720)
        except Exception as e:
            print(f"   ❌ Failed to upload 720p to R2: {e}")
            continue
            
        print(f"   📤 Uploading 540p to R2: {r2_key_540}")
        try:
            r2.upload_file(res_540, R2_BUCKET, r2_key_540)
            os.remove(res_540)
        except Exception as e:
            print(f"   ❌ Failed to upload 540p to R2: {e}")
            continue
            
        # 4. Upload subtitles to R2
        sub_uploaded = False
        r2_key_sub = f"dramas/netshort/{SLUG}/subs/ep{ep:03d}_id_ID.vtt"
        if sub_url:
            local_sub = download_subtitle(sub_url, ep)
            if local_sub:
                print(f"   📤 Uploading subtitles to R2: {r2_key_sub}")
                try:
                    r2.upload_file(local_sub, R2_BUCKET, r2_key_sub)
                    sub_uploaded = True
                    os.remove(local_sub)
                except Exception as e:
                    print(f"   ❌ Failed to upload subtitle to R2: {e}")
            else:
                print(f"   ⚠ Failed to download subtitle for Ep {ep}")
                
        # 5. Register episode to database
        db_video_url = f"{R2_PUBLIC}/{r2_key_720}"
        db_video_url_540 = f"{R2_PUBLIC}/{r2_key_540}"
        
        payload_ep = {
            "dramaId": DRAMA_ID_DB,
            "episodeNumber": ep,
            "title": f"Episode {ep}",
            "videoUrl": db_video_url,
            "videoUrl540p": db_video_url_540,
            "duration": duration
        }
        
        print(f"   📝 Registering episode to database...")
        ep_id = None
        for attempt in range(1, 6):
            try:
                r_reg = requests.post(f"{API_BASE}/api/episodes", json=payload_ep, headers=ADMIN_HDR, timeout=15)
                if r_reg.ok:
                    res_json = r_reg.json()
                    ep_id = res_json.get('id')
                    print(f"   ✅ Episode registered! ID: {ep_id}")
                    break
                else:
                    print(f"   ⚠ DB Episode register status {r_reg.status_code} (attempt {attempt}/5)")
            except Exception as e:
                print(f"   ⚠ DB Episode register error (attempt {attempt}/5): {e}")
            time.sleep(2)
            
        # 6. Register subtitle to database
        if ep_id and sub_uploaded:
            payload_sub = {
                "language": "id_ID",
                "label": "Indonesian",
                "url": f"{R2_PUBLIC}/{r2_key_sub}",
                "isDefault": True
            }
            print(f"   📝 Registering subtitle to database...")
            for attempt in range(1, 6):
                try:
                    r_sub = requests.post(f"{API_BASE}/api/episodes/{ep_id}/subtitles", json=payload_sub, headers=ADMIN_HDR, timeout=15)
                    if r_sub.ok:
                        print("   ✅ Subtitle registered successfully!")
                        break
                    else:
                        print(f"   ⚠ DB Subtitle register status {r_sub.status_code} (attempt {attempt}/5)")
                except Exception as e:
                    print(f"   ⚠ DB Subtitle register error (attempt {attempt}/5): {e}")
                time.sleep(2)
                
    print("\n=================================================================")
    print("INGESTION COMPLETED!")
    print("=================================================================")

if __name__ == '__main__':
    main()
