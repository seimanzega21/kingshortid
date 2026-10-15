#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Sedot 5 Drama dari Dracinema (VIP Session)
Target: Cloudflare R2 + KingShort DB + Single Local Storage (D:/Video Drama/Facebook)
"""

import sys
if sys.platform == 'win32':
    sys.stdout.reconfigure(encoding='utf-8', errors='replace')
    sys.stderr.reconfigure(encoding='utf-8', errors='replace')

import os
import json
import time
import shutil
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

TEMP_ROOT   = Path("D:/temp_scraper")
TEMP_ROOT.mkdir(parents=True, exist_ok=True)

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
def get_or_create_drama(meta):
    title = meta['title']
    slug = meta['slug']
    cover_r2_url = f"{R2_PUBLIC}/{meta['prefix']}/cover.webp"

    print(f"\n[DB] Memeriksa & Mendaftarkan Drama '{title}' ke KingShort...")
    try:
        r = requests.get(f"{API_BASE}/dramas?limit=1000&includeInactive=true", headers=ADMIN_HDR, timeout=15)
        if r.ok:
            for d in r.json().get('dramas', []):
                if d.get('title', '').strip().lower() == title.lower():
                    print(f"  -> Drama sudah ada di database (ID: {d['id']})")
                    return d['id']
    except Exception as e:
        print(f"  [WARN] Gagal cek drama di DB: {e}")

    payload = {
        'title': title,
        'description': meta.get('description') or title,
        'cover': cover_r2_url,
        'genres': meta.get('genres', ['Drama']),
        'totalEpisodes': meta['total_eps'],
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

def download_video(url, out_mp4):
    """Download direct mp4 or HLS m3u8 stream using ffmpeg"""
    cmd = [
        'ffmpeg', '-y',
        '-headers', 'User-Agent: Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36\r\nReferer: https://www.dracinema.com/\r\nOrigin: https://www.dracinema.com\r\n',
        '-i', url,
        '-c', 'copy',
        '-movflags', '+faststart',
        '-loglevel', 'error',
        str(out_mp4)
    ]
    res = subprocess.run(cmd, timeout=300)
    return res.returncode == 0 and os.path.exists(out_mp4) and os.path.getsize(out_mp4) > 100 * 1024

def ensure_cover(meta, temp_dir):
    cover_key = f"{meta['prefix']}/cover.webp"
    if r2_exists(cover_key):
        print(f"  -> [R2] Cover already exists for '{meta['title']}'.")
        return
    print(f"  -> [R2] Mengunduh dan mengupload cover untuk '{meta['title']}'...")
    try:
        r = requests.get(meta['cover_url'], timeout=15)
        if r.ok:
            tmp_cov = temp_dir / "cover.webp"
            tmp_cov.write_bytes(r.content)
            r2_upload(tmp_cov, cover_key, 'image/webp')
            tmp_cov.unlink(missing_ok=True)
            print("  -> [R2] Cover uploaded successfully!")
    except Exception as e:
        print(f"  -> [WARN] Cover error: {e}")

# ── PROCESS EPISODE ───────────────────────────────────────────────────────────
def process_episode(drama_id, meta, ep_num, video_url, temp_dir):
    prefix = meta['prefix']
    k720 = f"{prefix}/ep{ep_num:03d}.mp4"
    k540 = f"{prefix}/ep{ep_num:03d}_540p.mp4"
    local_file = meta['local_dir'] / f"ep{ep_num:03d}.mp4"

    # 1. Cek apakah sudah ada di R2
    if r2_exists(k720) and r2_exists(k540):
        print(f"  -> Ep {ep_num:02d}: Sudah ada di R2. Menghubungkan ke DB...", end="", flush=True)
        u720 = f"{R2_PUBLIC}/{k720}"
        u540 = f"{R2_PUBLIC}/{k540}"
        upsert_episode(drama_id, ep_num, u720, u540)
        # Cek local
        if not local_file.exists():
            try:
                s3.download_file(R2_BUCKET, k720, str(local_file))
            except Exception:
                pass
        print(" [OK]")
        return True

    print(f"  -> Ep {ep_num:02d}: Mendownload dari Dracinema...", end="", flush=True)
    raw_mp4 = temp_dir / f"raw_{ep_num:03d}.mp4"
    out_540 = temp_dir / f"out540_{ep_num:03d}.mp4"

    if not download_video(video_url, raw_mp4):
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

# ── PROCESS ONE DRAMA ────────────────────────────────────────────────────────
def process_drama(meta, urls_data):
    title = meta['title']
    print("\n" + "=" * 60)
    print(f"MEMULAI SEDOT: {title} ({meta['total_eps']} Episode)")
    print("=" * 60)

    temp_dir = TEMP_ROOT / meta['slug']
    temp_dir.mkdir(parents=True, exist_ok=True)

    # Pastikan local dir ada
    meta['local_dir'].mkdir(parents=True, exist_ok=True)

    # Ensure Cover
    ensure_cover(meta, temp_dir)

    # Get / Create Drama in DB
    drama_id = get_or_create_drama(meta)
    if not drama_id:
        print(f"[ERROR] Gagal mendapatkan ID drama DB untuk {title}.")
        return

    success = 0
    for item in urls_data:
        ep = item['ep']
        url = item.get('url') or item.get('u720')
        if not url:
            print(f"  -> Ep {ep:02d}: URL tidak valid. Melewati...")
            continue
        if process_episode(drama_id, meta, ep, url, temp_dir):
            success += 1

    print(f"\n[HASIL] Selesai {title}: {success}/{len(urls_data)} episode.")
    print(f"  - Cloudflare R2: {R2_PUBLIC}/{meta['prefix']}/")
    print(f"  - Local Storage (Single Location): {meta['local_dir']}")

# ── MAIN ─────────────────────────────────────────────────────────────────────
def main():
    with open(Path(__file__).parent / "dramas_metadata.json", "r", encoding="utf-8") as f:
        meta_all = json.load(f)

    # Process all available dramas
    order = [
        ("drama1", "drama1_urls.json"),
        ("drama2", "drama2_urls.json"),
        ("drama3", "drama3_urls.json"),
        ("drama4", "drama4_urls.json"),
        ("drama5", "drama5_urls.json")
    ]

    for key, filename in order:
        fpath = Path(__file__).parent / filename
        if not fpath.exists():
            print(f"\n[SKIP] File {filename} belum siap. Melanjutkan drama lainnya...")
            continue

        meta = meta_all.get(key)
        if not meta:
            continue
        meta['local_dir'] = Path(meta['local_dir'])

        with open(fpath, "r", encoding="utf-8") as fp:
            urls = json.load(fp)

        process_drama(meta, urls)

    print("\n" + "=" * 60)
    print("ALL BATCH COMPLETED!")
    print("=" * 60)

if __name__ == "__main__":
    main()

