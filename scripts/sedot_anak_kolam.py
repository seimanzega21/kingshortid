#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Sedot Drama: Anak di Bawah Penutup Kolam (46 Episode)
Provider: Dracinema (GoodShort / cdn.mebilu.com AES-128 HLS)
Features:
- Video asli dengan hardsub Indo bawaan yang sudah bersih & tajam.
- Decrypt HLS AES-128 secara otomatis di memori.
- Transcode 540p faststart.
- Upload 720p & 540p ke Cloudflare R2 (stream.shortlovers.id/dracinema/anak-di-bawah-penutup-kolam/).
- Daftarkan ke database KingShort (api.shortlovers.id).
- Simpan file lokal strictly di 1 tempat: D:\\Video Drama\\Facebook\\Anak di Bawah Penutup Kolam\\
"""

import sys
if sys.platform == 'win32':
    sys.stdout.reconfigure(encoding='utf-8', errors='replace')
    sys.stderr.reconfigure(encoding='utf-8', errors='replace')

import os
import re
import json
import uuid
import time
import shutil
import base64
import subprocess
import requests
import urllib3
import boto3
from pathlib import Path
from concurrent.futures import ThreadPoolExecutor
from botocore.config import Config
from cryptography.hazmat.primitives.ciphers import Cipher, algorithms, modes
from cryptography.hazmat.backends import default_backend

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

TITLE       = 'Anak di Bawah Penutup Kolam'
SLUG        = 'anak-di-bawah-penutup-kolam'
MOVIE_KEY   = 'anak-di-bawah-penutup-kolam-gs_31001855044'
TOTAL_EPS   = 46
COVER_URL   = 'https://img.mebilu.com/HJPbu6BmJ_3FRx8faaGrQmtFbo8f3OqjwcOynIQ-JLqvfaF6zQhjTIRs9aNIy6Zk9sI.webp'
GENRES      = ['Penuh Intrik', 'Lingkungan Sosial', 'Penebusan', 'Orang Biasa', 'Salah Paham', 'Drama']
DESC        = 'Saat mendengar teriakan minta tolong dari bawah penutup kolam, Marcus segera berusaha menolong. Namun, ayah dan nenek anak tersebut justru menghalanginya karena salah paham. Dari situ, mereka baru menyadari kesalahan setelah Marcus berhasil menyelamatkan anak tersebut.'
PREFIX      = f"dracinema/{SLUG}"

LOCAL_DIR   = Path("D:/Video Drama/Facebook") / TITLE
LOCAL_DIR.mkdir(parents=True, exist_ok=True)

TEMP_DIR    = Path("D:/temp_scraper") / SLUG
TEMP_DIR.mkdir(parents=True, exist_ok=True)

DUMP_FILE   = Path("D:/temp_scraper/anak_kolam_dump.json")
BRIDGE_URL  = 'http://127.0.0.1:20199/request'

HEADERS = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36',
    'Origin': 'https://www.dracinema.com',
    'Referer': f'https://www.dracinema.com/play/{MOVIE_KEY}'
}

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

def ensure_cover():
    cover_key = f"{PREFIX}/cover.webp"
    if r2_exists(cover_key):
        print(f"  -> [R2] Cover already exists.")
        return
    print(f"  -> [R2] Mengunduh dan mengupload cover...")
    try:
        r = requests.get(COVER_URL, timeout=15)
        if r.ok:
            tmp_cov = TEMP_DIR / "cover.webp"
            tmp_cov.write_bytes(r.content)
            r2_upload(tmp_cov, cover_key, 'image/webp')
            tmp_cov.unlink(missing_ok=True)
            print("  -> [R2] Cover uploaded successfully!")
    except Exception as e:
        print(f"  -> [WARN] Cover error: {e}")

# ── DATABASE HELPERS ─────────────────────────────────────────────────────────
def get_or_create_drama():
    cover_r2_url = f"{R2_PUBLIC}/{PREFIX}/cover.webp"
    print(f"\n[DB] Memeriksa & Mendaftarkan Drama '{TITLE}' ke KingShort...")
    try:
        r = requests.get(f"{API_BASE}/dramas?limit=1000&includeInactive=true", headers=ADMIN_HDR, timeout=15)
        if r.ok:
            for d in r.json().get('dramas', []):
                if d.get('title', '').strip().lower() == TITLE.lower():
                    print(f"  -> Drama sudah ada di database (ID: {d['id']})")
                    return d['id']
    except Exception as e:
        print(f"  [WARN] Gagal cek drama di DB: {e}")

    payload = {
        'title': TITLE,
        'description': DESC,
        'cover': cover_r2_url,
        'genres': GENRES,
        'totalEpisodes': TOTAL_EPS,
        'country': 'Luar Negeri',
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
        if r.ok:
            return r.json().get('id')
    except Exception as e:
        print(f"      [WARN] DB upsert ep {ep_num} error: {e}")
    return None

# ── HLS AES-128 DECRYPTOR & DOWNLOADER ────────────────────────────────────────
def download_segment(item):
    idx, url, key, iv = item
    for attempt in range(3):
        try:
            r = requests.get(url, headers=HEADERS, timeout=15)
            if r.status_code == 200:
                data = r.content
                if key and iv:
                    cipher = Cipher(algorithms.AES(key), modes.CBC(iv), backend=default_backend())
                    dec = cipher.decryptor()
                    data = dec.update(data) + dec.finalize()
                return idx, data
        except Exception:
            time.sleep(1)
    return idx, b""

def download_hls_aes128(m3u8_url, out_mp4):
    try:
        r = requests.get(m3u8_url, headers=HEADERS, timeout=15)
        if r.status_code != 200:
            return False

        lines = r.text.splitlines()
        key_re = re.compile(r'URI=\"data:application/octet-stream;base64,([^\"]+)\"')
        iv_re = re.compile(r'IV=0x([0-9a-fA-F]+)')

        current_key = None
        current_iv = None
        segments = []

        for line in lines:
            line = line.strip()
            if line.startswith('#EXT-X-KEY'):
                km = key_re.search(line)
                if km: current_key = base64.b64decode(km.group(1))
                im = iv_re.search(line)
                if im: current_iv = bytes.fromhex(im.group(1).zfill(32))
            elif line.startswith('http'):
                segments.append((len(segments), line, current_key, current_iv))

        if not segments:
            return False

        with ThreadPoolExecutor(max_workers=8) as ex:
            results = list(ex.map(download_segment, segments))

        results.sort(key=lambda x: x[0])
        all_ts = b''.join([r[1] for r in results])

        if len(all_ts) < 100 * 1024:
            return False

        temp_ts = out_mp4.with_suffix('.ts')
        temp_ts.write_bytes(all_ts)

        cmd = [
            'ffmpeg', '-y', '-i', str(temp_ts),
            '-c', 'copy', '-movflags', '+faststart',
            '-loglevel', 'error', str(out_mp4)
        ]
        res = subprocess.run(cmd)
        temp_ts.unlink(missing_ok=True)

        return res.returncode == 0 and out_mp4.exists() and out_mp4.stat().st_size > 100 * 1024
    except Exception as e:
        print(f" [HLS Error: {e}]", end="")
        return False

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

# ── BRIDGE CLIENT FOR FRESH URLS ──────────────────────────────────────────────
def get_fresh_playback_from_bridge(ep_num):
    for attempt in range(3):
        try:
            payload = {
                'id': str(uuid.uuid4()),
                'movieKey': MOVIE_KEY,
                'episode': ep_num
            }
            r = requests.post(BRIDGE_URL, json=payload, timeout=25)
            if r.status_code == 200:
                res = r.json()
                if res.get('ok') and res.get('data', {}).get('kind') == 'ok':
                    return res['data']
        except Exception:
            time.sleep(2)
    return None

def load_dump_items():
    if DUMP_FILE.exists():
        try:
            with open(DUMP_FILE, 'r', encoding='utf-8') as f:
                data = json.load(f)
                return {item['ep']: item for item in data.get('items', []) if item.get('url')}
        except Exception:
            pass
    return {}

# ── PROCESS EPISODE ───────────────────────────────────────────────────────────
def process_episode(drama_id, ep_num, ep_meta):
    k720 = f"{PREFIX}/ep{ep_num:03d}.mp4"
    k540 = f"{PREFIX}/ep{ep_num:03d}_540p.mp4"
    local_file = LOCAL_DIR / f"ep{ep_num:03d}.mp4"

    # 1. Cek jika sudah ada di R2
    has_720 = r2_exists(k720)
    has_540 = r2_exists(k540)

    if has_720 and has_540:
        print(f"  -> Ep {ep_num:02d}: Sudah lengkap di R2. Link DB...", end="", flush=True)
        u720 = f"{R2_PUBLIC}/{k720}"
        u540 = f"{R2_PUBLIC}/{k540}"
        upsert_episode(drama_id, ep_num, u720, u540)
        if not local_file.exists():
            try: s3.download_file(R2_BUCKET, k720, str(local_file))
            except Exception: pass
        print(" [OK]")
        return True

    video_url = ep_meta.get('url')
    if not video_url:
        fresh = get_fresh_playback_from_bridge(ep_num)
        if fresh and fresh.get('url'):
            video_url = fresh['url']

    if not video_url:
        print(f"  -> Ep {ep_num:02d}: [GAGAL - Tidak ada URL video]")
        return False

    print(f"  -> Ep {ep_num:02d}: Mengunduh & Decrypt HLS AES-128...", end="", flush=True)

    raw_mp4 = TEMP_DIR / f"raw_{ep_num:03d}.mp4"
    out_540 = TEMP_DIR / f"out540_{ep_num:03d}.mp4"

    if not download_hls_aes128(video_url, raw_mp4):
        print(" [Expired/Gagal - Coba URL Fresh via Bridge...]", end="", flush=True)
        fresh = get_fresh_playback_from_bridge(ep_num)
        if fresh and fresh.get('url'):
            video_url = fresh['url']
            if not download_hls_aes128(video_url, raw_mp4):
                print(" [GAGAL RETRY DOWNLOAD]")
                if raw_mp4.exists(): raw_mp4.unlink()
                return False
        else:
            print(" [GAGAL DAPAT URL FRESH]")
            if raw_mp4.exists(): raw_mp4.unlink()
            return False

    size_mb = raw_mp4.stat().st_size / (1024 * 1024)
    print(f" ({size_mb:.1f} MB) 540p...", end="", flush=True)

    if not encode_540p(raw_mp4, out_540):
        print(" [GAGAL 540P]")
        if raw_mp4.exists(): raw_mp4.unlink()
        if out_540.exists(): out_540.unlink()
        return False

    print(" R2...", end="", flush=True)
    u720 = r2_upload(raw_mp4, k720)
    u540 = r2_upload(out_540, k540)

    # Simpan ke folder lokal (Single Location)
    try:
        shutil.copy2(raw_mp4, local_file)
    except Exception as e:
        print(f" [WARN local copy: {e}]", end="")

    # Upsert DB
    upsert_episode(drama_id, ep_num, u720, u540)

    raw_mp4.unlink(missing_ok=True)
    out_540.unlink(missing_ok=True)
    print(" [SELESAI]")
    return True

# ── MAIN PIPELINE ────────────────────────────────────────────────────────────
def main():
    print("=" * 60)
    print(f"MEMULAI SEDOT: {TITLE} ({TOTAL_EPS} Episode)")
    print("=" * 60)

    ensure_cover()

    drama_id = get_or_create_drama()
    if not drama_id:
        print(f"[ERROR] Gagal mendapatkan ID drama DB untuk {TITLE}.")
        return

    dump_items = load_dump_items()
    print(f"[INFO] Terbaca {len(dump_items)} episode dari metadata dump.")

    success = 0
    for ep in range(1, TOTAL_EPS + 1):
        ep_meta = dump_items.get(ep, {})
        if process_episode(drama_id, ep, ep_meta):
            success += 1
        time.sleep(0.3)

    # Check if any episode is missing, and retry it
    missing = [e for e in range(1, TOTAL_EPS + 1) if not (LOCAL_DIR / f"ep{e:03d}.mp4").exists()]
    if missing:
        print(f"\n[RETRY] Memproses episode yang belum lengkap: {missing}...")
        for ep in missing:
            ep_meta = dump_items.get(ep, {})
            if process_episode(drama_id, ep, ep_meta):
                success += 1

    print("\n" + "=" * 60)
    print(f"[HASIL] Selesai {TITLE}: {success}/{TOTAL_EPS} episode.")
    print(f"  - Cloudflare R2: {R2_PUBLIC}/{PREFIX}/")
    print(f"  - Local Storage (Single Location): {LOCAL_DIR}")
    print("=" * 60)

if __name__ == "__main__":
    main()
