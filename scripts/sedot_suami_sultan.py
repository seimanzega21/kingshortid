#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Sedot Suami Baru Ternyata Sultan (107 Episode) - Melolo (Official Hardsub Indo)
- Stream: Direct unencrypted MP4 / decrypted Melolo stream
- Video: 720p H.264 faststart + 540p faststart
- Official Indonesian hardsub is built-in (no VTT to avoid double subtitles)
- Upload 720p & 540p to Cloudflare R2
- Upsert & activate drama + episodes in KingShort DB
- Single storage location strictly in D:\\Video Drama\\Facebook\\Suami Baru Ternyata Sultan\\
"""

import sys
if sys.platform == 'win32':
    sys.stdout.reconfigure(encoding='utf-8', errors='replace')
    sys.stderr.reconfigure(encoding='utf-8', errors='replace')

import os
import re
import json
import time
import shutil
import subprocess
import requests
import urllib3
import boto3
import concurrent.futures
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

DECRYPT_TOOL = Path("D:/kingshortid/scripts/melolo_decrypt_tool.js")

# ── R2 CLIENT ─────────────────────────────────────────────────────────────────
s3 = boto3.client('s3', endpoint_url=R2_ENDPOINT,
                  aws_access_key_id=R2_KEY_ID, aws_secret_access_key=R2_SECRET,
                  config=Config(signature_version='s3v4', retries={'max_attempts': 3}),
                  region_name='auto')

def r2_exists(key):
    try:
        s3.head_object(Bucket=R2_BUCKET, Key=key)
        return True
    except Exception:
        return False

def r2_upload(local_path, key, content_type='video/mp4'):
    s3.upload_file(str(local_path), R2_BUCKET, key, ExtraArgs={'ContentType': content_type},
                   Config=boto3.s3.transfer.TransferConfig(multipart_threshold=30*1024*1024, multipart_chunksize=10*1024*1024))
    return f"{R2_PUBLIC}/{key}"

# ── DATABASE HELPERS ─────────────────────────────────────────────────────────
def get_or_create_drama(meta):
    title = meta['title']
    cover_r2_url = f"{R2_PUBLIC}/{meta['prefix']}/cover.webp"

    print(f"\n[DB] Memeriksa & Mendaftarkan Drama '{title}' ke KingShort...")
    try:
        r = requests.get(f"{API_BASE}/dramas?limit=1000&includeInactive=true", headers=ADMIN_HDR, timeout=15)
        if r.ok:
            for d in r.json().get('dramas', []):
                if d.get('title', '').strip().lower() == title.lower():
                    print(f"  -> Drama sudah ada di database (ID: {d['id']})")
                    requests.patch(f"{API_BASE}/dramas/{d['id']}", headers=ADMIN_HDR, json={'isActive': True, 'totalEpisodes': meta['total_eps']})
                    return d['id']
    except Exception as e:
        print(f"  [WARN] Gagal cek drama di DB: {e}")

    payload = {
        'title': title,
        'description': meta.get('desc') or title,
        'cover': cover_r2_url,
        'genres': meta.get('genres', ['CEO', 'Romansa', 'Drama']),
        'totalEpisodes': meta['total_eps'],
        'country': meta.get('country', 'China'),
        'language': 'Indonesia',
        'status': 'completed',
        'isActive': True
    }
    try:
        r = requests.post(f"{API_BASE}/admin/dramas", headers=ADMIN_HDR, json=payload, timeout=20)
        if r.ok:
            new_id = r.json().get('id')
            print(f"  -> Berhasil membuat drama di DB (ID: {new_id})")
            requests.patch(f"{API_BASE}/dramas/{new_id}", headers=ADMIN_HDR, json={'isActive': True, 'totalEpisodes': meta['total_eps']})
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
        if r.ok:
            return r.json().get('id')
    except Exception as e:
        print(f"      [WARN] DB upsert ep {ep_num} error: {e}")
    return None

# ── DOWNLOAD & TRANSCODE ─────────────────────────────────────────────────────
def download_file(url, out_path):
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36',
        'Referer': 'https://www.dracinema.com/'
    }
    for attempt in range(4):
        try:
            with requests.get(url, headers=headers, stream=True, timeout=40) as r:
                r.raise_for_status()
                with open(out_path, 'wb') as f:
                    for chunk in r.iter_content(chunk_size=128 * 1024):
                        if chunk:
                            f.write(chunk)
            if out_path.exists() and out_path.stat().st_size > 50 * 1024:
                return True
        except Exception:
            time.sleep(2)
    return False

def decrypt_melolo(raw_path, dec_path, hex_key):
    cmd = ['node', str(DECRYPT_TOOL), str(raw_path), str(dec_path), hex_key]
    res = subprocess.run(cmd, capture_output=True, text=True, timeout=120)
    return res.returncode == 0 and dec_path.exists() and dec_path.stat().st_size > 50 * 1024

def transcode_dual(in_file, out_720, out_540):
    cmd = [
        'ffmpeg', '-y', '-loglevel', 'error',
        '-i', str(in_file),
        '-c:v', 'libx264', '-crf', '24', '-preset', 'veryfast',
        '-c:a', 'copy',
        '-movflags', '+faststart',
        str(out_720),
        '-vf', 'scale=-2:540',
        '-c:v', 'libx264', '-crf', '28', '-preset', 'veryfast',
        '-c:a', 'copy',
        '-movflags', '+faststart',
        str(out_540)
    ]
    res = subprocess.run(cmd, timeout=300)
    return res.returncode == 0 and out_720.exists() and out_540.exists()

def ensure_cover(meta, temp_dir):
    cover_key = f"{meta['prefix']}/cover.webp"
    if r2_exists(cover_key):
        print(f"  -> [R2] Cover already exists.")
        return
    print(f"  -> [R2] Mengunduh dan mengupload cover...")
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
def process_episode(drama_id, meta, ep_data, temp_dir):
    ep_num = ep_data['ep']
    prefix = meta['prefix']
    k720 = f"{prefix}/ep{ep_num:03d}.mp4"
    k540 = f"{prefix}/ep{ep_num:03d}_540p.mp4"

    local_file = meta['local_dir'] / f"ep{ep_num:03d}.mp4"

    # 1. Cek apakah video sudah lengkap di R2
    if r2_exists(k720) and r2_exists(k540):
        u720 = f"{R2_PUBLIC}/{k720}"
        u540 = f"{R2_PUBLIC}/{k540}"
        upsert_episode(drama_id, ep_num, u720, u540)
        if not local_file.exists():
            try: s3.download_file(R2_BUCKET, k720, str(local_file))
            except Exception: pass
        print(f"  -> Ep {ep_num:02d}: [OK - R2 Cache]")
        return True

    video_url = ep_data.get('url')
    hex_key = ep_data.get('key')
    if not video_url:
        print(f"  -> Ep {ep_num:02d}: [GAGAL - Tidak ada URL]")
        return False

    raw_mp4 = temp_dir / f"raw_{ep_num:03d}.mp4"
    dec_mp4 = temp_dir / f"dec_{ep_num:03d}.mp4"
    out_720 = temp_dir / f"out720_{ep_num:03d}.mp4"
    out_540 = temp_dir / f"out540_{ep_num:03d}.mp4"

    # 2. Download raw
    if not download_file(video_url, raw_mp4):
        print(f"  -> Ep {ep_num:02d}: [GAGAL UNDUH RAW]")
        raw_mp4.unlink(missing_ok=True)
        return False

    # 3. Decrypt if encrypted, or use raw if unencrypted
    if hex_key:
        if not decrypt_melolo(raw_mp4, dec_mp4, hex_key):
            print(f"  -> Ep {ep_num:02d}: [GAGAL DEKRIPSI]")
            raw_mp4.unlink(missing_ok=True)
            dec_mp4.unlink(missing_ok=True)
            return False
        raw_mp4.unlink(missing_ok=True)
        target_in = dec_mp4
    else:
        target_in = raw_mp4

    # 4. Transcode Dual (720p universal + 540p faststart)
    if not transcode_dual(target_in, out_720, out_540):
        print(f"  -> Ep {ep_num:02d}: [GAGAL TRANSCODE]")
        target_in.unlink(missing_ok=True)
        out_720.unlink(missing_ok=True)
        out_540.unlink(missing_ok=True)
        return False

    target_in.unlink(missing_ok=True)

    # 5. Upload R2
    u720 = r2_upload(out_720, k720)
    u540 = r2_upload(out_540, k540)

    # 6. Simpan lokal (Single Location)
    try:
        shutil.copy2(out_720, local_file)
    except Exception as e:
        print(f"  -> Ep {ep_num:02d}: [WARN local copy: {e}]")

    out_720.unlink(missing_ok=True)
    out_540.unlink(missing_ok=True)

    # 7. Upsert DB
    upsert_episode(drama_id, ep_num, u720, u540)
    print(f"  -> Ep {ep_num:02d}: [SELESAI - R2 + Local + DB]")
    return True

# ── PROCESS DRAMA ────────────────────────────────────────────────────────────
def process_drama(meta):
    title = meta['title']
    total_eps = meta['total_eps']
    print("\n" + "=" * 60)
    print(f"MEMULAI SEDOT: {title} ({total_eps} Episode)")
    print("=" * 60)

    dump_file = Path(meta['dump_file'])
    if not dump_file.exists():
        print(f"[ERROR] Dump file tidak ditemukan: {dump_file}")
        return

    with open(dump_file, 'r', encoding='utf-8') as f:
        data = json.load(f)
        episodes = data.get('items', [])

    temp_dir = TEMP_ROOT / meta['slug']
    temp_dir.mkdir(parents=True, exist_ok=True)
    meta['local_dir'].mkdir(parents=True, exist_ok=True)

    ensure_cover(meta, temp_dir)

    drama_id = get_or_create_drama(meta)
    if not drama_id:
        print(f"[ERROR] Gagal mendapatkan ID drama DB untuk {title}.")
        return

    success = 0
    with concurrent.futures.ThreadPoolExecutor(max_workers=2) as executor:
        futures = {executor.submit(process_episode, drama_id, meta, ep_data, temp_dir): ep_data['ep'] for ep_data in episodes}
        for future in concurrent.futures.as_completed(futures):
            ep_no = futures[future]
            try:
                if future.result():
                    success += 1
            except Exception as e:
                print(f"  -> Ep {ep_no:02d} exception: {e}")

    # Retry jika ada episode terlewat
    missing = [e for e in range(1, total_eps + 1) if not (meta['local_dir'] / f"ep{e:03d}.mp4").exists()]
    if missing:
        print(f"\n[RETRY] Memproses episode yang belum lengkap: {missing}...")
        ep_dict = {x['ep']: x for x in episodes}
        for ep in missing:
            if ep in ep_dict and process_episode(drama_id, meta, ep_dict[ep], temp_dir):
                success += 1

    # Final patch to ensure totalEpisodes and isActive are set
    requests.patch(f"{API_BASE}/dramas/{drama_id}", headers=ADMIN_HDR, json={'isActive': True, 'totalEpisodes': total_eps})

    print("\n" + "=" * 60)
    print(f"[HASIL] Selesai {title}: {success}/{total_eps} episode.")
    print(f"  - Cloudflare R2: {R2_PUBLIC}/{meta['prefix']}/")
    print(f"  - Local Storage (Single Location): {meta['local_dir']}")
    print("=" * 60)

# ── MAIN PIPELINE ────────────────────────────────────────────────────
def main():
    meta = {
        "title": "Suami Baru Ternyata Sultan",
        "slug": "suami-baru-ternyata-sultan",
        "movie_key": "suami-baru-ternyata-sultan-ml_7681635084536908805",
        "total_eps": 107,
        "dump_file": "D:/temp_scraper/suami_sultan_dump.json",
        "cover_url": "https://img.mebilu.com/0Y4gyuAksQ15cVIR90ux6sfYM-oLyz3MLd6u-ks2zCRy7s84Qh3gVoJQQNlTk-eT7HiXSKECEpwDkQ.webp",
        "genres": ["CEO", "Cinta Setelah Pernikahan", "Romansa", "Pemeran Utama Wanita Kuat", "Drama"],
        "desc": "Setelah bercerai, Yuan Yi terjebak masalah aset dan dijauhi keluarganya. Di titik terendah hidupnya, ia menikah kilat dengan Yun Xiao, pria sederhana yang ternyata seorang konglomerat papan atas berjuluk Sultan. Bersama sang suami baru, Yuan Yi membalikkan keadaan dan membalas mereka yang dulu meremehkannya!",
        "country": "China",
        "prefix": "dracinema/suami-baru-ternyata-sultan",
        "local_dir": Path("D:/Video Drama/Facebook/Suami Baru Ternyata Sultan")
    }

    process_drama(meta)

if __name__ == "__main__":
    main()
