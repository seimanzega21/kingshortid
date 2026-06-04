# -*- coding: utf-8 -*-
"""
Backfill Script for netshortv2 Provider pending dramas
- Skips already registered episodes using DB checks.
- Scrapes raw streams from netshortv2 API.
- Encodes to 720p & 540p faststart.
- Uploads to R2 and registers to DB.
- Status remains Pending.
"""
import requests
import boto3
import sys
import json
import time
import os
import argparse
import subprocess
import urllib3
import re
from pathlib import Path
from botocore.config import Config

urllib3.disable_warnings()
sys.stdout.reconfigure(encoding='utf-8')

# ─── CONFIG ─────────────────────────────────────────────────────────────────
API_BASE = 'https://api.shortlovers.id/api'
ADMIN_KEY = '00ca04e3e2702be565d7bf44e783255247708289bce9b2fb6187a2e117f87fd14'
ADMIN_HDR = {'x-admin-key': ADMIN_KEY, 'Content-Type': 'application/json'}

R2_ENDPOINT = 'https://a142d3b29a5d64943cb251157e25eaf3.r2.cloudflarestorage.com'
R2_KEY_ID = '07c99c897986ea52703c1285308d5e2c'
R2_SECRET = '44788d376ffb216e1e73784b6fe1ff1423607928898a87c50819b52cdfc12e44'
R2_BUCKET = 'shortlovers'
R2_PUBLIC = 'https://stream.shortlovers.id'

COOKIE = '_fbp=fb.1.1770653154777.876935444165455244; _tt_enable_cookie=1; _ttp=01KH1JE0K4H648BY6E3FQ6EXRZ_.tt.1; _ga=GA1.1.1826262121.1771037718; HstCfa5004644=1772873251576; c_ref_5004644=https%3A%2F%2Fwww.google.com%2F; __dtsu=4C301774685394D291D3AB624E4AA57E; _pubcid=8a5abbf9-164b-422f-b349-0e1ba702ea69; _cc_id=a4a99f9a552125d19ea447bfafb9c63b; global_ui_lang=id; HstCmu5004644=1779384259258; vidrama_chat_anon=45cc06417e3a261dc8f368a8; HstCnv5004644=48; cf_clearance=N5A.kyHMnJ7RBK3hOyqybB6KddOTpRsZyEiE.fgp5kM-1779713242-1.2.1.1-9YHMfsNOniF6J54T1_JEaJY6mYbVJWOz8Kkm0raJacrpotGOYzyN_gG.Kxb7kfPxOO1wYdSenqFW0HIUwqQ57F5gqyjRbwvS8_r8rLFxIbYHNWMAahrr.iKy0dsa1krg8mVhzXDilHK71X.Iszvd8uo_CwVzbHiVUurJ8eF1DyguF2fK1vFa68H3Z5HFzZhBvVaIle1tEW3443.tH9TYjQX.7HKB9SBI2ZHkNto2vDQ2F77XP3cLmCp7GPXINCG8mrZf6l5xsxuh_xyqNp1bIRyxkUhz9IooxQKp3yV9Crri9TFW9II5q0M50yOlhCROGsKwa0AkIkKtWi.pNc5ATg; HstCla5004644=1779713242621; HstPn5004644=2; HstPt5004644=93; HstCns5004644=54; panoramaId_expiry=1779799644224'

WEB_HDRS = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36',
    'Referer': 'https://vidrama.asia/',
    'Cookie': COOKIE
}

# Temp folder
WORKSPACE_DIR = Path(__file__).resolve().parent.parent
TEMP_DIR = WORKSPACE_DIR / 'temp_netshort'
TEMP_DIR.mkdir(exist_ok=True)

def get_r2():
    return boto3.client(
        's3', endpoint_url=R2_ENDPOINT,
        aws_access_key_id=R2_KEY_ID, aws_secret_access_key=R2_SECRET,
        config=Config(signature_version='s3v4'), region_name='auto'
    )

def make_slug(title):
    s = title.strip().lower()
    s = s.replace("(dubbing)", "")
    s = re.sub(r'[^\w\s-]', '', s)
    s = re.sub(r'[-\s]+', '-', s)
    return s.strip('-')

def get_db_dramas():
    url = f"{API_BASE}/dramas?limit=1500&includeInactive=true"
    r = requests.get(url, headers=ADMIN_HDR)
    if r.ok:
        data = r.json()
        return data if isinstance(data, list) else data.get("dramas", [])
    return []

def get_registered_episodes(db_id):
    url = f"{API_BASE}/dramas/{db_id}/episodes?includeInactive=true"
    r = requests.get(url, timeout=15)
    if r.ok:
        eps = r.json()
        ep_list = eps if isinstance(eps, list) else eps.get('episodes', eps.get('data', []))
        return {e.get('episodeNumber') for e in ep_list}
    return set()

def get_episode_data(ns_id, ep_no):
    url = f"https://vidrama.asia/api/netshortv2/episode/{ns_id}/{ep_no}?lang=id_ID"
    try:
        r = requests.get(url, headers=WEB_HDRS, timeout=20, verify=False)
        if r.ok:
            data = r.json()
            if data.get('code') == 200:
                return data.get('data', {})
            else:
                print(f"      ⚠ API returned code {data.get('code')}: {data.get('msg')}")
        else:
            print(f"      ⚠ HTTP error {r.status_code}: {r.text[:200]}")
    except Exception as e:
        print(f"      ⚠ Request exception: {e}")
    return {}

def download_file(url, local_path):
    with requests.get(url, headers=WEB_HDRS, stream=True, timeout=60, verify=False) as r:
        if r.status_code == 200:
            with open(local_path, 'wb') as f:
                for chunk in r.iter_content(chunk_size=2*1024*1024):
                    if chunk:
                        f.write(chunk)
            return True
    return False

def encode_faststart_720p(input_path, output_path):
    cmd = [
        'ffmpeg', '-y', '-i', str(input_path),
        '-c:v', 'libx264', '-crf', '26',
        '-maxrate', '1500k', '-bufsize', '3000k',
        '-c:a', 'aac', '-b:a', '128k',
        '-movflags', '+faststart',
        '-loglevel', 'error',
        str(output_path)
    ]
    res = subprocess.run(cmd)
    return res.returncode == 0

def downscale_faststart_540p(input_path, output_path):
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
    res = subprocess.run(cmd)
    return res.returncode == 0

def r2_upload_file(r2, local_path, key, content_type='video/mp4'):
    r2.upload_file(str(local_path), R2_BUCKET, key, ExtraArgs={
        'ContentType': content_type,
        'CacheControl': 'public, max-age=31536000'
    })
    return f"{R2_PUBLIC}/{key}"

def register_episode(db_id, ep_no, url_720, url_540):
    payload = {
        'episodeNumber': ep_no,
        'title': f'Episode {ep_no}',
        'videoUrl': url_720,
        'videoUrl540p': url_540,
        'isVip': False,
        'coinPrice': 0,
        'isActive': True
    }
    r = requests.post(f"{API_BASE}/admin/dramas/{db_id}/episodes", headers=ADMIN_HDR, json=payload, timeout=20)
    if r.ok:
        return r.json().get('id')
    return None

def register_subtitles(episode_id, subtitles_list, r2, slug, ep_no):
    count = 0
    for sub in subtitles_list:
        lang = sub.get('language') or sub.get('lang', '')
        url = sub.get('url') or sub.get('src', '')
        if not url or not lang:
            continue
        
        # Download subtitle
        sub_key = f"dramas/{slug}/ep{ep_no:03d}_{lang}.vtt"
        try:
            sub_r = requests.get(url, timeout=15, verify=False)
            if sub_r.ok:
                r2.put_object(Bucket=R2_BUCKET, Key=sub_key, Body=sub_r.content, ContentType='text/vtt')
                final_sub_url = f"{R2_PUBLIC}/{sub_key}"
                
                # Register in database
                payload = {
                    'language': lang,
                    'label': 'Indonesia' if lang == 'id_ID' else lang,
                    'url': final_sub_url,
                    'isDefault': lang == 'id_ID'
                }
                db_r = requests.post(f"{API_BASE}/episodes/{episode_id}/subtitles", headers=ADMIN_HDR, json=payload, timeout=15)
                if db_r.ok:
                    count += 1
        except Exception as e:
            print(f"      ⚠ Failed to process subtitle {lang}: {e}")
    return count

def main():
    parser = argparse.ArgumentParser(description="Backfill netshortv2 pending dramas")
    parser.add_argument("--dry-run", action="store_true", help="Perform a dry run without modifying anything")
    args = parser.parse_args()

    print("=" * 60)
    print("NETSHORTV2 BACKFILL PIPELINE")
    print("=" * 60)
    if args.dry_run:
        print("!!! DRY RUN MODE ACTIVE !!!")
        print("=" * 60)
    else:
        # Cleanup temp directory on start
        if TEMP_DIR.exists():
            import shutil
            print("Cleaning up temp directory...")
            for child in TEMP_DIR.iterdir():
                try:
                    if child.is_file() or child.is_symlink():
                        child.unlink()
                    elif child.is_dir():
                        shutil.rmtree(child)
                except Exception as e:
                    print(f"   ⚠ Failed to clean temp file {child.name}: {e}")

    # 1. Fetch mapping
    try:
        with open(WORKSPACE_DIR / 'scratch' / 'mapped_netshortv2_dramas.json', 'r') as f:
            mapped = json.load(f)
    except Exception as e:
        print(f"Failed to load mapped dramas: {e}")
        return

    # 2. Fetch all dramas from DB
    print("Fetching drama metadata from DB...")
    db_dramas = get_db_dramas()
    db_lookup = {d['id']: d for d in db_dramas}
    print(f"Loaded {len(db_lookup)} dramas from DB")

    r2 = None if args.dry_run else get_r2()

    # 3. Iterate through dramas
    for idx, item in enumerate(mapped, start=4):
        title = item['title']
        db_id = item['db_id']
        ns_id = item['netshort_id']
        
        if not ns_id:
            print(f"\n[-] Drama {idx}: {title} -> Skipping (No netshort ID mapped)")
            continue

        # Get metadata from DB
        db_meta = db_lookup.get(db_id)
        if not db_meta:
            print(f"\n[-] Drama {idx}: {title} -> Skipping (Not found in DB)")
            continue

        total_eps = db_meta.get('totalEpisodes', 0)
        slug = make_slug(title)
        print(f"\n🎬 Drama {idx}/23: {title}")
        print(f"   DB ID: {db_id} | Netshort ID: {ns_id} | Slug: {slug} | Total Eps: {total_eps}")

        # Fetch already registered episodes
        registered_eps = get_registered_episodes(db_id) if not args.dry_run else set()
        print(f"   Episodes in DB: {len(registered_eps)} / {total_eps}")

        if len(registered_eps) >= total_eps and total_eps > 0:
            print("   ✓ Already fully populated. Skipping.")
            continue

        # Process episodes
        for ep_no in range(1, total_eps + 1):
            if ep_no in registered_eps:
                continue

            print(f"\n   📹 Episode {ep_no}/{total_eps}:")
            if args.dry_run:
                print(f"     [DRY RUN] Would scrape EP {ep_no} for netshort_id {ns_id}")
                continue

            # Fetch episode data
            ep_data = {}
            for attempt in range(5):
                ep_data = get_episode_data(ns_id, ep_no)
                if ep_data and ep_data.get('videos'):
                    break
                print(f"     Waiting 8 seconds before retry {attempt+2}/5...")
                time.sleep(8)

            if not ep_data or not ep_data.get('videos'):
                print(f"     ✗ Failed to get episode data for EP {ep_no}, skipping")
                continue

            videos = ep_data.get('videos', [])
            subtitles = ep_data.get('subtitles', [])

            # Choose best quality URL
            best_video = None
            for q in ['1080p', '720p', '540p']:
                best_video = next((v for v in videos if v.get('quality') == q), None)
                if best_video:
                    break
            if not best_video and videos:
                best_video = videos[0]

            if not best_video:
                print(f"     ✗ No videos available for EP {ep_no}")
                continue

            video_url = best_video.get('url')
            print(f"     Selected Quality: {best_video.get('quality')}")

            # Paths
            raw_local = TEMP_DIR / f"raw_ep{ep_no:03d}.mp4"
            out_720_local = TEMP_DIR / f"ep{ep_no:03d}_720p.mp4"
            out_540_local = TEMP_DIR / f"ep{ep_no:03d}_540p.mp4"

            try:
                # A. Download raw stream
                print(f"     ⬇ Downloading raw stream...", end='', flush=True)
                if download_file(video_url, raw_local):
                    print(f" ✓ {raw_local.stat().st_size / 1024 / 1024:.1f}MB")
                else:
                    print(" ✗ Download failed")
                    continue

                # B. Encode to 720p
                print(f"     ⚙ Encoding 720p faststart...", end='', flush=True)
                t0 = time.time()
                if encode_faststart_720p(raw_local, out_720_local):
                    print(f" ✓ {out_720_local.stat().st_size / 1024 / 1024:.1f}MB (took {time.time()-t0:.1f}s)")
                else:
                    print(" ✗ Failed")
                    continue

                # C. Downscale to 540p
                print(f"     ⚙ Downscaling to 540p faststart...", end='', flush=True)
                t0 = time.time()
                if downscale_faststart_540p(out_720_local, out_540_local):
                    print(f" ✓ {out_540_local.stat().st_size / 1024 / 1024:.1f}MB (took {time.time()-t0:.1f}s)")
                else:
                    print(" ✗ Failed")
                    continue

                # D. Upload to R2
                print("     ⬆ Uploading videos to R2...", end='', flush=True)
                key_720 = f"dramas/{slug}/ep{ep_no:03d}_720p.mp4"
                key_540 = f"dramas/{slug}/ep{ep_no:03d}_540p.mp4"

                r2_url_720 = r2_upload_file(r2, out_720_local, key_720)
                r2_url_540 = r2_upload_file(r2, out_540_local, key_540)
                print(" ✓ Done")

                # E. Register in DB
                ep_id = register_episode(db_id, ep_no, r2_url_720, r2_url_540)
                if ep_id:
                    sub_count = register_subtitles(ep_id, subtitles, r2, slug, ep_no)
                    print(f"     ✓ EP {ep_no} registered | {sub_count} subtitle(s) registered")
                else:
                    print(f"     ✗ EP {ep_no} failed to register in DB")

            except Exception as e:
                print(f"     ✗ Error processing EP {ep_no}: {e}")
            finally:
                # Cleanup
                for path in [raw_local, out_720_local, out_540_local]:
                    if path.exists():
                        try:
                            path.unlink()
                        except: pass

            time.sleep(2.0)

    print("\n" + "=" * 60)
    print("BACKFILL PROCESS COMPLETED!")
    print("=" * 60)

if __name__ == '__main__':
    main()
