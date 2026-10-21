#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Sedot Drama: Tenggelam di Era 80, Ikan Ajaib Buatnya Kaya (80 Episode)
Provider: Dracinema (Melolo encrypted)
Decryptor: scripts/melolo_decrypt_tool.js
Target: Cloudflare R2 + KingShort DB + Single Local Storage (D:\Video Drama\Facebook\<TITLE>\)
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

BRIDGE_URL  = 'http://127.0.0.1:20199/request'

TITLE       = 'Tenggelam di Era 80, Ikan Ajaib Buatnya Kaya'
SLUG        = 'tenggelam-di-era-80-ikan-ajaib-buatnya-kaya'
MOVIE_KEY   = 'tenggelam-di-era-80-ikan-ajaib-buatnya-kaya-ml_7694912039776603189'
TOTAL_EPS   = 80
COVER_URL   = 'https://img.mebilu.com/P_lM9gAis9r-3gmPlpDm-0yidEetb4yWF_EXgrb4NiTCJzhphC86ZmklwO1enCCnlSUEc79YfN0Dig.webp'
GENRES      = ['Serangan balik', 'Pemeran Utama Pria', 'Imajinasi Perkotaan', 'Kekuatan Super', 'Drama']
DESC        = 'Tahun 1985, ia dibuang ke laut oleh keluarganya. Ikan ajaib yang ia selamatkan memberinya mutiara penyembuh dan kekuatan sakti. Ia pulang, menyelamatkan anak istrinya, dan memutus hubungan dengan keluarga kejamnya. Berkat keahlian melaut dan mutiara ajaib, ia menghidupi keluarga tercintanya dan bangkit menjadi raja nelayan kaya raya!'
PREFIX      = f"dracinema/{SLUG}"

LOCAL_DIR   = Path("D:/Video Drama/Facebook") / TITLE
LOCAL_DIR.mkdir(parents=True, exist_ok=True)

TEMP_DIR    = Path("D:/temp_scraper") / SLUG
TEMP_DIR.mkdir(parents=True, exist_ok=True)

DECRYPT_TOOL = Path(__file__).parent / "melolo_decrypt_tool.js"

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
        if r.ok:
            return r.json().get('id')
    except Exception as e:
        print(f"      [WARN] DB upsert ep {ep_num} error: {e}")
    return None

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

# ── BRIDGE CLIENT ────────────────────────────────────────────────────────────
def get_playback_via_bridge(ep_num):
    for attempt in range(4):
        req_id = str(uuid.uuid4())
        payload = {
            'id': req_id,
            'movieKey': MOVIE_KEY,
            'episode': ep_num
        }
        try:
            r = requests.post(BRIDGE_URL, json=payload, timeout=35)
            if r.status_code == 200:
                res = r.json()
                if res.get('ok') and res.get('data', {}).get('kind') == 'ok':
                    return res['data']
        except Exception:
            time.sleep(2)
    return None

# ── PROCESS EPISODE ───────────────────────────────────────────────────────────
def process_episode(drama_id, ep_num):
    k720 = f"{PREFIX}/ep{ep_num:03d}.mp4"
    k540 = f"{PREFIX}/ep{ep_num:03d}_540p.mp4"
    local_file = LOCAL_DIR / f"ep{ep_num:03d}.mp4"

    # 1. Cek apakah video sudah ada di R2
    if r2_exists(k720) and r2_exists(k540):
        print(f"  -> Ep {ep_num:02d}: Sudah ada di R2. Link DB...", end="", flush=True)
        u720 = f"{R2_PUBLIC}/{k720}"
        u540 = f"{R2_PUBLIC}/{k540}"
        upsert_episode(drama_id, ep_num, u720, u540)
        if not local_file.exists():
            try:
                s3.download_file(R2_BUCKET, k720, str(local_file))
            except Exception:
                pass
        print(" [OK Video]")
        return True

    # 2. Ambil URL video fresh melalui Bridge Browser
    print(f"  -> Ep {ep_num:02d}: Mengambil stream dari Dracinema...", end="", flush=True)
    pb = get_playback_via_bridge(ep_num)
    if not pb or not pb.get('url'):
        print(" [GAGAL DAPAT URL STREAM]")
        return False

    video_url = pb['url']
    hex_key = pb.get('key')
    if not hex_key:
        print(" [GAGAL DAPAT ENCRYPTION KEY]")
        return False

    raw_mp4 = TEMP_DIR / f"raw_{ep_num:03d}.mp4"
    dec_mp4 = TEMP_DIR / f"dec_{ep_num:03d}.mp4"
    out_540 = TEMP_DIR / f"out540_{ep_num:03d}.mp4"

    # 3. Download encrypted MP4
    try:
        r_vid = requests.get(video_url, headers={'User-Agent': 'Mozilla/5.0'}, stream=True, timeout=90)
        if not r_vid.ok:
            print(f" [GAGAL DOWNLOAD: {r_vid.status_code}]")
            return False
        with open(raw_mp4, 'wb') as f:
            for chunk in r_vid.iter_content(chunk_size=1024*1024):
                if chunk: f.write(chunk)
    except Exception as e:
        print(f" [DOWNLOAD EXCEPTION: {e}]")
        if raw_mp4.exists(): raw_mp4.unlink()
        return False

    size_mb = raw_mp4.stat().st_size / (1024 * 1024)
    print(f" ({size_mb:.1f} MB) Decrypting...", end="", flush=True)

    # 4. Decrypt using node tool
    dec_cmd = ["node", str(DECRYPT_TOOL), str(raw_mp4), str(dec_mp4), hex_key]
    dec_res = subprocess.run(dec_cmd, capture_output=True, text=True)
    if dec_res.returncode != 0 or not dec_mp4.exists() or dec_mp4.stat().st_size < 100 * 1024:
        print(f" [GAGAL DECRYPT: {dec_res.stderr}]")
        if raw_mp4.exists(): raw_mp4.unlink()
        if dec_mp4.exists(): dec_mp4.unlink()
        return False

    # 5. Compress 540p
    print(" 540p...", end="", flush=True)
    if not encode_540p(dec_mp4, out_540):
        print(" [GAGAL 540P]")
        if raw_mp4.exists(): raw_mp4.unlink()
        if dec_mp4.exists(): dec_mp4.unlink()
        if out_540.exists(): out_540.unlink()
        return False

    # 6. Upload R2
    print(" R2...", end="", flush=True)
    u720 = r2_upload(dec_mp4, k720)
    u540 = r2_upload(out_540, k540)

    # 7. Simpan ke folder lokal (Single Location)
    try:
        shutil.copy2(dec_mp4, local_file)
    except Exception as e:
        print(f" [WARN local copy: {e}]", end="")

    # 8. Upsert ke database
    upsert_episode(drama_id, ep_num, u720, u540)

    # Clean temp
    raw_mp4.unlink(missing_ok=True)
    dec_mp4.unlink(missing_ok=True)
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

    success = 0
    for ep in range(1, TOTAL_EPS + 1):
        if process_episode(drama_id, ep):
            success += 1
        time.sleep(1.0) # Jeda aman anti-rate-limit

    print("\n" + "=" * 60)
    print(f"[HASIL] Selesai {TITLE}: {success}/{TOTAL_EPS} episode.")
    print(f"  - Cloudflare R2: {R2_PUBLIC}/{PREFIX}/")
    print(f"  - Local Storage (Single Location): {LOCAL_DIR}")
    print("=" * 60)

if __name__ == "__main__":
    main()
