#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
KingShort Vidrama Scraper for cubetv Provider
=============================================
Downloads dramas from cubetv provider on vidrama.asia,
transcodes each episode to 720p and 540p with faststart,
uploads to Cloudflare R2, and registers to database with status Pending.
"""
import requests
import boto3
import subprocess
import time
import tempfile
import urllib3
import re
import os
import sys
from pathlib import Path
from botocore.config import Config

urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)
sys.stdout.reconfigure(encoding='utf-8')

# ── CONFIG ───────────────────────────────────────────────────────────────────
API_BASE    = 'https://api.shortlovers.id/api'
ADMIN_KEY   = '00ca04e3e2702be565d7bf44e783255247708289bce9b2fb6187a2e117f87fd14'
ADMIN_HDR   = {'x-admin-key': ADMIN_KEY, 'Content-Type': 'application/json'}

R2_ENDPOINT = 'https://a142d3b29a5d64943cb251157e25eaf3.r2.cloudflarestorage.com'
R2_KEY_ID   = '07c99c897986ea52703c1285308d5e2c'
R2_SECRET   = '44788d376ffb216e1e73784b6fe1ff1423607928898a87c50819b52cdfc12e44'
R2_BUCKET   = 'shortlovers'
R2_PUBLIC   = 'https://stream.shortlovers.id'

VIDRAMA_API = 'https://vidrama.asia/api/netshortv2'
WEB_HDRS    = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36',
    'Referer': 'https://vidrama.asia/',
    'Cookie': '_fbp=fb.1.1770653154777.876935444165455244; _tt_enable_cookie=1; _ttp=01KH1JE0K4H648BY6E3FQ6EXRZ_.tt.1; _ga=GA1.1.1826262121.1771037718; HstCfa5004644=1772873251576; c_ref_5004644=https%3A%2F%2Fwww.google.com%2F; __dtsu=4C301774685394D291D3AB624E4AA57E; _pubcid=8a5abbf9-164b-422f-b349-0e1ba702ea69; _cc_id=a4a99f9a552125d19ea447bfafb9c63b; global_ui_lang=id; HstCmu5004644=1779384259258; vidrama_chat_anon=45cc06417e3a261dc8f368a8; HstCnv5004644=57; panorama_chat_expiry=180615916940; cf_clearance=VX_Xr7NRDn_bHR2_IRoxNdxL5BLxbzfsHkfsLSMFtA-1780530299-1.2.1.1-DhdR_gz24mRDxfqDZ6JRW4At_PbLTJ69TGIB31qouJlgG1ikLqNuWbm0okBLp1Go2MWem_3X.cMay4eQE7HLKx.Wz4KMiulNBq9fjyCxxmDPzi0YVkbw9OYiRi.jdLdpNnisuVfw8pLUT6D_YvEsubtvxlDh5jDYbq4oTMFkq1fE56yfDW6b6jn6IJ6bvb3akXHtVJ6OQFo1geg5Wb6Xw_ir7wl9U2yv1T0KvJKz4vMT0EgO6XLW1vbbwyS24o0gn_DLqysP7wxeeSoHslRpEeEXdsdPQjhy48S0JGs8NQPgxSoEuttjbRZEuqOiGjJjqCM6i9P9i1NArsF4tZuA; HstCns5004644=78; HstCla5004644=1780530357612; HstPn5004644=6; HstPt5004644=144; _ga_HCQQPKGEVH=GS2.1.s1780529507$o116$g1$t1780530797$j60$l0$h0; ttcsid=1780529507258::pJpTkBxKiHThj3O3zgcq.134.1780530904561.0::1.1288704.850729::1397297.32.106.1284::1396541.167.800; ttcsid_D5SNQPRC77UDQTF8A5EG=1780529507262::spplkSuwY5eRZp2hmJoH.116.1780530904561.1'
}

TEMP_DIR = Path(tempfile.gettempdir()) / 'cubetv_scraper'
TEMP_DIR.mkdir(exist_ok=True)

# ── HELPERS ──────────────────────────────────────────────────────────────────
def get_r2():
    return boto3.client('s3', endpoint_url=R2_ENDPOINT,
                        aws_access_key_id=R2_KEY_ID, aws_secret_access_key=R2_SECRET,
                        config=Config(signature_version='s3v4'), region_name='auto')

def r2_exists(r2, key):
    try:
        r2.head_object(Bucket=R2_BUCKET, Key=key)
        return True
    except:
        return False

def r2_upload(r2, local_path, key, content_type='video/mp4'):
    r2.upload_file(str(local_path), R2_BUCKET, key, ExtraArgs={'ContentType': content_type},
                    Config=boto3.s3.transfer.TransferConfig(multipart_threshold=30*1024*1024, multipart_chunksize=10*1024*1024))
    return f"{R2_PUBLIC}/{key}"

def check_duplicate_in_db(title):
    try:
        r = requests.get(f"{API_BASE}/dramas/search?q={title}", timeout=10)
        dramas = r.json().get('dramas', [])
        for d in dramas:
            if d['title'].lower().strip() == title.lower().strip():
                return d['id']
    except Exception as e:
        print(f"Error checking duplicate for '{title}': {e}")
    return None

def slugify(text):
    text = text.lower()
    # Replace non-word chars with -
    slug = re.sub(r'[\W_]+', '-', text).strip('-')
    return slug

def get_episode_url(drama_id, ep_no, retries=3):
    url = f"{VIDRAMA_API}/episode/{drama_id}/{ep_no}?lang=id_ID"
    for attempt in range(retries):
        try:
            r = requests.get(url, headers=WEB_HDRS, timeout=15, verify=False)
            data = r.json()
            if data.get('code') == 200:
                videos = data['data'].get('videos', [])
                subs = data['data'].get('subtitles', [])
                
                # Check for Indonesian subtitle
                id_sub = next((s['url'] for s in subs if s.get('language') == 'id_ID'), None)
                if not id_sub and subs: 
                    id_sub = subs[0]['url']
                
                video_urls = []
                # Prioritize qualities
                for q in ['720p', '1080p', '540p']:
                    for v in videos:
                        if v.get('quality') == q and v['url'] not in video_urls:
                            video_urls.append(v['url'])
                            
                for v in videos:
                    if v['url'] not in video_urls:
                        video_urls.append(v['url'])
                        
                return video_urls, id_sub
        except Exception as e:
            print(f"      [WARN] Episode API failed for ep{ep_no} (attempt {attempt+1}): {e}")
            time.sleep(2)
    return [], None

def api_get_or_create_drama(detail, slug, cover_url):
    title = detail.get('title', 'Unknown Title')
    payload = {
        'title': title,
        'description': detail.get('description', title),
        'cover': cover_url,
        'genres': detail.get('labels', ['Drama']) or ['Drama'],
        'totalEpisodes': detail.get('totalEpisodes', 0),
        'isComplete': detail.get('isFinished', False),
        'country': 'China', 
        'language': 'Indonesia',
        'status': 'completed' if detail.get('isFinished') else 'ongoing',
        'isActive': False, # Pending!
    }
    try:
        r = requests.post(f"{API_BASE}/admin/dramas", headers=ADMIN_HDR, json=payload, timeout=20)
        if r.ok:
            return r.json().get('id')
        else:
            print(f"      [ERROR] Failed to create drama in DB. Status: {r.status_code}, Body: {r.text}")
    except Exception as e:
        print(f"      [ERROR] Exception creating drama in DB: {e}")
    return None

def api_upsert_episode(drama_db_id, ep_no, url_720, url_540=None, sub_url=None):
    payload = {
        'episodeNumber': ep_no, 
        'title': f'Episode {ep_no}', 
        'videoUrl': url_720, 
        'isActive': True
    }
    if url_540: 
        payload['videoUrl540p'] = url_540
        
    try:
        r = requests.post(f"{API_BASE}/admin/dramas/{drama_db_id}/episodes", headers=ADMIN_HDR, json=payload, timeout=20)
        if not r.ok: 
            print(f"      [WARN] DB Episode upsert failed. Status: {r.status_code}")
            return None
        ep_id = r.json().get('id')
        if ep_id and sub_url:
            sub_payload = {
                'language': 'indonesia', 
                'label': 'Indonesia', 
                'url': sub_url, 
                'isDefault': True
            }
            requests.post(f"{API_BASE}/episodes/{ep_id}/subtitles", headers=ADMIN_HDR, json=sub_payload, timeout=10)
        return ep_id
    except Exception as e:
        print(f"      [ERROR] DB Episode upsert exception: {e}")
    return None

def encode_720_and_540(inp, out_720, out_540):
    # Transcode raw to 720p with faststart
    cmd_720 = [
        'ffmpeg', '-y', '-i', str(inp), 
        '-c:v', 'libx264', '-crf', '26', '-maxrate', '1500k', '-bufsize', '3000k',
        '-c:a', 'aac', '-b:a', '128k', '-movflags', '+faststart', 
        '-loglevel', 'error', str(out_720)
    ]
    res_720 = subprocess.run(cmd_720, timeout=600)
    if res_720.returncode != 0: 
        return False
        
    # Transcode 720p to 540p with faststart
    cmd_540 = [
        'ffmpeg', '-y', '-i', str(out_720), 
        '-vf', 'scale=-2:540', 
        '-c:v', 'libx264', '-crf', '28', '-preset', 'fast',
        '-c:a', 'aac', '-b:a', '96k', '-movflags', '+faststart', 
        '-loglevel', 'error', str(out_540)
    ]
    return subprocess.run(cmd_540, timeout=600).returncode == 0

def fetch_cubetv_provider_dramas():
    dramas = []
    print("=== Disclosing dramas from provider cubetv ===")
    for page in range(1, 15):
        url = f"{VIDRAMA_API}/feed/{page}?provider=cubetv&lang=id_ID"
        try:
            r = requests.get(url, headers=WEB_HDRS, timeout=20, verify=False)
            if r.status_code == 200:
                items = r.json().get('data', [])
                if not items:
                    break
                print(f"  Page {page}: Found {len(items)} dramas")
                for it in items:
                    # Deduplicate in current list
                    if not any(d['id'] == it['id'] for d in dramas):
                        dramas.append({
                            'id': it.get('id'),
                            'title': it.get('title'),
                            'slug': slugify(it.get('title', ''))
                        })
            else:
                break
        except Exception as e:
            print(f"  Error paging provider list: {e}")
            break
            
    print(f"Total unique dramas discovered: {len(dramas)}")
    return dramas

def scrape_single_drama(r2, vid_id, slug, title):
    prefix = f"netshortv2/{slug}"
    print(f"\nProcessing drama: '{title}' (ID: {vid_id}, Slug: {slug})")
    
    # 1. Check duplicate in database
    db_id = check_duplicate_in_db(title)
    if db_id:
        print(f"  -> Title already exists in database (ID: {db_id}). Skipping creation.")
    else:
        # Get Metadata
        url = f"{VIDRAMA_API}/detail/{vid_id}?lang=id_ID"
        try:
            r = requests.get(url, headers=WEB_HDRS, timeout=15, verify=False)
            if not r.ok or r.json().get('code') != 200:
                print(f"  -> [ERROR] Failed to fetch metadata details for ID {vid_id}.")
                return False
            detail = r.json()['data']
        except Exception as e:
            print(f"  -> [ERROR] Exception fetching metadata: {e}")
            return False
            
        # Create cover WebP URL
        cover_key = f"{prefix}/cover.webp"
        r2_cover_url = f"{R2_PUBLIC}/{cover_key}"
        
        # Register in database
        db_id = api_get_or_create_drama(detail, slug, r2_cover_url)
        if not db_id:
            print("  -> [ERROR] Failed to register drama in DB.")
            return False
        print(f"  -> [DB] Created drama entry (ID: {db_id}, status: Pending)")
        
        # Upload Cover to R2
        if not r2_exists(r2, cover_key):
            try:
                cov_res = requests.get(detail['cover'], headers=WEB_HDRS, timeout=30, verify=False)
                if cov_res.ok:
                    p = TEMP_DIR / f"{slug}_cover.webp"
                    p.write_bytes(cov_res.content)
                    r2_upload(r2, p, cover_key, 'image/webp')
                    p.unlink()
                    print("  -> [R2] Cover uploaded successfully")
            except Exception as e:
                print(f"  -> [WARN] Failed to upload cover to R2: {e}")
                
    # 2. Scrape episodes
    url = f"{VIDRAMA_API}/detail/{vid_id}?lang=id_ID"
    try:
        r = requests.get(url, headers=WEB_HDRS, timeout=15, verify=False)
        detail = r.json()['data']
    except Exception as e:
        print(f"  -> [ERROR] Failed to fetch episode list metadata: {e}")
        return False
        
    total_eps = detail.get('totalEpisodes', 0)
    print(f"  -> Total Episodes to process: {total_eps}")
    
    success_count = 0
    failed_count = 0
    skipped_count = 0
    
    for ep_no in range(1, total_eps + 1):
        k720 = f"{prefix}/ep{ep_no:03d}.mp4"
        k540 = f"{prefix}/ep{ep_no:03d}_540p.mp4"
        ksub = f"{prefix}/ep{ep_no:03d}.vtt"
        
        # If both 720p and 540p exist in R2, skip download/transcode
        if r2_exists(r2, k720) and r2_exists(r2, k540):
            print(f"    ep{ep_no:03d}: already exists in R2. Linking to DB...", end="", flush=True)
            u720 = f"{R2_PUBLIC}/{k720}"
            u540 = f"{R2_PUBLIC}/{k540}"
            sub_url = f"{R2_PUBLIC}/{ksub}" if r2_exists(r2, ksub) else None
            api_upsert_episode(db_id, ep_no, u720, u540, sub_url)
            print(" LINKED")
            success_count += 1
            continue
            
        print(f"    ep{ep_no:03d}: processing... ", end="", flush=True)
        vurls, sub_url_raw = get_episode_url(vid_id, ep_no)
        if not vurls:
            print("SKIPPED (No URLs)")
            skipped_count += 1
            continue
            
        # Download subtitle VTT
        final_sub_r2 = None
        if sub_url_raw:
            try:
                sub_res = requests.get(sub_url_raw, timeout=10, verify=False)
                if sub_res.ok:
                    r2.put_object(Bucket=R2_BUCKET, Key=ksub, Body=sub_res.content, ContentType='text/vtt')
                    final_sub_r2 = f"{R2_PUBLIC}/{ksub}"
            except Exception as e:
                pass
                
        # Download video files
        raw_path = TEMP_DIR / f"{slug}_raw_{ep_no}.mp4"
        o720_path = TEMP_DIR / f"{slug}_720_{ep_no}.mp4"
        o540_path = TEMP_DIR / f"{slug}_540_{ep_no}.mp4"
        
        download_success = False
        for vurl in vurls:
            if download_success:
                break
                
            for attempt in range(2):
                cdn_headers = {
                    'User-Agent': WEB_HDRS['User-Agent'],
                    'Referer': 'https://vidrama.asia/',
                    'Accept': '*/*'
                }
                try:
                    with requests.get(vurl, stream=True, headers=cdn_headers, verify=False, timeout=60) as res:
                        if res.status_code == 200:
                            with open(raw_path, 'wb') as f_out:
                                for chunk in res.iter_content(2*1024*1024):
                                    if chunk:
                                        f_out.write(chunk)
                            size_kb = raw_path.stat().st_size / 1024 if raw_path.exists() else 0
                            if size_kb > 50:
                                download_success = True
                                break
                        elif res.status_code == 403:
                            # Use curl
                            curl_cmd = [
                                "curl", "-s", "-L",
                                "-H", f"User-Agent: {cdn_headers['User-Agent']}",
                                "-H", f"Referer: {cdn_headers['Referer']}",
                                "-o", str(raw_path),
                                vurl
                            ]
                            subprocess.run(curl_cmd, timeout=60)
                            size_kb = raw_path.stat().st_size / 1024 if raw_path.exists() else 0
                            if size_kb > 50:
                                download_success = True
                                break
                except:
                    pass
                time.sleep(1)
                
        if not download_success:
            print("ERROR (Download failed)")
            failed_count += 1
            continue
            
        # Transcode & Upload
        try:
            if encode_720_and_540(raw_path, o720_path, o540_path):
                u720 = r2_upload(r2, o720_path, k720)
                u540 = r2_upload(r2, o540_path, k540)
                api_upsert_episode(db_id, ep_no, u720, u540, final_sub_r2)
                print("SUCCESS")
                success_count += 1
            else:
                print("ERROR (Transcode failed)")
                failed_count += 1
        except Exception as e:
            print(f"ERROR ({e})")
            failed_count += 1
        finally:
            for p in [raw_path, o720_path, o540_path]:
                if p.exists():
                    p.unlink()
                    
        # Sleep to avoid rate limiting
        time.sleep(2)
        
    print(f"  -> Scrape results for '{title}': {success_count} success, {failed_count} failed, {skipped_count} skipped.")
    return True

# ── MAIN ─────────────────────────────────────────────────────────────────────
def main():
    r2 = get_r2()
    
    # Optional single drama test argument
    if len(sys.argv) > 1 and sys.argv[1] == '--test':
        print("=== TEST RUN: Processing 1 drama only ===")
        # Felix nelayan: "Mencari Sinar di Lautan" (ID: 2056946805631225858)
        scrape_single_drama(r2, "2056946805631225858", "mencari-sinar-di-lautan", "Mencari Sinar di Lautan")
        print("=== TEST RUN COMPLETED ===")
        return
        
    # Get all dramas for cubetv
    dramas = fetch_cubetv_provider_dramas()
    
    # Process sequentially
    for idx, d in enumerate(dramas):
        print(f"\n--- Progress: {idx+1}/{len(dramas)} ---")
        scrape_single_drama(r2, d['id'], d['slug'], d['title'])
        # Sleep between dramas
        time.sleep(5)
        
    print("\n=== SCRAPING COMPLETED FOR ALL CUBETV DRAMAS ===")

if __name__ == "__main__":
    main()
