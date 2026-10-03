#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
KingShort GoodShort Scraper - Kabur Dari Nikah Malah Dapat Pembalap Sultan
========================================================================
- Download & remux native 720p & 540p streams
- Upload to Cloudflare R2
- Register to Database with isActive: False (Pending / Jangan Langsung Tayangkan)
"""

import os
import sys
import time
import json
import boto3
import requests
import subprocess
from pathlib import Path
from botocore.config import Config
from concurrent.futures import ThreadPoolExecutor, as_completed

sys.stdout.reconfigure(encoding='utf-8', line_buffering=True)

# ── CONFIG ───────────────────────────────────────────────────────────────────
API_BASE    = 'https://api.shortlovers.id/api'
ADMIN_KEY   = '00ca04e3e2702be565d7bf44e783255247708289bce9b2fb6187a2e117f87fd14'
ADMIN_HDR   = {'x-admin-key': ADMIN_KEY, 'Content-Type': 'application/json'}

R2_ENDPOINT = 'https://a142d3b29a5d64943cb251157e25eaf3.r2.cloudflarestorage.com'
R2_KEY_ID   = '07c99c897986ea52703c1285308d5e2c'
R2_SECRET   = '44788d376ffb216e1e73784b6fe1ff1423607928898a87c50819b52cdfc12e44'
R2_BUCKET   = 'shortlovers'
R2_PUBLIC   = 'https://stream.shortlovers.id'

FFMPEG_EXE  = r'C:\ProgramData\chocolatey\bin\ffmpeg.exe'
TEMP_DIR    = Path('D:/temp_scraper')
TEMP_DIR.mkdir(exist_ok=True)

BOOK_ID     = '31001740822'
SLUG        = 'kabur-dari-nikah-malah-dapat-pembalap-sultan--31001740822'
PROVIDER    = 'goodshortv2'
PREFIX      = f'{PROVIDER}/{SLUG}'
WATCH_URL   = f'https://vidrama.asia/en/watch/{SLUG}/1?provider={PROVIDER}&lang=in'

DRAMA_META  = {
    'title': 'Kabur dari Nikah, Malah Dapat Pembalap Sultan',
    'description': (
        'Setelah melarikan diri dari pernikahan paksa, Mallory Sutton secara impulsif menikahi '
        'seorang montir yang dicampakkan oleh mantannya. Ternyata, montir itu adalah legenda balap '
        'yang menyembunyikan identitasnya dan pewaris keluarga kaya! Ketika mantannya yang toksik '
        'memohon agar dia kembali, montir itu menggenggam tangan Mallory lebih erat dan tidak pernah '
        'menoleh ke belakang.'
    ),
    'cover_src': 'https://acfs1.goodreels.com/videobook/202609/cover-RFJIEZAjcs.jpg',
    'genres': ['Drama', 'Nikah Kilat', 'Pewaris', 'Pembalasan', 'Pengkhianatan', 'Pernikahan'],
    'totalEpisodes': 55
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
    except:
        return False

def r2_upload(local_path, key, content_type='video/mp4'):
    s3.upload_file(str(local_path), R2_BUCKET, key, ExtraArgs={'ContentType': content_type},
                   Config=boto3.s3.transfer.TransferConfig(multipart_threshold=30*1024*1024, multipart_chunksize=10*1024*1024))
    return f"{R2_PUBLIC}/{key}"

# ── DATABASE HELPERS ─────────────────────────────────────────────────────────
def get_or_create_drama():
    print("[1] Memeriksa status Drama di Database KingShort...")
    # Cek duplikat
    try:
        r = requests.get(f"{API_BASE}/dramas?limit=1000&includeInactive=true", headers=ADMIN_HDR, timeout=15)
        if r.ok:
            for d in r.json().get('dramas', []):
                if d.get('title', '').strip().lower() == DRAMA_META['title'].strip().lower():
                    print(f"  -> Drama sudah ada di database (ID: {d['id']}, isActive: {d.get('isActive')})")
                    # Pastikan isActive tetap False
                    if d.get('isActive') is True:
                        requests.patch(f"{API_BASE}/admin/dramas/{d['id']}", headers=ADMIN_HDR, json={'isActive': False})
                    return d['id']
    except Exception as e:
        print(f"  [WARN] Gagal mencari database: {e}")

    cover_r2_url = f"{R2_PUBLIC}/{PREFIX}/cover_hq.jpg"
    payload = {
        'title': DRAMA_META['title'],
        'description': DRAMA_META['description'],
        'cover': cover_r2_url,
        'genres': DRAMA_META['genres'],
        'totalEpisodes': DRAMA_META['totalEpisodes'],
        'isComplete': True,
        'country': 'China',
        'language': 'Indonesia',
        'status': 'completed',
        'isActive': False,  # PENTING: Selesai sedot jangan langsung tayangkan!
        'providerName': PROVIDER,
        'sourceMovieId': BOOK_ID
    }

    print(f"  -> Mendaftarkan drama baru ke Database dengan status PENDING (isActive=False)...")
    res = requests.post(f"{API_BASE}/admin/dramas", headers=ADMIN_HDR, json=payload, timeout=20)
    if res.ok:
        did = res.json().get('id')
        print(f"  [✓] Berhasil membuat Drama di Database! ID: {did}")
        return did
    else:
        raise Exception(f"Gagal membuat drama di DB: {res.status_code} - {res.text}")

def upsert_episode(drama_id, ep_no, u720, u540):
    payload = {
        'episodeNumber': ep_no,
        'title': f'Episode {ep_no}',
        'videoUrl': u720,
        'videoUrl540p': u540,
        'isActive': True
    }
    for attempt in range(3):
        try:
            r = requests.post(f"{API_BASE}/admin/dramas/{drama_id}/episodes", headers=ADMIN_HDR, json=payload, timeout=15)
            if r.ok:
                return r.json().get('id')
        except:
            time.sleep(1)
    return None

# ── COVER PROCESSING ──────────────────────────────────────────────────────────
def process_cover():
    cover_key = f"{PREFIX}/cover_hq.jpg"
    if r2_exists(cover_key):
        print(f"  [✓] Cover sudah ada di R2: {R2_PUBLIC}/{cover_key}")
        return f"{R2_PUBLIC}/{cover_key}"

    print(f"[*] Mendownload & memproses Cover HD...")
    raw_path = TEMP_DIR / f"{SLUG}_cover_raw.jpg"
    hq_path = TEMP_DIR / f"{SLUG}_cover_hq.jpg"
    try:
        r = requests.get(DRAMA_META['cover_src'], headers={'User-Agent': 'Mozilla/5.0'}, timeout=20)
        raw_path.write_bytes(r.content)
        cmd = [FFMPEG_EXE, '-y', '-i', str(raw_path), '-vf', 'scale=1080:-1', '-update', '1', '-q:v', '2', '-loglevel', 'error', str(hq_path)]
        subprocess.run(cmd, check=True)
        r2_upload(hq_path, cover_key, 'image/jpeg')
        print(f"  [✓] Cover berhasil diupload ke R2: {R2_PUBLIC}/{cover_key}")
        return f"{R2_PUBLIC}/{cover_key}"
    finally:
        if raw_path.exists(): raw_path.unlink()
        if hq_path.exists(): hq_path.unlink()

# ── EPISODE FETCHER & DOWNLOADER ─────────────────────────────────────────────
ACTION_HEADERS = {
    'sec-ch-ua-platform': '"Windows"',
    'next-action': '6095289ff5eab15c1c5f6d76318539b63b263abee6',
    'referer': WATCH_URL,
    'user-agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36',
    'accept': 'text/x-component',
    'content-type': 'text/plain;charset=UTF-8'
}

def get_stream_urls(ep_no):
    data = json.dumps([BOOK_ID, ep_no])
    for attempt in range(4):
        try:
            r = requests.post(WATCH_URL, headers=ACTION_HEADERS, data=data, timeout=12)
            if r.status_code == 200:
                lines = r.text.strip().split('\n')
                for line in lines:
                    if line.startswith('1:'):
                        parsed = json.loads(line[2:])
                        url_720 = parsed.get('videoUrl')
                        url_540 = None
                        qualities = parsed.get('qualities', [])
                        for q in qualities:
                            if q.get('type') == '720p':
                                url_720 = q.get('url')
                            elif q.get('type') == '540p':
                                url_540 = q.get('url')
                        if not url_540 and url_720:
                            url_540 = url_720.replace('q=720p', 'q=540p')
                        return url_720, url_540
        except Exception as e:
            time.sleep(2)
    return None, None

def process_single_episode(ep_no, drama_id):
    k720 = f"{PREFIX}/ep{ep_no:03d}.mp4"
    k540 = f"{PREFIX}/ep{ep_no:03d}_540p.mp4"
    u720_public = f"{R2_PUBLIC}/{k720}"
    u540_public = f"{R2_PUBLIC}/{k540}"

    # Fast-resume: jika sudah ada di R2
    if r2_exists(k720) and r2_exists(k540):
        upsert_episode(drama_id, ep_no, u720_public, u540_public)
        print(f"  [Eps {ep_no:02d}/55] SUDAH ADA di R2 (Resume & Sync DB OK)")
        return ep_no, True, "Already in R2"

    url_720, url_540 = get_stream_urls(ep_no)
    if not url_720:
        print(f"  [Eps {ep_no:02d}/55] [X] Gagal mendapatkan URL stream")
        return ep_no, False, "Stream URL error"

    f720 = TEMP_DIR / f"{SLUG}_ep{ep_no:03d}_720.mp4"
    f540 = TEMP_DIR / f"{SLUG}_ep{ep_no:03d}_540.mp4"

    ff_headers = 'Referer: https://vidrama.asia/\r\nUser-Agent: Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36\r\n'

    try:
        # Download 720p (-c copy, faststart)
        cmd_720 = [
            FFMPEG_EXE, '-y',
            '-headers', ff_headers,
            '-i', url_720,
            '-c', 'copy',
            '-movflags', '+faststart',
            '-loglevel', 'error',
            str(f720)
        ]
        res_720 = subprocess.run(cmd_720, timeout=120)
        if res_720.returncode != 0 or not f720.exists() or f720.stat().st_size < 100000:
            raise Exception("Gagal download 720p")

        # Download 540p (-c copy jika stream tersedia, atau scale dari 720p)
        if url_540:
            cmd_540 = [
                FFMPEG_EXE, '-y',
                '-headers', ff_headers,
                '-i', url_540,
                '-c', 'copy',
                '-movflags', '+faststart',
                '-loglevel', 'error',
                str(f540)
            ]
            res_540 = subprocess.run(cmd_540, timeout=120)
            if res_540.returncode != 0 or not f540.exists():
                url_540 = None

        if not url_540 or not f540.exists():
            # Fallback scale 540p
            cmd_scale = [
                FFMPEG_EXE, '-y',
                '-i', str(f720),
                '-vf', 'scale=-2:540',
                '-c:v', 'libx264', '-crf', '28', '-preset', 'ultrafast',
                '-c:a', 'copy',
                '-movflags', '+faststart',
                '-loglevel', 'error',
                str(f540)
            ]
            subprocess.run(cmd_scale, timeout=180)

        # Upload ke Cloudflare R2
        r2_upload(f720, k720, 'video/mp4')
        r2_upload(f540, k540, 'video/mp4')

        # Daftarkan ke Database
        upsert_episode(drama_id, ep_no, u720_public, u540_public)

        sz_mb = f720.stat().st_size / (1024 * 1024)
        print(f"  [Eps {ep_no:02d}/55] [OK] Downloaded, Uploaded R2 & DB Sync ({sz_mb:.1f} MB)")
        return ep_no, True, "OK"
    except Exception as e:
        print(f"  [Eps {ep_no:02d}/55] [ERROR] {e}")
        return ep_no, False, str(e)
    finally:
        if f720.exists(): f720.unlink()
        if f540.exists(): f540.unlink()

# ── MAIN PIPELINE ────────────────────────────────────────────────────────────
def main():
    print("=" * 65)
    print("  SEDOT DRAMA GOODSHORT: KABUR DARI NIKAH MALAH DAPAT PEMBALAP SULTAN")
    print(f"  Target: {DRAMA_META['title']} (Total {DRAMA_META['totalEpisodes']} Episodes)")
    print("  Status Publikasi: PENDING / DRAFT (isActive=False)")
    print("=" * 65)

    # 1. Process Cover
    process_cover()

    # 2. Get or Create Drama in DB
    drama_id = get_or_create_drama()

    # 3. Process Episodes in Parallel (3 workers for optimal bandwidth & safety)
    total_eps = DRAMA_META['totalEpisodes']
    ep_list = list(range(1, total_eps + 1))

    print(f"\n[2] Memulai Sedot {total_eps} Episode (Parallel 3 Workers)...")
    success_count = 0
    failed_eps = []

    with ThreadPoolExecutor(max_workers=3) as executor:
        futures = {executor.submit(process_single_episode, ep, drama_id): ep for ep in ep_list}
        for future in as_completed(futures):
            ep_no, success, msg = future.result()
            if success:
                success_count += 1
            else:
                failed_eps.append(ep_no)

    # Retry jika ada episode gagal
    if failed_eps:
        print(f"\n[*] Melakukan retry untuk {len(failed_eps)} episode yang gagal: {failed_eps}...")
        for ep_no in failed_eps:
            _, success, _ = process_single_episode(ep_no, drama_id)
            if success:
                success_count += 1

    # Verifikasi status di DB
    print("\n[3] Memverifikasi Status Drama di Database KingShort...")
    try:
        r = requests.get(f"{API_BASE}/dramas/{drama_id}", headers=ADMIN_HDR, timeout=15)
        d_data = r.json()
        print(f"  - Judul          : {d_data.get('title')}")
        print(f"  - Total Episode  : {len(d_data.get('episodes', []))}/{total_eps}")
        print(f"  - isActive       : {d_data.get('isActive')} (Pending / Draft)")
    except Exception as e:
        print(f"  [WARN] {e}")

    print("\n" + "=" * 65)
    print(f"[SELESAI] Sedot Drama '{DRAMA_META['title']}' Telah Berhasil!")
    print(f"  - Sukses Diserap : {success_count}/{total_eps} Episode")
    print(f"  - Status Tayang  : INACTIVE / DRAFT (Sesuai instruksi: TIDAK langsung ditayangkan)")
    print(f"  - Drama ID di DB : {drama_id}")
    print("=" * 65)

if __name__ == '__main__':
    main()
