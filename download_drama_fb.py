# -*- coding: utf-8 -*-
# Download drama dari R2 Cloudflare ke folder lokal.
# Target folder: D:/Video Drama/Upload Facebook

import sys
import os
import re
import boto3
import requests
from botocore.config import Config

# Fix encoding for Windows console
if sys.platform == 'win32':
    sys.stdout.reconfigure(encoding='utf-8', errors='replace')

# -- R2 Config ---------------------------------------------------------------
R2_ENDPOINT = 'https://a142d3b29a5d64943cb251157e25eaf3.r2.cloudflarestorage.com'
R2_KEY_ID   = '07c99c897986ea52703c1285308d5e2c'
R2_SECRET   = '44788d376ffb216e1e73784b6fe1ff1423607928898a87c50819b52cdfc12e44'
BUCKET      = 'shortlovers'
API_BASE    = 'https://api.shortlovers.id'

# -- Target folder -----------------------------------------------------------
DEST_ROOT = 'D:/Video Drama/Upload Facebook'

# -- Drama yang ingin di-download --------------------------------------------
TARGET_DRAMAS = [
    "Jangan Tangisi Kepergianku",
    "Tombak Sakti Gadis Desa",
    "Makhluk Abadi",
    "Pedang sakti Sang Menantu Desa",
    "Edukasi Seks Oleh Sahabatku",
    "Istri Magang Bosku",
    "Titisan Dewa Obat",
    "Warisan Mata Sakti",
]

# -- Init boto3 R2 client ----------------------------------------------------
r2 = boto3.client(
    's3',
    endpoint_url=R2_ENDPOINT,
    aws_access_key_id=R2_KEY_ID,
    aws_secret_access_key=R2_SECRET,
    config=Config(signature_version='s3v4'),
    region_name='auto'
)

def normalize(title: str) -> str:
    return re.sub(r'\s+', ' ', title.strip().lower())

def fetch_all_dramas() -> list:
    print("[*] Fetching drama list dari API...")
    try:
        r = requests.get(f"{API_BASE}/api/dramas?limit=1000", timeout=30)
        r.raise_for_status()
        data = r.json()
        dramas = data if isinstance(data, list) else data.get('dramas', data.get('data', []))
        print(f"    -> {len(dramas)} drama ditemukan di API")
        return dramas
    except Exception as e:
        print(f"    ERROR fetch API: {e}")
        return []

def find_drama(all_dramas: list, title: str) -> dict | None:
    norm_target = normalize(title)
    # Exact match dulu
    for d in all_dramas:
        if normalize(d.get('title', '')) == norm_target:
            return d
    # Partial match
    for d in all_dramas:
        if norm_target in normalize(d.get('title', '')):
            return d
    # Keyword match (kata kunci utama)
    keywords = [w for w in norm_target.split() if len(w) > 4]
    for d in all_dramas:
        drama_norm = normalize(d.get('title', ''))
        if all(kw in drama_norm for kw in keywords[:2]):
            return d
    return None

def list_r2_files(prefix: str) -> list:
    files = []
    paginator = r2.get_paginator('list_objects_v2')
    for page in paginator.paginate(Bucket=BUCKET, Prefix=prefix):
        for obj in page.get('Contents', []):
            files.append(obj)
    return files

def pick_highest_res(files: list) -> dict | None:
    """Pilih video resolusi tertinggi."""
    video_ext = ('.mp4', '.m3u8', '.ts', '.mkv', '.avi', '.mov', '.webm')
    video_files = [f for f in files if f['Key'].lower().endswith(video_ext)]
    if not video_files:
        return None

    res_priority = [1080, 720, 540, 480, 360, 240]
    for res in res_priority:
        for f in video_files:
            if str(res) in f['Key']:
                return f
    # Fallback: file terbesar
    return max(video_files, key=lambda x: x.get('Size', 0))

def pick_cover(files: list) -> dict | None:
    """Cari file cover/thumbnail."""
    img_ext = ('.jpg', '.jpeg', '.png', '.webp')
    img_files = [f for f in files if f['Key'].lower().endswith(img_ext)]
    if not img_files:
        return None
    priority = ['cover', 'thumb', 'poster', 'banner']
    for kw in priority:
        for f in img_files:
            if kw in f['Key'].lower():
                return f
    # Ambil yang terbesar (biasanya cover lebih besar dari thumbnail kecil)
    return max(img_files, key=lambda x: x.get('Size', 0))

def safe_folder_name(title: str) -> str:
    return re.sub(r'[<>:"/\\|?*]', '', title).strip()

def download_file(r2_key: str, dest_path: str):
    os.makedirs(os.path.dirname(dest_path), exist_ok=True)
    
    head = r2.head_object(Bucket=BUCKET, Key=r2_key)
    total_size = head.get('ContentLength', 0)
    size_mb = total_size / (1024 * 1024)
    
    print(f"    [DL] {os.path.basename(dest_path)} ({size_mb:.1f} MB)")
    
    downloaded = [0]
    def progress(chunk):
        downloaded[0] += chunk
        pct = (downloaded[0] / total_size * 100) if total_size else 0
        print(f"\r         {pct:.1f}% ({downloaded[0]/(1024*1024):.1f}/{size_mb:.1f} MB)", end='', flush=True)
    
    r2.download_file(
        Bucket=BUCKET,
        Key=r2_key,
        Filename=dest_path,
        Callback=progress
    )
    print()

def main():
    print("=" * 60)
    print("[DRAMA DOWNLOADER] R2 -> Upload Facebook")
    print("=" * 60)
    
    os.makedirs(DEST_ROOT, exist_ok=True)
    
    all_dramas = fetch_all_dramas()
    if not all_dramas:
        print("[ERROR] Tidak bisa mendapatkan daftar drama.")
        return
    
    results = []
    
    for title in TARGET_DRAMAS:
        print(f"\n{'─'*60}")
        print(f"[CARI] {title}")
        
        drama = find_drama(all_dramas, title)
        if not drama:
            print(f"    [X] Drama tidak ditemukan di API: {title}")
            print(f"    [INFO] Semua judul di API:")
            for d in all_dramas[:30]:
                print(f"          - {d.get('title','')}")
            results.append({'title': title, 'status': 'NOT FOUND'})
            continue
        
        drama_id = drama.get('id', drama.get('drama_id', ''))
        drama_title = drama.get('title', title)
        print(f"    [OK] Ditemukan: {drama_title} (ID: {drama_id})")
        
        # Coba berbagai prefix R2
        all_files = []
        prefixes_to_try = [
            f"dramas/{drama_id}/",
            f"{drama_id}/",
            f"videos/{drama_id}/",
            f"drama/{drama_id}/",
        ]
        
        for prefix in prefixes_to_try:
            files = list_r2_files(prefix)
            if files:
                print(f"    [R2] Prefix: '{prefix}' -> {len(files)} file")
                all_files = files
                break
        
        if not all_files:
            print(f"    [X] Tidak ada file R2 (prefix dicoba: {prefixes_to_try})")
            results.append({'title': drama_title, 'status': 'NO FILES IN R2'})
            continue
        
        # Tampilkan daftar file
        print(f"    [FILES] Daftar file di R2:")
        for f in all_files[:15]:
            size_mb = f.get('Size', 0) / (1024 * 1024)
            print(f"      - {f['Key']} ({size_mb:.1f} MB)")
        if len(all_files) > 15:
            print(f"      ... dan {len(all_files) - 15} file lainnya")
        
        # Buat folder tujuan
        folder_name = safe_folder_name(drama_title)
        dest_folder = os.path.join(DEST_ROOT, folder_name)
        os.makedirs(dest_folder, exist_ok=True)
        
        downloaded_files = []
        
        # Download cover
        cover_file = pick_cover(all_files)
        if cover_file:
            ext = os.path.splitext(cover_file['Key'])[1] or '.jpg'
            cover_dest = os.path.join(dest_folder, f"cover{ext}")
            try:
                download_file(cover_file['Key'], cover_dest)
                downloaded_files.append(cover_dest)
                print(f"    [DONE] Cover: {cover_dest}")
            except Exception as e:
                print(f"    [FAIL] Cover error: {e}")
        else:
            print(f"    [WARN] Tidak ada cover ditemukan")
        
        # Download video resolusi tertinggi
        video_file = pick_highest_res(all_files)
        if video_file:
            ext = os.path.splitext(video_file['Key'])[1] or '.mp4'
            video_name = f"{folder_name}{ext}"
            video_dest = os.path.join(dest_folder, video_name)
            try:
                download_file(video_file['Key'], video_dest)
                downloaded_files.append(video_dest)
                print(f"    [DONE] Video: {video_dest}")
            except Exception as e:
                print(f"    [FAIL] Video error: {e}")
        else:
            print(f"    [WARN] Tidak ada file video ditemukan")
        
        results.append({
            'title': drama_title,
            'status': 'OK' if downloaded_files else 'FAILED',
            'files': downloaded_files
        })
    
    # Summary
    print(f"\n{'='*60}")
    print("RINGKASAN DOWNLOAD:")
    print(f"{'='*60}")
    for r in results:
        icon = "[OK]" if r['status'] == 'OK' else ("[SKIP]" if 'NO FILES' in r['status'] else "[FAIL]")
        print(f"  {icon} {r['title']} -> {r['status']}")
    print(f"\nSemua file di: {DEST_ROOT}")

if __name__ == "__main__":
    main()
