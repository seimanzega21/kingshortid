#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Netshort V2 Scraper - KingShort Pipeline (Auto-Discovery)
======================================================
Automatically discovers all dramas from NetshortV2 feeds,
downloads episodes using VIP cookie, transcodes to 720p/540p,
uploads to R2, and syncs to KingShort via API.
"""
import sys
import requests
import boto3
import subprocess
import time
import json
import tempfile
import urllib3
import re
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

# ── Helpers ───────────────────────────────────────────────────────────────────
def slugify(text):
    text = text.lower()
    text = re.sub(r'[^a-z0-9]+', '-', text)
    return text.strip('-')

# ── R2 ────────────────────────────────────────────────────────────────────────
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

# ── Vidrama API ───────────────────────────────────────────────────────────────
def discover_dramas():
    """Fetches all dramas from netshortv2 feeds."""
    found = []
    page = 1
    max_pages = 20
    while page <= max_pages:
        print(f"[DISCOVER] Page {page}...", flush=True)
        url = f"{VIDRAMA_API}/feed/{page}?lang=id_ID"
        try:
            r = requests.get(url, headers=WEB_HDRS, timeout=15, verify=False)
            if not r.ok: break
            items = r.json().get('data', [])
            if not items: break
            for it in items:
                print(f"  - Found: {it.get('title')}", flush=True)
                found.append({
                    'title': it.get('title'),
                    'drama_id': it.get('id'),
                    'slug': slugify(it.get('title'))
                })
            page += 1
        except: break
    return found

def get_drama_detail(drama_id):
    url = f"{VIDRAMA_API}/detail/{drama_id}?lang=id_ID"
    r = requests.get(url, headers=WEB_HDRS, timeout=15, verify=False)
    return r.json()['data']

def get_episode_url(drama_id, ep_no, retries=3):
    url = f"{VIDRAMA_API}/episode/{drama_id}/{ep_no}?lang=id_ID"
    for attempt in range(retries):
        try:
            r = requests.get(url, headers=WEB_HDRS, timeout=15, verify=False)
            data = r.json()
            if data.get('code') == 200:
                videos = data['data'].get('videos', [])
                ep_id  = data['data'].get('episodeId', '')
                for q in ['720p', '1080p', '540p']:
                    for v in videos:
                        if v.get('quality') == q: return v['url'], ep_id
                if videos: return videos[0]['url'], ep_id
        except: time.sleep(2)
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
        'country': 'China', 'language': 'Indonesia',
        'status': 'completed' if detail.get('isFinished') else 'ongoing',
        'isActive': False,
    }
    r = requests.post(f"{API_BASE}/api/admin/dramas", headers=ADMIN_HDR, json=payload, timeout=20)
    return r.json().get('id') if r.ok else None

def api_upsert_episode(drama_db_id, ep_no, url_720, url_540=None):
    payload = {'episodeNumber': ep_no, 'title': f'Episode {ep_no}', 'videoUrl': url_720, 'isActive': False}
    if url_540: payload['videoUrl540p'] = url_540
    r = requests.post(f"{API_BASE}/api/admin/dramas/{drama_db_id}/episodes", headers=ADMIN_HDR, json=payload, timeout=20)
    return r.ok

# ── Processing ───────────────────────────────────────────────────────────────
def encode_720_and_540(inp, out_720, out_540):
    cmd = ['ffmpeg', '-y', '-i', str(inp), '-c:v', 'libx264', '-crf', '26', '-maxrate', '1500k', '-bufsize', '3000k',
           '-c:a', 'aac', '-b:a', '128k', '-movflags', '+faststart', '-loglevel', 'error', str(out_720)]
    res = subprocess.run(cmd, timeout=600)
    if res.returncode != 0: return False
    cmd3 = ['ffmpeg', '-y', '-i', str(out_720), '-vf', 'scale=-2:540', '-c:v', 'libx264', '-crf', '28', '-preset', 'fast',
            '-c:a', 'aac', '-b:a', '96k', '-movflags', '+faststart', '-loglevel', 'error', str(out_540)]
    return subprocess.run(cmd3, timeout=600).returncode == 0

def process_drama(cfg, r2):
    slug, drama_id = cfg['slug'], cfg['drama_id']
    prefix = f"netshortv2/{slug}"
    print(f"\n{'='*65}\n[DRAMA] {slug} ({drama_id})")
    
    try: detail = get_drama_detail(drama_id)
    except: return
    
    cover_key = f"{prefix}/cover.webp"
    cover_url = f"{R2_PUBLIC}/{cover_key}"
    if not r2_exists(r2, cover_key):
        try:
            cov = requests.get(detail['cover'], headers=WEB_HDRS, timeout=30, verify=False)
            p = TEMP_DIR / f"{slug}_cov"
            p.write_bytes(cov.content)
            r2_upload(r2, p, cover_key, 'image/webp')
            p.unlink()
        except: cover_url = detail['cover']
    
    episodes = detail.get('episodes', [])
    # Temporary list to hold episode data before DB sync
    ready_episodes = []
    
    for ep in episodes:
        no = ep['episodeNo']
        k720, k540 = f"{prefix}/ep{no:03d}.mp4", f"{prefix}/ep{no:03d}_540p.mp4"
        
        # Check if already in R2
        is_in_r2 = r2_exists(r2, k720)
        
        if is_in_r2:
            print(f"  ep{no:03d}: ALREADY in R2", flush=True)
            ready_episodes.append({'no': no, 'u720': f"{R2_PUBLIC}/{k720}", 'u540': f"{R2_PUBLIC}/{k540}" if r2_exists(r2, k540) else None})
            continue
        
        # Process new episode
        print(f"  ep{no:03d}: downloading & transcoding...", flush=True)
        vurl, _ = get_episode_url(drama_id, no)
        if not vurl: 
            print(f"    [WARN] No URL for ep{no}, skipping this drama for now to ensure integrity.")
            return # Abort this drama so it doesn't enter DB incomplete
        
        raw, o720, o540 = TEMP_DIR/f"{slug}_raw.mp4", TEMP_DIR/f"{slug}_720.mp4", TEMP_DIR/f"{slug}_540.mp4"
        try:
            with requests.get(vurl, stream=True, headers=WEB_HDRS, verify=False) as r:
                with open(raw, 'wb') as f:
                    for c in r.iter_content(2*1024*1024): f.write(c)
            
            if encode_720_and_540(raw, o720, o540):
                u720 = r2_upload(r2, o720, k720)
                u540 = r2_upload(r2, o540, k540) if o540.exists() else None
                ready_episodes.append({'no': no, 'u720': u720, 'u540': u540})
                print(f"    ep{no:03d}: SUCCESS", flush=True)
            else:
                print(f"    [ERROR] Ffmpeg failed for ep{no}. Aborting drama sync.")
                return
        except Exception as e: 
            print(f"    [ERROR] ep{no}: {e}")
            return
        finally:
            for p in [raw, o720, o540]:
                if p.exists(): p.unlink()

    # PHASE 2: SYNC TO DATABASE (Only if we reached here with all episodes processed)
    if len(ready_episodes) > 0:
        print(f"\n[SYNC] Registering {slug} to Database with {len(ready_episodes)} episodes...")
        db_id = api_get_or_create_drama(detail, slug, cover_url)
        if db_id:
            for rep in ready_episodes:
                api_upsert_episode(db_id, rep['no'], rep['u720'], rep['u540'])
            print(f"[SUCCESS] {slug} is now complete in Admin Panel.")
        else:
            print(f"[ERROR] Failed to register drama {slug} in DB.")
    else:
        print(f"[SKIP] No episodes processed for {slug}.")

def main():
    print("[START] NetshortV2 Scraper - Priority & Discovery Mode")
    r2 = get_r2()
    
    # 4 Priority Dramas first
    priority = [
        {'title': '(Sulih suara) Dia Kembali dari Balik Legenda', 'drama_id': '2011980833696841730', 'slug': 'dia-kembali-dari-balik-legenda'},
        {'title': 'Krisis Mineral Penuh Intrik', 'drama_id': '1996524173033156610', 'slug': 'krisis-mineral-penuh-intrik'},
        {'title': 'Permainan Hasrat Khusus Sang CEO', 'drama_id': '2045032067133079554', 'slug': 'permainan-hasrat-sang-ceo'},
        {'title': '(Sulih suara) Menantu Kerajaan dari Masa Depan', 'drama_id': '2033434071169761281', 'slug': 'menantu-kerajaan-masa-depan'},
        {'title': '(Sulih suara) Demi Putriku, Identitasku Bocor', 'drama_id': '2036701497621741570', 'slug': 'demi-putriku-identitasku-bocor'},
        {'title': 'Kode Cinta Robot', 'drama_id': '2044326309693227010', 'slug': 'kode-cinta-robot'},
        {'title': '(Sulih suara) Pemilik Kitab Pedang', 'drama_id': '2036690458087784450', 'slug': 'pemilik-kitab-pedang'},
        {'title': 'Jenderal, Masakanku Siap', 'drama_id': '2045396177699995650', 'slug': 'jenderal-masakanku-siap'},
    ]
    
    print(f"[INFO] Processing {len(priority)} Priority Dramas...")
    for d in priority:
        process_drama(d, r2)
        
    print("\n[INFO] Starting Discovery for other dramas...")
    dramas = discover_dramas()
    # Filter out priority ones from discovery to avoid double check
    priority_ids = [p['drama_id'] for p in priority]
    to_process = [d for d in dramas if d['drama_id'] not in priority_ids]
    
    print(f"[INFO] {len(to_process)} more dramas found in discovery.")
    for d in to_process:
        process_drama(d, r2)
    
    print("\n[DONE]")

if __name__ == "__main__":
    main()
