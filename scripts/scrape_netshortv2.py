#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Netshort V2 Scraper - KingShort Pipeline (API-based)
======================================================
Downloads 4 target dramas, uploads to R2, syncs to KingShort via API.

API Endpoint for episodes:
  GET https://vidrama.asia/api/netshortv2/episode/{drama_id}/{ep_no}?lang=id_ID
  Returns: { code: 200, data: { episodeId, videos: [{quality, url}] } }
"""
import sys
import requests
import boto3
import subprocess
import time
import json
import tempfile
import urllib3
from pathlib import Path
from botocore.config import Config

urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

# ── Config ──────────────────────────────────────────────────────────────────
API_BASE    = 'https://api.shortlovers.id'
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
    'Cookie': '_fbp=fb.1.1770653154777.876935444165455244; _tt_enable_cookie=1; _ttp=01KH1JE0K4H648BY6E3FQ6EXRZ_.tt.1; _ga=GA1.1.1826262121.1771037718; HstCfa5004644=1772873251576; c_ref_5004644=https%3A%2F%2Fwww.google.com%2F; __dtsu=4C301774685394D291D3AB624E4AA57E; _pubcid=8a5abbf9-164b-422f-b349-0e1ba702ea69; _cc_id=a4a99f9a552125d19ea447bfafb9c63b; HstCmu5004644=1776164034743; HstPn5004644=1; cf_clearance=AQRjv4.Cj2nHbg_KLivmkViGOllnwGPpIVkj35_jfKI-1777471778-1.2.1.1-TEdhFr7wBXOwe6l8ybhNx3V3OAO2FmEP81fCwLc_mclcsLHuLye6b0vcwrShIGHIdgmlaY14VoOLGlccyUA11WHrRIEncihkGDwdc8C44c79F_3U4SEVsPeQAtPP.1_v6j.daxeE5gMBUPycNwj8rIn4fxg5dhhxrCsZvPIyDKo0BUWtkSEcjfRXcll7MrK8y3YSM8WhGmqI.PzKcfsFF.006ENmy7BGlLwqjy_QDYg8Y7xuxVKlIr_3ApmsnXItGKvJ2DDt_XQUqh1H5hqKnf50BS4QFNfxQEUeytk94ofP8SYQwlqg1HEIz3BMlJC4OQhzn5m0L6muYtASD.jwaw; HstCla5004644=1777471778959; HstPt5004644=72; HstCnv5004644=31; HstCns5004644=35; panoramaId_expiry=1777558180696; _ga_HCQQPKGEVH=GS2.1.s1777476684$o70$g1$t1777477281$j55$l0$h0; ttcsid_D5SNQPRC77UDQTF8A5EG=1777476683162::JiaNdPsba2GCy8oVLuyE.75.1777477294114.1; ttcsid=1777476683155::c9Pa9Oee_DaSEml_Mj5I.85.1777477294114.0::1.610918.6485::610880.63.113.1122::610008.512.600'
}

TEMP_DIR = Path(tempfile.gettempdir()) / 'ns2_scraper'
TEMP_DIR.mkdir(exist_ok=True)

# ── Target Dramas ────────────────────────────────────────────────────────────
TARGET_DRAMAS = [
    {
        'slug': 'pemilik-kitab-pedang',
        'drama_id': '2036690458087784450',
        'r2_prefix': 'netshortv2/pemilik-kitab-pedang',
    },
    {
        'slug': 'jenderal-masakanku-siap',
        'drama_id': '2045396177699995650',
        'r2_prefix': 'netshortv2/jenderal-masakanku-siap',
    },
    {
        'slug': 'kode-cinta-robot',
        'drama_id': '2044326309693227010',
        'r2_prefix': 'netshortv2/kode-cinta-robot',
    },
    {
        'slug': 'dia-kembali-dari-balik-legenda',
        'drama_id': '2011980833696841730',
        'r2_prefix': 'netshortv2/dia-kembali-dari-balik-legenda',
    },
]

# ── R2 ────────────────────────────────────────────────────────────────────────
def get_r2():
    return boto3.client(
        's3',
        endpoint_url=R2_ENDPOINT,
        aws_access_key_id=R2_KEY_ID,
        aws_secret_access_key=R2_SECRET,
        config=Config(signature_version='s3v4'),
        region_name='auto',
    )

def r2_exists(r2, key):
    try:
        r2.head_object(Bucket=R2_BUCKET, Key=key)
        return True
    except:
        return False

def r2_upload(r2, local_path, key, content_type='video/mp4'):
    r2.upload_file(
        str(local_path), R2_BUCKET, key,
        ExtraArgs={'ContentType': content_type},
        Config=boto3.s3.transfer.TransferConfig(
            multipart_threshold=30 * 1024 * 1024,
            multipart_chunksize=10 * 1024 * 1024,
        )
    )
    return f"{R2_PUBLIC}/{key}"

# ── Vidrama API ───────────────────────────────────────────────────────────────
def get_drama_detail(drama_id):
    url = f"{VIDRAMA_API}/detail/{drama_id}?lang=id_ID"
    r = requests.get(url, headers=WEB_HDRS, timeout=15, verify=False)
    data = r.json()
    if data.get('code') != 200:
        raise Exception(f"Failed: {data}")
    return data['data']

def get_episode_url(drama_id, ep_no, retries=3):
    url = f"{VIDRAMA_API}/episode/{drama_id}/{ep_no}?lang=id_ID"
    for attempt in range(retries):
        try:
            r = requests.get(url, headers=WEB_HDRS, timeout=15, verify=False)
            data = r.json()
            if data.get('code') == 200:
                videos = data['data'].get('videos', [])
                ep_id  = data['data'].get('episodeId', '')
                for q in ['720p', '1080p', '540p', '480p', '360p']:
                    for v in videos:
                        if v.get('quality') == q:
                            return v['url'], ep_id
                if videos:
                    return videos[0]['url'], ep_id
        except Exception as e:
            print(f"    url attempt {attempt+1}: {e}")
            time.sleep(2)
    return None, None

# ── Backend API ───────────────────────────────────────────────────────────────
def api_get_or_create_drama(detail, slug, cover_url):
    payload = {
        'title': detail['title'],
        'description': detail.get('description', detail['title']),
        'cover': cover_url,
        'genres': detail.get('labels', ['Drama']) or ['Drama'],
        'totalEpisodes': detail.get('totalEpisodes', 0),
        'isComplete': detail.get('isFinished', False),
        'country': 'China',
        'language': 'Indonesia',
        'status': 'completed' if detail.get('isFinished') else 'ongoing',
        'isActive': False,
    }
    r = requests.post(f"{API_BASE}/api/admin/dramas", headers=ADMIN_HDR, json=payload, timeout=20)
    if r.ok:
        result = r.json()
        return result.get('id')
    else:
        print(f"  Drama API error: {r.status_code} {r.text[:200]}")
        return None

def api_upsert_episode(drama_db_id, ep_no, url_720, url_540=None):
    payload = {
        'episodeNumber': ep_no,
        'title': f'Episode {ep_no}',
        'videoUrl': url_720,
        'isActive': False,
    }
    if url_540:
        payload['videoUrl540p'] = url_540
    r = requests.post(
        f"{API_BASE}/api/admin/dramas/{drama_db_id}/episodes",
        headers=ADMIN_HDR, json=payload, timeout=20
    )
    return r.ok

def api_update_drama(drama_db_id, total_episodes):
    r = requests.patch(
        f"{API_BASE}/api/admin/dramas/{drama_db_id}",
        headers=ADMIN_HDR,
        json={'totalEpisodes': total_episodes},
        timeout=15
    )
    return r.ok

# ── Download & Encode ──────────────────────────────────────────────────────────
def download_mp4(url, out_path, label=''):
    print(f"    Download {label}...", end='', flush=True)
    with requests.get(url, stream=True, timeout=180, headers=WEB_HDRS, verify=False) as resp:
        resp.raise_for_status()
        done = 0
        with open(out_path, 'wb') as f:
            for chunk in resp.iter_content(chunk_size=2 * 1024 * 1024):
                f.write(chunk)
                done += len(chunk)
    print(f" {done/(1024*1024):.1f}MB OK")

def encode_720_and_540(inp, out_720, out_540):
    cmd = [
        'ffmpeg', '-y', '-i', str(inp),
        '-c:v', 'libx264', '-crf', '26',
        '-maxrate', '1500k', '-bufsize', '3000k',
        '-c:a', 'aac', '-b:a', '128k',
        '-movflags', '+faststart',
        '-loglevel', 'error', str(out_720)
    ]
    res = subprocess.run(cmd, capture_output=True, text=True, timeout=600)
    if res.returncode != 0:
        cmd2 = ['ffmpeg', '-y', '-i', str(inp), '-c', 'copy',
                 '-movflags', '+faststart', '-loglevel', 'error', str(out_720)]
        res2 = subprocess.run(cmd2, capture_output=True, text=True, timeout=300)
        if res2.returncode != 0:
            raise Exception(f"ffmpeg 720p failed: {res2.stderr[-200:]}")
    
    cmd3 = [
        'ffmpeg', '-y', '-i', str(out_720),
        '-vf', 'scale=-2:540',
        '-c:v', 'libx264', '-crf', '28', '-preset', 'fast',
        '-c:a', 'aac', '-b:a', '96k',
        '-movflags', '+faststart',
        '-loglevel', 'error', str(out_540)
    ]
    res3 = subprocess.run(cmd3, capture_output=True, text=True, timeout=600)
    return res3.returncode == 0

# ── Main Process ──────────────────────────────────────────────────────────────
def process_drama(cfg, r2):
    slug     = cfg['slug']
    drama_id = cfg['drama_id']
    prefix   = cfg['r2_prefix']
    
    print(f"\n{'='*65}")
    print(f"[DRAMA] {slug}")
    print(f"[ID]    {drama_id}")
    
    # 1. Detail
    print("[1/4] Fetching detail...")
    try:
        detail = get_drama_detail(drama_id)
    except Exception as e:
        print(f"  FAILED: {e}")
        return
    
    title     = detail['title']
    total_eps = detail['totalEpisodes']
    episodes  = detail.get('episodes', [])
    print(f"  Title: {title} | {total_eps} eps | finished={detail.get('isFinished', False)}")
    
    # 2. Cover
    print("[2/4] Cover...")
    cover_key   = f"{prefix}/cover.webp"
    cover_r2url = f"{R2_PUBLIC}/{cover_key}"
    
    if not r2_exists(r2, cover_key):
        try:
            cov = requests.get(detail['cover'], headers=WEB_HDRS, timeout=30, verify=False)
            cov_path = TEMP_DIR / f"{slug}_cover"
            cov_path.write_bytes(cov.content)
            r2_upload(r2, cov_path, cover_key, 'image/webp')
            cov_path.unlink()
            print(f"  Uploaded: {cover_r2url}")
        except Exception as e:
            print(f"  Cover failed (fallback to source URL): {e}")
            cover_r2url = detail['cover']
    else:
        print("  Already in R2")
    
    # 3. Register drama
    print("[3/4] Registering in backend API...")
    drama_db_id = api_get_or_create_drama(detail, slug, cover_r2url)
    if drama_db_id:
        print(f"  Drama DB ID: {drama_db_id}")
    else:
        print("  WARNING: No DB ID - will skip DB sync but will still upload to R2")
    
    # 4. Process episodes
    print(f"[4/4] Processing {len(episodes)} episodes...")
    success, skipped, failed = 0, 0, []
    
    for ep_data in episodes:
        ep_no  = ep_data['episodeNo']
        locked = ep_data.get('isLocked', False)
        
        key_720 = f"{prefix}/ep{ep_no:03d}.mp4"
        key_540 = f"{prefix}/ep{ep_no:03d}_540p.mp4"
        
        if r2_exists(r2, key_720):
            print(f"  ep{ep_no:03d}: SKIP (in R2)")
            skipped += 1
            if drama_db_id:
                url_540 = f"{R2_PUBLIC}/{key_540}" if r2_exists(r2, key_540) else None
                api_upsert_episode(drama_db_id, ep_no, f"{R2_PUBLIC}/{key_720}", url_540)
            continue
        
        # VIP lock check removed as we have a cookie now
        print(f"  ep{ep_no:03d}: processing...")
        
        video_url, ep_id = get_episode_url(drama_id, ep_no)
        if not video_url:
            print(f"  ep{ep_no:03d}: FAILED (no URL)")
            failed.append(ep_no)
            continue
        
        raw  = TEMP_DIR / f"{slug}_ep{ep_no:03d}_raw.mp4"
        o720 = TEMP_DIR / f"{slug}_ep{ep_no:03d}_720p.mp4"
        o540 = TEMP_DIR / f"{slug}_ep{ep_no:03d}_540p.mp4"
        
        try:
            download_mp4(video_url, raw, f"ep{ep_no:03d}")
            
            print(f"    Encoding...", end='', flush=True)
            has_540 = encode_720_and_540(raw, o720, o540)
            print(" OK")
            raw.unlink(missing_ok=True)
            
            print(f"    Upload 720p...", end='', flush=True)
            url_720 = r2_upload(r2, o720, key_720)
            print(f" OK")
            
            url_540_r2 = None
            if has_540 and o540.exists():
                print(f"    Upload 540p...", end='', flush=True)
                url_540_r2 = r2_upload(r2, o540, key_540)
                print(f" OK")
            
            if drama_db_id:
                ok = api_upsert_episode(drama_db_id, ep_no, url_720, url_540_r2)
                print(f"    DB: {'OK' if ok else 'FAILED'}")
            
            success += 1
            
        except Exception as e:
            print(f"\n  ep{ep_no:03d}: ERROR: {e}")
            failed.append(ep_no)
        finally:
            for p in [raw, o720, o540]:
                try:
                    if p.exists(): p.unlink()
                except:
                    pass
    
    # Update total in backend
    if drama_db_id and success > 0:
        free_count = sum(1 for e in episodes if not e.get('isLocked'))
        api_update_drama(drama_db_id, free_count)
    
    print(f"\n  --- Summary: {slug} ---")
    print(f"  OK: {success} | Skip: {skipped} | Fail: {len(failed)} {failed if failed else ''}")


def main():
    print("[START] NetshortV2 Scraper - KingShort Pipeline")
    print(f"[INFO] {len(TARGET_DRAMAS)} dramas queued")
    print()
    
    # Wait for API to be ready (after deployment)
    print("[CHECK] Backend API health...")
    r = requests.get(f"{API_BASE}/health", timeout=10)
    if r.ok:
        print(f"  Backend OK: {r.status_code}")
    else:
        print(f"  Backend WARNING: {r.status_code}")
    
    r2 = get_r2()
    print("[R2] Connected")
    
    for cfg in TARGET_DRAMAS:
        process_drama(cfg, r2)
    
    print(f"\n{'='*65}")
    print("[DONE] ALL DRAMAS PROCESSED!")

if __name__ == "__main__":
    main()
