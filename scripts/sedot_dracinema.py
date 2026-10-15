#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Sedot Drama: (Sulih Suara) Ayah Miliarderku Akhirnya Menemukanku
Provider: Dracinema (dracinema.com)
Source MovieKey: sulih-suara-ayah-miliarderku-akhirnya-menemukanku-id_161001644384
Target: Cloudflare R2 + KingShort DB + Local Storage
"""

import sys
if sys.platform == 'win32':
    sys.stdout.reconfigure(encoding='utf-8', errors='replace')
    sys.stderr.reconfigure(encoding='utf-8', errors='replace')

import os
import json
import time
import shutil
import base64
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

DRACINEMA_API_KEY = 'xb3MdwdLrZrpaDXvrLLwfP=='
DRACINEMA_BASE    = 'https://www.dracinema.com'
MOVIE_KEY         = 'sulih-suara-ayah-miliarderku-akhirnya-menemukanku-id_161001644384'
TITLE             = '(Sulih Suara) Ayah Miliarderku Akhirnya Menemukanku'
SLUG              = 'ayah-miliarderku-akhirnya-menemukanku'
TOTAL_EPS         = 30
PREFIX            = f"dracinema/{SLUG}"

COVER_IMG_SRC     = 'https://img.mebilu.com/EBd_2QahU9CU2lrYFkQyKtwU5BfXm8XKbKhAAAXcO9GzekWDAPFx__bSVQTooVoZo9Yu.webp'
DESCRIPTION       = 'Dibuang ke tahanan remaja, Astra diselamatkan ayah kandung miliardernya, Constantine Kingsley. Kembali ke dunia elit, ia dihujani jebakan dari musuh sekolah hingga tim hoki. Saat turnamen nasional dimulai, sebuah badai besar siap mengubah segalanya dan membungkam mereka semua!'

TEMP_DIR    = Path("D:/temp_scraper") / SLUG
TEMP_DIR.mkdir(parents=True, exist_ok=True)

LOCAL_DIR = Path("D:/Video Drama/Facebook") / TITLE
LOCAL_DIR.mkdir(parents=True, exist_ok=True)

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
def get_or_create_drama():
    print("\n[DB] Memeriksa & Mendaftarkan Drama ke KingShort...")
    try:
        r = requests.get(f"{API_BASE}/dramas?limit=1000&includeInactive=true", headers=ADMIN_HDR, timeout=15)
        if r.ok:
            for d in r.json().get('dramas', []):
                if d.get('title', '').strip().lower() == TITLE.lower():
                    print(f"  -> Drama sudah ada di database (ID: {d['id']})")
                    return d['id']
    except Exception as e:
        print(f"  [WARN] Gagal cek drama di DB: {e}")

    cover_r2_url = f"{R2_PUBLIC}/{PREFIX}/cover.webp"
    payload = {
        'title': TITLE,
        'description': DESCRIPTION,
        'cover': cover_r2_url,
        'genres': ['Miliarder', 'Drama Keluarga', 'Sulih Suara'],
        'totalEpisodes': TOTAL_EPS,
        'country': 'China',
        'language': 'Indonesia',
        'status': 'completed',
        'isActive': False  # Pending verifikasi admin
    }
    try:
        r = requests.post(f"{API_BASE}/admin/dramas", headers=ADMIN_HDR, json=payload, timeout=20)
        if r.ok:
            new_id = r.json().get('id')
            print(f"  -> Berhasil membuat drama di DB (ID: {new_id})")
            return new_id
        else:
            print(f"  [ERROR] Gagal buat drama di DB: {r.status_code} {r.text}")
    except Exception as e:
        print(f"  [ERROR] Exception creating drama in DB: {e}")
    return None

def upsert_episode(drama_id, ep_num, url_720, url_540=None):
    payload = {
        'episodeNumber': ep_num,
        'title': f'Episode {ep_num}',
        'videoUrl': url_720,
        'isActive': True
    }
    if url_540:
        payload['videoUrl540p'] = url_540

    try:
        r = requests.post(f"{API_BASE}/admin/dramas/{drama_id}/episodes", headers=ADMIN_HDR, json=payload, timeout=20)
        return r.ok
    except Exception as e:
        print(f"      [WARN] DB upsert ep {ep_num} error: {e}")
        return False

# ── VIDEO HELPERS ─────────────────────────────────────────────────────────────
def encode_540p(in_file, out_540p):
    cmd = [
        'ffmpeg', '-y', '-i', str(in_file),
        '-vf', 'scale=-2:540',
        '-c:v', 'libx264', '-crf', '28', '-preset', 'fast',
        '-c:a', 'aac', '-b:a', '96k',
        '-movflags', '+faststart',
        '-loglevel', 'error',
        str(out_540p)
    ]
    return subprocess.run(cmd).returncode == 0

def download_hls_stream(m3u8_url, out_mp4):
    cmd = [
        'ffmpeg', '-y',
        '-headers', 'User-Agent: Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36\r\nReferer: https://www.dracinema.com/\r\nOrigin: https://www.dracinema.com\r\n',
        '-i', m3u8_url,
        '-c', 'copy',
        '-movflags', '+faststart',
        '-loglevel', 'error',
        str(out_mp4)
    ]
    res = subprocess.run(cmd, timeout=300)
    return res.returncode == 0 and os.path.exists(out_mp4) and os.path.getsize(out_mp4) > 100 * 1024

# ── COVER UPLOAD ──────────────────────────────────────────────────────────────
def ensure_cover():
    cover_key = f"{PREFIX}/cover.webp"
    if r2_exists(cover_key):
        print("  -> [R2] Cover already exists.")
        return
    print("  -> [R2] Mengunduh dan mengupload cover...")
    try:
        r = requests.get(COVER_IMG_SRC, timeout=15)
        if r.ok:
            tmp_cov = TEMP_DIR / "cover.webp"
            tmp_cov.write_bytes(r.content)
            r2_upload(tmp_cov, cover_key, 'image/webp')
            tmp_cov.unlink(missing_ok=True)
            print("  -> [R2] Cover uploaded successfully!")
    except Exception as e:
        print(f"  -> [WARN] Cover error: {e}")

# ── PROCESS EPISODE ───────────────────────────────────────────────────────────
def process_episode(drama_id, ep_num, m3u8_url):
    k720 = f"{PREFIX}/ep{ep_num:03d}.mp4"
    k540 = f"{PREFIX}/ep{ep_num:03d}_540p.mp4"
    local_file = LOCAL_DIR / f"ep{ep_num:03d}.mp4"

    # 1. Cek apakah sudah ada di R2
    if r2_exists(k720) and r2_exists(k540):
        print(f"  -> Ep {ep_num:02d}: Sudah ada di R2. Menghubungkan ke DB...", end="", flush=True)
        u720 = f"{R2_PUBLIC}/{k720}"
        u540 = f"{R2_PUBLIC}/{k540}"
        upsert_episode(drama_id, ep_num, u720, u540)
        # Cek local
        if not local_file.exists():
            try:
                r_dl = requests.get(u720, stream=True, timeout=60)
                if r_dl.ok:
                    with open(local_file, 'wb') as f:
                        for chunk in r_dl.iter_content(chunk_size=1024*1024):
                            if chunk: f.write(chunk)
            except Exception:
                pass
        print(" [OK]")
        return True

    print(f"  -> Ep {ep_num:02d}: Mendownload dari Dracinema (HLS Decrypt)...", end="", flush=True)
    raw_mp4 = TEMP_DIR / f"raw_{ep_num:03d}.mp4"
    out_540 = TEMP_DIR / f"out540_{ep_num:03d}.mp4"

    if not download_hls_stream(m3u8_url, raw_mp4):
        print(" [GAGAL DOWNLOAD]")
        if raw_mp4.exists(): raw_mp4.unlink()
        return False

    size_mb = raw_mp4.stat().st_size / (1024 * 1024)
    print(f" ({size_mb:.1f} MB) Mengompres 540p...", end="", flush=True)

    if not encode_540p(raw_mp4, out_540):
        print(" [GAGAL 540P]")
        if raw_mp4.exists(): raw_mp4.unlink()
        if out_540.exists(): out_540.unlink()
        return False

    print(" Uploading R2...", end="", flush=True)
    u720 = r2_upload(raw_mp4, k720)
    u540 = r2_upload(out_540, k540)

    # Simpan ke folder lokal (hanya 1 tempat)
    try:
        shutil.copy2(raw_mp4, local_file)
    except Exception as e:
        print(f" [WARN local copy: {e}]", end="")

    # Upsert ke database
    upsert_episode(drama_id, ep_num, u720, u540)

    # Bersihkan file temp
    raw_mp4.unlink(missing_ok=True)
    out_540.unlink(missing_ok=True)

    print(" [SELESAI]")
    return True

# ── MAIN ─────────────────────────────────────────────────────────────────────
def main():
    print("=" * 60)
    print(f"Sedot Dracinema: {TITLE}")
    print("=" * 60)

    # 1. Pastikan cover terupload
    ensure_cover()

    # 2. Pastikan drama ada di DB
    drama_id = get_or_create_drama()
    if not drama_id:
        print("[ERROR] Tidak dapat melanjutkan tanpa ID Drama DB.")
        return

    # 3. Load url all eps dari cache/ekstraksi
    urls_file = Path(__file__).parent / "dracinema_all_urls.json"
    if not urls_file.exists():
        print(f"[ERROR] File {urls_file} tidak ditemukan.")
        return

    with open(urls_file, 'r', encoding='utf-8') as f:
        ep_urls = json.load(f)

    print(f"\n[DOWNLOAD] Memulai download {len(ep_urls)} episode yang sudah siap...")
    success = 0
    for item in ep_urls:
        ep = item['ep']
        url = item['u720']
        if process_episode(drama_id, ep, url):
            success += 1

    print(f"\n[HASIL] Berhasil memproses {success}/{len(ep_urls)} episode!")
    print(f"Video tersimpan di:")
    print(f"  - Cloudflare R2: {R2_PUBLIC}/{PREFIX}/")
    print(f"  - Local Storage: {LOCAL_DIR}")
    print("=" * 60)

if __name__ == "__main__":
    main()
