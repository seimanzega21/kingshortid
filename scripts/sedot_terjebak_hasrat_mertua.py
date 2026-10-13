#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Sedot Drama: Terjebak Hasrat Mertua (Netshort / Netshort V2)
- Provider: netshortv2
- Source ID: 2090382057861120001
- Episodes: 30
- Target: Cloudflare R2 + KingShort DB + Local Storage
"""

import sys
if sys.platform == 'win32':
    sys.stdout.reconfigure(encoding='utf-8', errors='replace')
    sys.stderr.reconfigure(encoding='utf-8', errors='replace')

import os
import json
import time
import shutil
import tempfile
import subprocess
import requests
import urllib3
import boto3
from pathlib import Path
from botocore.config import Config

urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

# ── CONFIGURATION ─────────────────────────────────────────────────────────────
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
}

DRAMA_ID    = '2090382057861120001'
SLUG        = 'terjebak-hasrat-mertua'
TITLE       = 'Terjebak Hasrat Mertua'
TOTAL_EPS   = 30
PREFIX      = f"netshortv2/{SLUG}"

CACHE_FILE  = Path(__file__).parent / f"cache_{SLUG}.json"
TEMP_DIR    = Path("D:/temp_scraper") / SLUG
TEMP_DIR.mkdir(parents=True, exist_ok=True)

LOCAL_DIR_FB = Path("D:/Video Drama/Facebook") / TITLE
LOCAL_DIR_VD = Path("D:/Video Drama") / TITLE
LOCAL_DIR_FB.mkdir(parents=True, exist_ok=True)
LOCAL_DIR_VD.mkdir(parents=True, exist_ok=True)

FFMPEG_BIN = r'C:\ProgramData\chocolatey\bin\ffmpeg.exe'
if not os.path.exists(FFMPEG_BIN):
    FFMPEG_BIN = shutil.which('ffmpeg') or 'ffmpeg'

# ── R2 CLIENT ─────────────────────────────────────────────────────────────────
s3 = boto3.client('s3', endpoint_url=R2_ENDPOINT,
                  aws_access_key_id=R2_KEY_ID, aws_secret_access_key=R2_SECRET,
                  config=Config(signature_version='s3v4', retries={'max_attempts': 3}),
                  region_name='auto')

def r2_exists(key):
    try:
        s3.head_object(Bucket=R2_BUCKET, Key=key)
        return True
    except:
        return False

def r2_upload(local_path, key, content_type='video/mp4'):
    s3.upload_file(str(local_path), R2_BUCKET, key, ExtraArgs={'ContentType': content_type},
                   Config=boto3.s3.transfer.TransferConfig(multipart_threshold=30*1024*1024, multipart_chunksize=10*1024*1024))
    return f"{R2_PUBLIC}/{key}"

# ── DATABASE HELPERS ─────────────────────────────────────────────────────────
def get_or_create_drama(detail):
    print("\n[1/3] Memeriksa & Mendaftarkan Drama ke Database KingShort...")
    try:
        r = requests.get(f"{API_BASE}/dramas?limit=1000&includeInactive=true", headers=ADMIN_HDR, timeout=15)
        if r.ok:
            for d in r.json().get('dramas', []):
                if d.get('title', '').strip().lower() == TITLE.lower() or d.get('sourceMovieId') == DRAMA_ID:
                    print(f"  -> Drama sudah ada di database (ID: {d['id']}, isActive: {d.get('isActive')})")
                    return d['id']
    except Exception as e:
        print(f"  [WARN] Gagal cek drama di DB: {e}")

    cover_r2_url = f"{R2_PUBLIC}/{PREFIX}/cover.webp"
    payload = {
        'title': TITLE,
        'description': detail.get('description', TITLE),
        'cover': cover_r2_url,
        'genres': detail.get('labels', ['Moral dan Etika', 'Romantis Urban']) or ['Drama'],
        'totalEpisodes': TOTAL_EPS,
        'isComplete': True,
        'country': 'China',
        'language': 'Indonesia',
        'status': 'completed',
        'isActive': False,  # Pending review
        'providerName': 'netshort',
        'sourceMovieId': DRAMA_ID
    }

    res = requests.post(f"{API_BASE}/admin/dramas", headers=ADMIN_HDR, json=payload, timeout=20)
    if res.ok:
        did = res.json().get('id')
        print(f"  [✓] Drama berhasil didaftarkan ke DB! ID: {did} (Status: Pending Review)")
        return did
    else:
        raise Exception(f"Gagal membuat drama di DB: {res.status_code} - {res.text}")

def get_existing_db_episodes(drama_db_id):
    try:
        r = requests.get(f"{API_BASE}/dramas/{drama_db_id}/episodes", timeout=15)
        if r.ok:
            eps = r.json()
            return {e.get('episodeNumber'): e.get('id') for e in eps if 'episodeNumber' in e}
    except Exception as e:
        print(f"  [WARN] Gagal membaca episode dari DB: {e}")
    return {}

def upsert_episode(drama_id, ep_no, u720, u540, sub_url=None):
    payload = {
        'episodeNumber': ep_no,
        'title': f'Episode {ep_no}',
        'videoUrl': u720,
        'videoUrl540p': u540,
        'isActive': True
    }
    ep_id = None
    for attempt in range(3):
        try:
            r = requests.post(f"{API_BASE}/admin/dramas/{drama_id}/episodes", headers=ADMIN_HDR, json=payload, timeout=15)
            if r.ok:
                ep_id = r.json().get('id')
                break
        except:
            time.sleep(1)

    if ep_id and sub_url:
        sub_payload = {
            'language': 'indonesia',
            'label': 'Indonesia',
            'url': sub_url,
            'isDefault': True
        }
        for attempt in range(3):
            try:
                r_sub = requests.post(f"{API_BASE}/episodes/{ep_id}/subtitles", headers=ADMIN_HDR, json=sub_payload, timeout=10)
                if r_sub.ok:
                    break
            except:
                time.sleep(1)

    return ep_id

# ── COVER PROCESSOR ──────────────────────────────────────────────────────────
def process_cover(cover_src):
    cover_key = f"{PREFIX}/cover.webp"
    if r2_exists(cover_key):
        print(f"  [✓] Cover sudah ada di R2: {R2_PUBLIC}/{cover_key}")
        return f"{R2_PUBLIC}/{cover_key}"

    print(f"  [*] Mengunggah Cover ke R2...")
    tmp_cover = TEMP_DIR / "cover_raw.webp"
    try:
        r = requests.get(cover_src, headers=WEB_HDRS, timeout=20, verify=False)
        tmp_cover.write_bytes(r.content)
        r2_upload(tmp_cover, cover_key, 'image/webp')
        print(f"  [✓] Cover berhasil diunggah: {R2_PUBLIC}/{cover_key}")
        return f"{R2_PUBLIC}/{cover_key}"
    finally:
        if tmp_cover.exists():
            tmp_cover.unlink()

# ── METADATA & STREAM URL CACHER ─────────────────────────────────────────────
def load_cached_episodes():
    if CACHE_FILE.exists():
        try:
            with open(CACHE_FILE, 'r', encoding='utf-8') as f:
                return json.load(f)
        except:
            pass
    return {}

def save_cached_episodes(cache):
    try:
        with open(CACHE_FILE, 'w', encoding='utf-8') as f:
            json.dump(cache, f, indent=2, ensure_ascii=False)
    except:
        pass

def fetch_stream_info(ep_no, retries=6):
    url = f"{VIDRAMA_API}/episode/{DRAMA_ID}/{ep_no}?lang=id_ID"
    for attempt in range(retries):
        try:
            r = requests.get(url, headers=WEB_HDRS, timeout=15, verify=False)
            if r.status_code == 200:
                data = r.json()
                if data.get('code') == 200:
                    ep_data = data.get('data', {})
                    videos = ep_data.get('videos', [])
                    subs = ep_data.get('subtitles', [])

                    vurl = None
                    for q in ['720p', '1080p', '540p']:
                        for v in videos:
                            if v.get('quality') == q:
                                vurl = v.get('url')
                                break
                        if vurl: break
                    if not vurl and videos:
                        vurl = videos[0].get('url')

                    sub_url = None
                    for s in subs:
                        if s.get('language') in ['id_ID', 'indonesia', 'in']:
                            sub_url = s.get('url')
                            break
                    if not sub_url and subs:
                        sub_url = subs[0].get('url')

                    if vurl:
                        return {'video_url': vurl, 'sub_url': sub_url}
            elif r.status_code == 500:
                # Upstream error 401 / rate limit -> backoff
                wait_sec = 2.5 * (attempt + 1)
                time.sleep(wait_sec)
                continue
        except Exception as e:
            time.sleep(2)
        time.sleep(1.5)
    return None

def build_all_stream_cache():
    print(f"\n[2/3] Membangun Cache Stream URL Semua Episode (1 s/d {TOTAL_EPS})...")
    cache = load_cached_episodes()
    missing_eps = [ep for ep in range(1, TOTAL_EPS + 1) if str(ep) not in cache]

    if not missing_eps:
        print(f"  [✓] Semua {TOTAL_EPS} episode sudah ada di cache!")
        return cache

    print(f"  -> Perlu mengambil {len(missing_eps)} episode dari Vidrama API...")
    for idx, ep in enumerate(missing_eps, 1):
        print(f"     [{idx}/{len(missing_eps)}] Mengambil info Ep {ep:02d}...", end="", flush=True)
        info = fetch_stream_info(ep)
        if info:
            cache[str(ep)] = info
            save_cached_episodes(cache)
            print(f" [OK] (Video: OK, Sub: {'OK' if info.get('sub_url') else 'None'})")
        else:
            print(f" [GAGAL]")
        time.sleep(2.0)

    save_cached_episodes(cache)
    return cache

# ── EPISODE PROCESSOR ─────────────────────────────────────────────────────────
def process_single_episode(ep_no, stream_info, drama_db_id, existing_db_eps):
    k720 = f"{PREFIX}/ep{ep_no:03d}.mp4"
    k540 = f"{PREFIX}/ep{ep_no:03d}_540p.mp4"
    ksub = f"{PREFIX}/ep{ep_no:03d}.vtt"
    u720_public = f"{R2_PUBLIC}/{k720}"
    u540_public = f"{R2_PUBLIC}/{k540}"
    sub_public  = f"{R2_PUBLIC}/{ksub}"

    local_fb = LOCAL_DIR_FB / f"ep{ep_no:03d}.mp4"
    local_vd = LOCAL_DIR_VD / f"ep{ep_no:03d}.mp4"

    # Fast resume jika sudah ada di R2
    if r2_exists(k720):
        if ep_no not in existing_db_eps:
            has_sub = r2_exists(ksub)
            upsert_episode(drama_db_id, ep_no, u720_public, u540_public, sub_public if has_sub else None)

        if not local_fb.exists() or not local_vd.exists():
            try:
                r_dl = requests.get(u720_public, stream=True, timeout=60)
                if r_dl.ok:
                    target = local_fb if not local_fb.exists() else local_vd
                    with open(target, 'wb') as f:
                        for chunk in r_dl.iter_content(1024*1024):
                            if chunk: f.write(chunk)
                    if not local_vd.exists() and local_fb.exists():
                        shutil.copy2(local_fb, local_vd)
                    elif not local_fb.exists() and local_vd.exists():
                        shutil.copy2(local_vd, local_fb)
            except:
                pass
        print(f"  [Ep {ep_no:02d}/{TOTAL_EPS:02d}] SUDAH ADA di R2 & DB (Resume OK)")
        return True

    if not stream_info:
        print(f"  [Ep {ep_no:02d}/{TOTAL_EPS:02d}] [X] Stream info tidak tersedia!")
        return False

    vurl = stream_info.get('video_url')
    sub_url_raw = stream_info.get('sub_url')

    raw_file = TEMP_DIR / f"raw_{ep_no:03d}.mp4"
    f720     = TEMP_DIR / f"ep_{ep_no:03d}_720.mp4"
    f540     = TEMP_DIR / f"ep_{ep_no:03d}_540.mp4"

    try:
        # A. Upload subtitle ke R2 jika ada
        has_sub_uploaded = False
        if sub_url_raw and not r2_exists(ksub):
            try:
                r_sub = requests.get(sub_url_raw, headers=WEB_HDRS, timeout=15, verify=False)
                if r_sub.ok and len(r_sub.content) > 20:
                    s3.put_object(Bucket=R2_BUCKET, Key=ksub, Body=r_sub.content, ContentType='text/vtt')
                    has_sub_uploaded = True
            except Exception as e:
                pass
        elif r2_exists(ksub):
            has_sub_uploaded = True

        # B. Download video raw dari CDN
        print(f"  [Ep {ep_no:02d}/{TOTAL_EPS:02d}] Mendownload video...", end="", flush=True)
        dl_ok = False
        for dl_attempt in range(3):
            try:
                with requests.get(vurl, stream=True, headers=WEB_HDRS, timeout=90, verify=False) as r_dl:
                    if r_dl.status_code == 200:
                        with open(raw_file, 'wb') as f:
                            for chunk in r_dl.iter_content(2*1024*1024):
                                if chunk: f.write(chunk)
                        if raw_file.exists() and raw_file.stat().st_size > 100000:
                            dl_ok = True
                            break
            except:
                time.sleep(2)

        if not dl_ok:
            print(" [GAGAL DOWNLOAD]")
            return False

        print(f" ({raw_file.stat().st_size / (1024*1024):.1f} MB) -> Remux & Scale 540p...", end="", flush=True)

        # C. 720p Remux (-c copy + faststart)
        cmd_720 = [
            FFMPEG_BIN, '-y',
            '-i', str(raw_file),
            '-c', 'copy',
            '-movflags', '+faststart',
            '-loglevel', 'error',
            str(f720)
        ]
        res_720 = subprocess.run(cmd_720)
        if res_720.returncode != 0 or not f720.exists() or f720.stat().st_size < 100000:
            cmd_720_fb = [
                FFMPEG_BIN, '-y',
                '-i', str(raw_file),
                '-c:v', 'libx264', '-crf', '26', '-preset', 'veryfast',
                '-c:a', 'aac', '-b:a', '128k',
                '-movflags', '+faststart',
                '-loglevel', 'error',
                str(f720)
            ]
            subprocess.run(cmd_720_fb, check=True)

        # D. 540p Scale
        cmd_540 = [
            FFMPEG_BIN, '-y',
            '-i', str(f720),
            '-vf', 'scale=-2:540',
            '-c:v', 'libx264', '-crf', '28', '-preset', 'ultrafast',
            '-c:a', 'copy',
            '-movflags', '+faststart',
            '-loglevel', 'error',
            str(f540)
        ]
        subprocess.run(cmd_540, check=True)

        # E. Upload ke Cloudflare R2
        print(" Upload R2...", end="", flush=True)
        r2_upload(f720, k720, 'video/mp4')
        r2_upload(f540, k540, 'video/mp4')

        # F. Daftarkan ke Database KingShort
        upsert_episode(drama_db_id, ep_no, u720_public, u540_public, sub_public if has_sub_uploaded else None)

        # G. Simpan Backup Lokal
        shutil.copy2(f720, local_fb)
        shutil.copy2(f720, local_vd)

        print(" [✓ SUKSES]")
        return True

    except Exception as e:
        print(f" [ERROR: {e}]")
        return False
    finally:
        for p in [raw_file, f720, f540]:
            if p.exists():
                try: p.unlink()
                except: pass

# ── MAIN EXECUTION ────────────────────────────────────────────────────────────
def main():
    print("=" * 65)
    print(f"🚀 SEDOT NETSHORT: {TITLE.upper()}")
    print(f"   Source ID: {DRAMA_ID} | Total Episodes: {TOTAL_EPS}")
    print("=" * 65)

    detail_url = f"{VIDRAMA_API}/detail/{DRAMA_ID}?lang=id_ID"
    r_detail = requests.get(detail_url, headers=WEB_HDRS, timeout=20, verify=False)
    if not r_detail.ok or r_detail.json().get('code') != 200:
        print("[ERROR] Gagal mengambil metadata drama dari Vidrama!")
        sys.exit(1)

    detail = r_detail.json()['data']

    process_cover(detail['cover'])
    drama_db_id = get_or_create_drama(detail)
    existing_db_eps = get_existing_db_episodes(drama_db_id)

    cache = build_all_stream_cache()

    print(f"\n[3/3] Memulai Proses Download, Transcode, Upload R2 & Simpan Lokal...")
    success_count = 0
    failed_count = 0

    for ep_no in range(1, TOTAL_EPS + 1):
        info = cache.get(str(ep_no))
        if not info:
            print(f"  [Ep {ep_no:02d}/{TOTAL_EPS:02d}] Mengambil ulang info stream...", end="", flush=True)
            info = fetch_stream_info(ep_no, retries=5)
            if info:
                cache[str(ep_no)] = info
                save_cached_episodes(cache)
                print(" [OK]")
            else:
                print(" [GAGAL]")

        ok = process_single_episode(ep_no, info, drama_db_id, existing_db_eps)
        if ok:
            success_count += 1
        else:
            failed_count += 1

    print("\n" + "=" * 65)
    print(f"🎉 SELESAI! Hasil Sedot:")
    print(f"   Drama: {TITLE}")
    print(f"   Database ID: {drama_db_id} (Status: Pending Review / isActive=False)")
    print(f"   Sukses: {success_count}/{TOTAL_EPS}")
    print(f"   Gagal: {failed_count}/{TOTAL_EPS}")
    print(f"   Folder Lokal 1: {LOCAL_DIR_FB}")
    print(f"   Folder Lokal 2: {LOCAL_DIR_VD}")
    print("=" * 65)

if __name__ == '__main__':
    main()
