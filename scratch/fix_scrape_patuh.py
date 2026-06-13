# -*- coding: utf-8 -*-
"""
Fix scraper for: Aku Terlahir Terlalu Patuh (ID: lsr7c0n1qxnrfse46j86n88e)
- EP 1-21 sudah ada di DB tapi mungkin TANPA subtitle -> patch subtitle
- EP 22+ belum ada -> download, encode, upload, register dengan subtitle
"""
import sys
sys.stdout.reconfigure(encoding='utf-8')

import requests
import boto3
import json
import time
import re
import subprocess
import warnings
warnings.filterwarnings('ignore')
from pathlib import Path
from botocore.config import Config

API_BASE    = 'https://api.shortlovers.id/api'
ADMIN_KEY   = '00ca04e3e2702be565d7bf44e783255247708289bce9b2fb6187a2e117f87fd14'
ADMIN_HDR   = {'x-admin-key': ADMIN_KEY, 'Content-Type': 'application/json'}

R2_ENDPOINT = 'https://a142d3b29a5d64943cb251157e25eaf3.r2.cloudflarestorage.com'
R2_KEY_ID   = '07c99c897986ea52703c1285308d5e2c'
R2_SECRET   = '44788d376ffb216e1e73784b6fe1ff1423607928898a87c50819b52cdfc12e44'
R2_BUCKET   = 'shortlovers'
R2_PUBLIC   = 'https://stream.shortlovers.id'

HEADERS = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36',
    'Referer': 'https://vidrama.asia/',
}

UPSTREAM_ID = '160000641860'
DRAMA_DB_ID = 'lsr7c0n1qxnrfse46j86n88e'  # Already registered
SLUG        = 'aku-terlahir-terlalu-patuh'
WORKSPACE   = Path(__file__).resolve().parent.parent
TEMP_DIR    = WORKSPACE / 'temp_patuh'
TEMP_DIR.mkdir(exist_ok=True)
LOG_FILE    = WORKSPACE / 'scratch' / 'fix_patuh2.log'

def log(msg):
    ts = time.strftime('%Y-%m-%d %H:%M:%S')
    full = f"[{ts}] {msg}"
    print(full, flush=True)
    with open(LOG_FILE, 'a', encoding='utf-8') as f:
        f.write(full + '\n')

def get_r2():
    return boto3.client(
        's3', endpoint_url=R2_ENDPOINT,
        aws_access_key_id=R2_KEY_ID, aws_secret_access_key=R2_SECRET,
        config=Config(signature_version='s3v4'), region_name='auto'
    )

def get_episodes_from_db():
    """Returns dict: ep_no -> {id, subtitles: [...]}"""
    r = requests.get(f"{API_BASE}/dramas/{DRAMA_DB_ID}/episodes?includeInactive=true", timeout=15)
    if not r.ok:
        return {}
    eps = r.json()
    ep_list = eps if isinstance(eps, list) else eps.get('episodes', eps.get('data', []))
    result = {}
    for e in ep_list:
        ep_no = e.get('episodeNumber')
        if ep_no:
            result[ep_no] = {'id': e.get('id'), 'subtitles': e.get('subtitles', [])}
    return result

def get_episode_subtitles(ep_db_id):
    """Check if episode already has subtitles in DB"""
    r = requests.get(f"{API_BASE}/episodes/{ep_db_id}/subtitles", timeout=10)
    if r.ok:
        data = r.json()
        return data if isinstance(data, list) else data.get('subtitles', [])
    return []

def fetch_unlock(ep_no, retries=5):
    for attempt in range(retries):
        try:
            url = f"https://vidrama.asia/api/idrama2/unlock/{UPSTREAM_ID}/{ep_no}?lang=id"
            resp = requests.get(url, headers=HEADERS, verify=False, timeout=20)
            if resp.ok:
                info = resp.json().get('target_ep_info', {})
                if info and info.get('play_url'):
                    return info
        except Exception as e:
            log(f"    Unlock attempt {attempt+1}: {e}")
        time.sleep(5)
    return {}

def get_id_subtitle(unlock_info):
    all_subs = list(unlock_info.get('screentext_list') or []) + list(unlock_info.get('subtitle_list') or [])
    for s in all_subs:
        if s.get('language', '').lower() == 'id' and s.get('url'):
            return s['url']
    return None

def upload_subtitle(r2, sub_url, ep_no):
    sub_resp = requests.get(sub_url, headers=HEADERS, timeout=15, verify=False)
    if sub_resp.ok:
        key = f"dramas/{SLUG}/ep{ep_no:03d}_id.vtt"
        r2.put_object(Bucket=R2_BUCKET, Key=key, Body=sub_resp.content, ContentType='text/vtt')
        return f"{R2_PUBLIC}/{key}"
    return None

def register_subtitle(ep_db_id, sub_r2_url):
    payload = {
        'language': 'id',
        'label': 'Bahasa Indonesia',
        'url': sub_r2_url,
        'isDefault': True
    }
    r = requests.post(f"{API_BASE}/episodes/{ep_db_id}/subtitles", headers=ADMIN_HDR, json=payload, timeout=15)
    return r.ok

def transcode_720p(m3u8_url, out_path):
    headers_str = f"Referer: https://vidrama.asia/\r\nUser-Agent: {HEADERS['User-Agent']}\r\n"
    cmd = [
        'ffmpeg', '-y', '-headers', headers_str,
        '-i', m3u8_url,
        '-c:v', 'libx264', '-crf', '26', '-preset', 'fast',
        '-maxrate', '1500k', '-bufsize', '3000k',
        '-c:a', 'aac', '-b:a', '128k',
        '-movflags', '+faststart',
        '-loglevel', 'error', str(out_path)
    ]
    return subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE).returncode == 0

def downscale_540p(inp, out):
    cmd = [
        'ffmpeg', '-y', '-i', str(inp),
        '-vf', 'scale=-2:540',
        '-c:v', 'libx264', '-crf', '28', '-preset', 'fast',
        '-c:a', 'aac', '-b:a', '96k',
        '-movflags', '+faststart',
        '-loglevel', 'error', str(out)
    ]
    return subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE).returncode == 0

def upload_video(r2, path, key):
    r2.upload_file(str(path), R2_BUCKET, key, ExtraArgs={
        'ContentType': 'video/mp4', 'CacheControl': 'public, max-age=31536000'
    })
    return f"{R2_PUBLIC}/{key}"

def register_episode(ep_no, url_720, url_540):
    payload = {
        'episodeNumber': ep_no,
        'title': f'Episode {ep_no}',
        'videoUrl': url_720,
        'videoUrl540p': url_540,
        'isVip': False, 'coinPrice': 0, 'isActive': True
    }
    r = requests.post(f"{API_BASE}/admin/dramas/{DRAMA_DB_ID}/episodes", headers=ADMIN_HDR, json=payload, timeout=20)
    if r.ok:
        return r.json().get('id')
    return None

def main():
    with open(LOG_FILE, 'w', encoding='utf-8') as f:
        f.write("--- FIX PATUH v2 ---\n")

    log("=" * 60)
    log("FIX v2: Aku Terlahir Terlalu Patuh")
    log(f"Drama DB ID: {DRAMA_DB_ID}")
    log("=" * 60)

    r2 = get_r2()

    # Fetch total episodes from upstream
    meta = requests.get(f"https://vidrama.asia/api/idrama2/drama/{UPSTREAM_ID}?lang=id",
                        headers=HEADERS, verify=False, timeout=20).json()
    total_eps = meta.get('current_count', 75)
    log(f"Total upstream episodes: {total_eps}")

    # Get existing DB episodes
    db_eps = get_episodes_from_db()
    log(f"DB episodes found: {sorted(db_eps.keys())}")

    # === PHASE 1: Patch subtitles for existing episodes (1-21) ===
    log("\n--- PHASE 1: Patching subtitles for existing episodes ---")
    for ep_no in sorted(db_eps.keys()):
        ep_info = db_eps[ep_no]
        ep_db_id = ep_info['id']

        # Check if subtitle already registered
        existing_subs = get_episode_subtitles(ep_db_id)
        has_id_sub = any(s.get('language') == 'id' for s in existing_subs)

        if has_id_sub:
            log(f"  EP {ep_no}: subtitle already OK, skip")
            continue

        log(f"  EP {ep_no}: no subtitle found, fetching from upstream...")
        unlock_info = fetch_unlock(ep_no)
        if not unlock_info:
            log(f"  EP {ep_no}: [ERROR] unlock failed")
            continue

        sub_upstream_url = get_id_subtitle(unlock_info)
        if not sub_upstream_url:
            log(f"  EP {ep_no}: [WARN] no ID subtitle in upstream")
            continue

        r2_sub_url = upload_subtitle(r2, sub_upstream_url, ep_no)
        if not r2_sub_url:
            log(f"  EP {ep_no}: [ERROR] subtitle upload failed")
            continue

        ok = register_subtitle(ep_db_id, r2_sub_url)
        log(f"  EP {ep_no}: subtitle registered = {ok} -> {r2_sub_url}")
        time.sleep(1)

    # === PHASE 2: Process remaining episodes ===
    log("\n--- PHASE 2: Processing remaining episodes ---")
    for ep_no in range(1, total_eps + 1):
        if ep_no in db_eps:
            continue

        log(f"\n  EP {ep_no}/{total_eps}:")

        unlock_info = fetch_unlock(ep_no)
        if not unlock_info.get('play_url'):
            log(f"    [ERROR] No play_url for EP {ep_no}, skip")
            continue

        m3u8 = unlock_info['play_url']
        sub_upstream_url = get_id_subtitle(unlock_info)
        log(f"    Subtitle ID: {'FOUND' if sub_upstream_url else 'MISSING'}")

        out_720 = TEMP_DIR / f"patuh_ep{ep_no:03d}_720p.mp4"
        out_540 = TEMP_DIR / f"patuh_ep{ep_no:03d}_540p.mp4"

        try:
            log("    Transcoding 720p...")
            t0 = time.time()
            if not transcode_720p(m3u8, out_720):
                log("    [ERROR] 720p failed")
                continue
            log(f"    [OK] 720p: {out_720.stat().st_size/1024/1024:.1f}MB ({time.time()-t0:.0f}s)")

            log("    Downscaling 540p...")
            t0 = time.time()
            if not downscale_540p(out_720, out_540):
                log("    [ERROR] 540p failed")
                continue
            log(f"    [OK] 540p: {out_540.stat().st_size/1024/1024:.1f}MB ({time.time()-t0:.0f}s)")

            log("    Uploading to R2...")
            url_720 = upload_video(r2, out_720, f"dramas/{SLUG}/ep{ep_no:03d}_720p.mp4")
            url_540 = upload_video(r2, out_540, f"dramas/{SLUG}/ep{ep_no:03d}_540p.mp4")

            r2_sub_url = None
            if sub_upstream_url:
                r2_sub_url = upload_subtitle(r2, sub_upstream_url, ep_no)
                if r2_sub_url:
                    log(f"    [OK] Subtitle: {r2_sub_url}")

            ep_id = register_episode(ep_no, url_720, url_540)
            if ep_id:
                log(f"    [OK] EP {ep_no} registered: {ep_id}")
                if r2_sub_url:
                    ok = register_subtitle(ep_id, r2_sub_url)
                    log(f"    [OK] Subtitle linked: {ok}")
            else:
                log(f"    [ERROR] EP {ep_no} DB register failed")

        except Exception as e:
            log(f"    [ERROR] EP {ep_no}: {e}")
        finally:
            for p in [out_720, out_540]:
                if p.exists():
                    try: p.unlink()
                    except: pass

        time.sleep(1.0)

    log("\n" + "=" * 60)
    log("COMPLETE: Aku Terlahir Terlalu Patuh")
    log("=" * 60)

if __name__ == '__main__':
    main()
