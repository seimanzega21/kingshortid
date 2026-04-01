import os, subprocess, sys, requests, json
import boto3
from botocore.config import Config
from pathlib import Path

# =================CONFIGURATION=================
# API Base URL — no database connection needed!
API_BASE     = 'https://api.shortlovers.id'
ADMIN_KEY    = '00ca04e3e2702be565d7bf44e783255247708289bce9b2fb6187a2e117f87fd14'

R2_ENDPOINT  = 'https://a142d3b29a5d64943cb251157e25eaf3.r2.cloudflarestorage.com'
R2_KEY_ID    = '07c99c897986ea52703c1285308d5e2c'
R2_SECRET    = '44788d376ffb216e1e73784b6fe1ff1423607928898a87c50819b52cdfc12e44'
R2_BUCKET    = 'shortlovers'
R2_PUBLIC    = 'https://stream.shortlovers.id'

TEMP_DIR = Path('/tmp/video_backfill')
TEMP_DIR.mkdir(exist_ok=True)
# ===============================================

HEADERS = {'x-admin-key': ADMIN_KEY, 'Content-Type': 'application/json'}

def get_r2():
    return boto3.client('s3', endpoint_url=R2_ENDPOINT,
                        aws_access_key_id=R2_KEY_ID, aws_secret_access_key=R2_SECRET,
                        config=Config(signature_version='s3v4'), region_name='auto')

def r2_upload(r2c, path, key):
    with open(path, 'rb') as f:
        r2c.upload_fileobj(f, R2_BUCKET, key,
                           ExtraArgs={'ContentType': 'video/mp4'},
                           Config=boto3.s3.transfer.TransferConfig(
                               multipart_threshold=30*1024*1024,
                               multipart_chunksize=10*1024*1024))

def convert_video(input_url, temp_720, temp_540):
    cmd_720 = ['ffmpeg', '-y', '-i', input_url]
    if '.m3u8' in input_url:
        cmd_720 += ['-c', 'copy', '-bsf:a', 'aac_adtstoasc', '-movflags', '+faststart', str(temp_720)]
    else:
        cmd_720 += ['-c', 'copy', '-movflags', '+faststart', str(temp_720)]
    res1 = subprocess.run(cmd_720, capture_output=True, text=True, timeout=1200)
    if res1.returncode != 0 or not temp_720.exists():
        print(f"FFmpeg 720p error: {res1.stderr[-300:]}")
        return False

    cmd_540 = ['ffmpeg', '-y', '-i', str(temp_720),
               '-vf', 'scale=-2:540', '-c:v', 'libx264', '-crf', '28', '-preset', 'fast',
               '-c:a', 'aac', '-b:a', '128k', '-movflags', '+faststart', str(temp_540)]
    res2 = subprocess.run(cmd_540, capture_output=True, text=True, timeout=1200)
    if res2.returncode != 0 or not temp_540.exists():
        print(f"FFmpeg 540p error: {res2.stderr[-300:]}")
        return False
    return True

def get_prefix_from_cover(cover_url, drama_id):
    if not cover_url or cover_url.startswith('/api/uploads') or cover_url.startswith('https://admin'):
        return f"converted/{drama_id}"
    parsed = cover_url.replace(R2_PUBLIC + "/", "")
    for ext in ["cover.webp", "cover.jpg", "cover.png"]:
        parsed = parsed.replace(ext, "")
    parsed = parsed.strip('/')
    return parsed if parsed else f"converted/{drama_id}"

def fetch_external_dramas():
    """Fetch all dramas that have at least one external episode via API."""
    print("Fetching drama list from API...")
    resp = requests.get(f"{API_BASE}/api/dramas?page=1&limit=200", timeout=30)
    resp.raise_for_status()
    data = resp.json()
    dramas = data.get('dramas', data.get('data', []))
    print(f"  Found {len(dramas)} total dramas. Checking each for external episodes...")
    return dramas

def fetch_episodes_for_drama(drama_id):
    resp = requests.get(f"{API_BASE}/api/dramas/{drama_id}", timeout=30)
    if not resp.ok:
        return []
    data = resp.json()
    return data.get('episodes', [])

def patch_episode(ep_id, url_720, url_540):
    resp = requests.patch(
        f"{API_BASE}/api/episodes/{ep_id}",
        headers=HEADERS,
        json={"videoUrl": url_720, "videoUrl540p": url_540},
        timeout=30
    )
    return resp.ok

def run_migration():
    r2c = get_r2()
    dramas = fetch_external_dramas()
    
    total_success, total_failed = 0, 0

    for drama in dramas:
        drama_id = drama.get('id')
        drama_title = drama.get('title', '?')
        cover_url = drama.get('cover', '')
        
        episodes = fetch_episodes_for_drama(drama_id)
        external = [ep for ep in episodes
                    if ep.get('videoUrl') and
                    'shortlovers.id' not in ep.get('videoUrl', '') and
                    'r2.' not in ep.get('videoUrl', '')]
        
        if not external:
            continue
        
        print(f"\n[Drama] {drama_title} — {len(external)} external episodes to migrate")
        prefix = get_prefix_from_cover(cover_url, drama_id)
        
        for i, ep in enumerate(external):
            ep_id   = ep.get('id')
            ep_num  = ep.get('episodeNumber', i+1)
            video_url = ep.get('videoUrl')
            
            key_720 = f"{prefix}/ep{ep_num:03d}.mp4"
            key_540 = f"{prefix}/ep{ep_num:03d}_540p.mp4"
            url_720 = f"{R2_PUBLIC}/{key_720}"
            url_540 = f"{R2_PUBLIC}/{key_540}"
            
            print(f"  [{i+1}/{len(external)}] Ep {ep_num}... ", end='', flush=True)
            
            t_720 = TEMP_DIR / f"tmp_720_{ep_id}.mp4"
            t_540 = TEMP_DIR / f"tmp_540_{ep_id}.mp4"
            
            try:
                if convert_video(video_url, t_720, t_540):
                    print("Encoded. Uploading... ", end='', flush=True)
                    r2_upload(r2c, t_720, key_720)
                    r2_upload(r2c, t_540, key_540)
                    
                    if patch_episode(ep_id, url_720, url_540):
                        print("API OK ✓")
                        total_success += 1
                    else:
                        print("API PATCH FAILED!")
                        total_failed += 1
                else:
                    print("FFmpeg FAILED!")
                    total_failed += 1
            except Exception as e:
                print(f"ERROR: {e}")
                total_failed += 1
            finally:
                if t_720.exists(): t_720.unlink()
                if t_540.exists(): t_540.unlink()

    print(f"\n{'='*40}")
    print(f"MIGRATION COMPLETE! Success: {total_success} | Failed: {total_failed}")

if __name__ == '__main__':
    run_migration()
