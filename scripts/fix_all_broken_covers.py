#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
KingShort - Bulk Auto-Fix Broken Covers (404)
=============================================
Perbaikan otomatis 243 cover drama yang 404:
1. Mengambil video episode pertama (ep001.mp4) dari Cloudflare R2
2. Mengekstrak frame karakter tokoh utama beresolusi HD
3. Mengunggah gambar cover baru ke R2 (image/jpeg)
4. Memperbarui link cover di database Shortlovers API
"""
import json
import subprocess
import requests
import boto3
from botocore.config import Config
from pathlib import Path
import time
import re
import concurrent.futures
import urllib3

urllib3.disable_warnings()

API_BASE    = 'https://api.shortlovers.id/api'
ADMIN_KEY   = '00ca04e3e2702be565d7bf44e783255247708289bce9b2fb6187a2e117f87fd14'
ADMIN_HDR   = {'x-admin-key': ADMIN_KEY, 'Content-Type': 'application/json'}

R2_ENDPOINT = 'https://a142d3b29a5d64943cb251157e25eaf3.r2.cloudflarestorage.com'
R2_KEY_ID   = '07c99c897986ea52703c1285308d5e2c'
R2_SECRET   = '44788d376ffb216e1e73784b6fe1ff1423607928898a87c50819b52cdfc12e44'
R2_BUCKET   = 'shortlovers'
R2_PUBLIC   = 'https://stream.shortlovers.id'

TEMP_DIR = Path('temp_covers_bulk')
TEMP_DIR.mkdir(exist_ok=True)

def get_s3():
    return boto3.client('s3', endpoint_url=R2_ENDPOINT,
                        aws_access_key_id=R2_KEY_ID, aws_secret_access_key=R2_SECRET,
                        config=Config(signature_version='s3v4'), region_name='auto')

def slugify(text):
    text = text.lower()
    return re.sub(r'[\W_]+', '-', text).strip('-')

def fix_single_drama(item, s3):
    did = item['id']
    title = item['title']
    slug = slugify(title)

    try:
        # 1. Ambil episode 1
        r_eps = requests.get(f"{API_BASE}/dramas/{did}/episodes", timeout=15)
        if not r_eps.ok:
            return (did, title, False, f"HTTP {r_eps.status_code} fetching episodes")

        data = r_eps.json()
        eps = data if isinstance(data, list) else data.get('episodes', [])
        if not eps:
            return (did, title, False, "No episodes")

        video_url = eps[0].get('videoUrl')
        if not video_url:
            return (did, title, False, "No videoUrl")

        out_jpg = TEMP_DIR / f"{slug}_{did[:6]}_cover.jpg"

        # 2. Ekstrak frame di detik ke-8 (karakter sudah muncul jelas)
        cmd = [
            'ffmpeg', '-y',
            '-ss', '00:00:08',
            '-i', video_url,
            '-vframes', '1',
            '-q:v', '2',
            str(out_jpg)
        ]
        res = subprocess.run(cmd, capture_output=True, text=True, timeout=40)
        if res.returncode != 0 or not out_jpg.exists() or out_jpg.stat().st_size < 1000:
            # Fallback ke detik 4
            cmd[2] = '00:00:04'
            res = subprocess.run(cmd, capture_output=True, text=True, timeout=40)

        if not out_jpg.exists() or out_jpg.stat().st_size < 1000:
            return (did, title, False, "FFmpeg failed to extract frame")

        # 3. Upload ke Cloudflare R2
        cover_key = f"dramas/covers/{slug}_cover_v2.jpg"
        s3.upload_file(str(out_jpg), R2_BUCKET, cover_key, ExtraArgs={'ContentType': 'image/jpeg'})
        new_cover_url = f"{R2_PUBLIC}/{cover_key}"

        # 4. Patch Database
        requests.patch(f"{API_BASE}/admin/dramas/{did}", headers=ADMIN_HDR, json={'cover': new_cover_url}, timeout=15)

        out_jpg.unlink(missing_ok=True)
        return (did, title, True, new_cover_url)

    except Exception as e:
        return (did, title, False, str(e)[:60])

def main():
    s3 = get_s3()
    with open('broken_covers.json', 'r', encoding='utf-8') as f:
        broken_list = json.load(f)

    total = len(broken_list)
    print(f"=== Memulai perbaikan otomatis {total} drama cover 404 ===")

    success_count = 0
    failed_count = 0

    # Menggunakan 6 worker threads untuk kecepatan optimal
    with concurrent.futures.ThreadPoolExecutor(max_workers=6) as executor:
        future_to_drama = {executor.submit(fix_single_drama, item, s3): item for item in broken_list}
        for i, future in enumerate(concurrent.futures.as_completed(future_to_drama), 1):
            did, title, success, msg = future.result()
            if success:
                success_count += 1
                print(f"[{i}/{total}] [SUKSES] {title}")
            else:
                failed_count += 1
                print(f"[{i}/{total}] [GAGAL] {title} ({msg})")

    print("\n=======================================================")
    print(f"Selesai! Berhasil: {success_count} | Gagal: {failed_count} | Total: {total}")
    print("=======================================================")

if __name__ == '__main__':
    main()
