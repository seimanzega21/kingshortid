#!/usr/bin/env python3
"""
Re-scrape specific episodes of a drama that have wrong subtitle language.
Usage: python rescrape_episodes.py
"""
import requests, json, re, os, sys, subprocess, time, boto3
from pathlib import Path
from dotenv import load_dotenv

sys.stdout.reconfigure(encoding='utf-8')
load_dotenv()

# ── CONFIG ──
DRAMA_ID      = '2016783678950682625'
DRAMA_TITLE   = 'Putri Asli Kembali, Membalas Semuanya'
DRAMA_SLUG    = 'putri-asli-kembali-membalas-semuanya'  # generated slug
TARGET_EPISODES = [3, 5, 6]  # episodes with wrong subtitle
NEXT_ACTION   = '40c1405810e1d492d36c686b19fdd772f47beba84f'
BACKEND_URL   = 'https://api.shortlovers.id/api'
R2_PUBLIC     = 'https://stream.shortlovers.id'
R2_BUCKET     = os.getenv('R2_BUCKET_NAME') or 'shortlovers'
TEMP_DIR      = Path('C:/tmp/rescrape_fix')
QUALITY_PREF  = ['720P', '540P', '480P', '360P']

TEMP_DIR.mkdir(parents=True, exist_ok=True)

def get_s3():
    return boto3.client('s3',
        endpoint_url=os.getenv('R2_ENDPOINT'),
        aws_access_key_id=os.getenv('R2_ACCESS_KEY_ID'),
        aws_secret_access_key=os.getenv('R2_SECRET_ACCESS_KEY'),
        region_name='auto',
    )

def fetch_episodes():
    watch_url = f'https://vidrama.asia/watch/{DRAMA_SLUG}--{DRAMA_ID}/1?provider=microdrama'
    headers = {
        'next-action': NEXT_ACTION,
        'accept': 'text/x-component',
        'content-type': 'text/plain;charset=UTF-8',
        'origin': 'https://vidrama.asia',
        'referer': watch_url,
        'user-agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
    }
    r = requests.post(watch_url, headers=headers,
                      data=json.dumps([DRAMA_ID]).encode('utf-8'), timeout=30)
    for line in r.text.split('\n'):
        if ':' not in line: continue
        idx, _, rest = line.partition(':')
        if idx.strip().isdigit() and rest:
            try:
                chunk = json.loads(rest)
                if isinstance(chunk, dict) and 'episodes' in chunk:
                    return chunk['episodes']
                if isinstance(chunk, list) and chunk and isinstance(chunk[0], dict) and 'videos' in chunk[0]:
                    return chunk
            except: pass
    return []

def get_best_url(videos):
    qmap = {v.get('quality', ''): v.get('url', '') for v in videos}
    for q in QUALITY_PREF:
        if qmap.get(q): return qmap[q]
    for v in videos:
        if v.get('url'): return v['url']
    return None

def download_and_encode(url, dest):
    raw = dest.with_suffix('.raw.mp4')
    print(f'    Downloading {url[:60]}...')
    resp = requests.get(url, timeout=180, stream=True)
    resp.raise_for_status()
    total = 0
    with open(raw, 'wb') as f:
        for chunk in resp.iter_content(chunk_size=2*1024*1024):
            f.write(chunk)
            total += len(chunk)
    print(f'    Downloaded: {total/1024/1024:.1f}MB')

    # Encode mobile-friendly + faststart
    result = subprocess.run(
        ['ffmpeg', '-y', '-i', str(raw),
         '-c:v', 'libx264', '-crf', '26', '-preset', 'fast',
         '-maxrate', '1500k', '-bufsize', '3000k',
         '-c:a', 'aac', '-b:a', '128k',
         '-movflags', '+faststart', str(dest)],
        capture_output=True, timeout=300
    )
    try: raw.unlink()
    except: pass
    return result.returncode == 0 and dest.exists()

def upload_to_r2(src, r2_key):
    print(f'    Uploading to R2: {r2_key}')
    get_s3().upload_file(
        str(src), R2_BUCKET, r2_key,
        ExtraArgs={
            'ContentType': 'video/mp4',
            'CacheControl': 'public, max-age=31536000, immutable',
            'ContentDisposition': 'inline',
        }
    )
    return f'{R2_PUBLIC}/{r2_key}'

def main():
    print(f'=== Re-scraping {DRAMA_TITLE} ===')
    print(f'Target episodes: {TARGET_EPISODES}')

    episodes = fetch_episodes()
    print(f'Fetched {len(episodes)} total episodes')

    # Index episodes by number
    ep_map = {}
    for i, ep in enumerate(episodes):
        # Try different field names
        epnum = ep.get('episodeNumber') or ep.get('episode') or ep.get('ep') or (i + 1)
        try: epnum = int(epnum)
        except: epnum = i + 1
        ep_map[epnum] = ep

    print(f'Episode numbers found: {sorted(ep_map.keys())[:10]}...')

    for target_ep in TARGET_EPISODES:
        print(f'\n[Ep {target_ep}]')
        ep = ep_map.get(target_ep)
        if not ep:
            print(f'  NOT FOUND in episode list - trying by index')
            ep = episodes[target_ep - 1] if target_ep <= len(episodes) else None
        if not ep:
            print(f'  SKIPPING - episode not found')
            continue

        videos = ep.get('videos', [])
        print(f'  Videos available: {[v.get("quality") for v in videos]}')

        url = get_best_url(videos)
        if not url:
            print(f'  No video URL found')
            continue

        dest = TEMP_DIR / f'ep{target_ep:03d}.mp4'
        r2_key = f'dramas/microdrama/{DRAMA_SLUG}/ep{target_ep:03d}/video.mp4'

        ok = download_and_encode(url, dest)
        if not ok:
            print(f'  Encode FAILED')
            continue

        video_url = upload_to_r2(dest, r2_key)
        print(f'  [DONE] {video_url}')

        try: dest.unlink()
        except: pass
        time.sleep(1)

    print('\n=== DONE ===')

if __name__ == '__main__':
    main()
