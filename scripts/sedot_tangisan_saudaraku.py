#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Sedot Tangisan Tiga Saudaraku (51 Episode) - ReelShort (Hardsub Indo)
- Unencrypted HLS M3U8 streams from Crazy Maple Studios CDN (ReelShort)
- Download & remux to 720p faststart, and transcode 540p faststart
- Hardsub Indonesia official built-in
- Upload 720p & 540p to Cloudflare R2
- Upsert & activate drama + episodes in KingShort DB
- Single storage location strictly in D:\\Video Drama\\Facebook\\Tangisan Tiga Saudaraku\\
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
        'genres': meta.get('genres', ['Dewasa Muda', 'Drama']),
        'totalEpisodes': meta['total_eps'],
        'country': meta.get('country', 'Luar Negeri'),
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
def download_and_remux_m3u8(url, out_path):
    cmd = [
        'ffmpeg', '-y',
        '-headers', 'Referer: https://www.dracinema.com/\r\nUser-Agent: Mozilla/5.0\r\n',
        '-i', url,
        '-c', 'copy',
        '-movflags', '+faststart',
        '-loglevel', 'error',
        str(out_path)
    ]
    for attempt in range(4):
        res = subprocess.run(cmd, timeout=300)
        if res.returncode == 0 and out_path.exists() and out_path.stat().st_size > 50 * 1024:
            return True
        time.sleep(2)
    return False

def transcode_540p(in_file, out_file):
    cmd = [
        'ffmpeg', '-y', '-loglevel', 'error',
        '-i', str(in_file),
        '-vf', 'scale=-2:540',
        '-c:v', 'libx264', '-crf', '28', '-preset', 'veryfast',
        '-c:a', 'aac', '-b:a', '96k',
        '-movflags', '+faststart',
        str(out_file)
    ]
    res = subprocess.run(cmd, timeout=300)
    return res.returncode == 0 and out_file.exists() and out_file.stat().st_size > 50 * 1024

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
    if not video_url:
        print(f"  -> Ep {ep_num:02d}: [GAGAL - Tidak ada URL video]")
        return False

    out_720 = temp_dir / f"out720_{ep_num:03d}.mp4"
    out_540 = temp_dir / f"out540_{ep_num:03d}.mp4"

    # 2. Download and remux HLS M3U8
    if not download_and_remux_m3u8(video_url, out_720):
        print(f"  -> Ep {ep_num:02d}: [GAGAL UNDUH M3U8]")
        out_720.unlink(missing_ok=True)
        return False

    # 3. Transcode 540p faststart
    if not transcode_540p(out_720, out_540):
        print(f"  -> Ep {ep_num:02d}: [GAGAL TRANSCODE 540P]")
        out_720.unlink(missing_ok=True)
        out_540.unlink(missing_ok=True)
        return False

    # 4. Upload R2
    u720 = r2_upload(out_720, k720)
    u540 = r2_upload(out_540, k540)

    # 5. Simpan lokal (Single Location)
    try:
        shutil.copy2(out_720, local_file)
    except Exception as e:
        print(f"  -> Ep {ep_num:02d}: [WARN local copy: {e}]")

    out_720.unlink(missing_ok=True)
    out_540.unlink(missing_ok=True)

    # 6. Upsert DB
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

# ── MAIN PIPELINE ────────────────────────────────────────────────────────────
def main():
    meta = {
        "title": "Tangisan Tiga Saudaraku",
        "slug": "tangisan-tiga-saudaraku",
        "movie_key": "tangisan-tiga-saudaraku-rs_6acc9a54b88045ea5a060895",
        "total_eps": 51,
        "dump_file": "D:/temp_scraper/tangisan_dump.json",
        "cover_url": "https://img.mebilu.com/ib-mMGLFe_bNfhNYU0Pt-iQ29j8H2ahQcdtZSX2MXt8r5XU1O226wtrvjpKUREtWUU2H-I85RTv9Z55QwH-e.webp",
        "genres": ["Dewasa Muda", "Fantasi", "Romantis", "Drama"],
        "desc": "Elisa, gadis setengah manusia dan setengah vampir, percaya bahwa si kembar tiga Lockhart adalah satu-satunya orang yang tulus padanya. Ia rela menjadi manusia demi menghabiskan sisa hidup bersama salah satu dari mereka. Namun, segalanya berubah saat Amber, putri pelayan mereka, muncul. Berkali-kali Elisa diabaikan dan dipermalukan hingga rahasia dan kebenaran mulai terungkap!",
        "country": "Luar Negeri",
        "prefix": "dracinema/tangisan-tiga-saudaraku",
        "local_dir": Path("D:/Video Drama/Facebook/Tangisan Tiga Saudaraku")
    }

    process_drama(meta)

if __name__ == "__main__":
    main()
