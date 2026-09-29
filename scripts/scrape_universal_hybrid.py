#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
KingShort Universal Hybrid Scraper
===================================
Script baru yang sangat cepat!
Hanya mendownload cover, lalu mengirim ID dan nama provider ke database.
VIDEO TIDAK DIDOWNLOAD. Backend yang akan mengambil video secara live saat diputar.
"""
import requests
import boto3
import time
import subprocess
import urllib3
import re
import os
import sys
from pathlib import Path
from botocore.config import Config

urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)
sys.stdout.reconfigure(encoding='utf-8')

# --- CONFIG ---
API_BASE    = 'https://api.shortlovers.id/api'
ADMIN_KEY   = '00ca04e3e2702be565d7bf44e783255247708289bce9b2fb6187a2e117f87fd14'
ADMIN_HDR   = {'x-admin-key': ADMIN_KEY, 'Content-Type': 'application/json'}

R2_ENDPOINT = 'https://a142d3b29a5d64943cb251157e25eaf3.r2.cloudflarestorage.com'
R2_KEY_ID   = '07c99c897986ea52703c1285308d5e2c'
R2_SECRET   = '44788d376ffb216e1e73784b6fe1ff1423607928898a87c50819b52cdfc12e44'
R2_BUCKET   = 'shortlovers'
R2_PUBLIC   = 'https://stream.shortlovers.id'

WEB_HDRS    = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36',
    'Referer': 'https://vidrama.asia/',
}

TEMP_DIR = Path('D:/temp_scraper')
TEMP_DIR.mkdir(exist_ok=True)

def get_r2():
    return boto3.client('s3', endpoint_url=R2_ENDPOINT,
                        aws_access_key_id=R2_KEY_ID, aws_secret_access_key=R2_SECRET,
                        config=Config(signature_version='s3v4'), region_name='auto')

def slugify(text):
    text = text.lower()
    text = re.sub(r'[^a-z0-9\s-]', '', text)
    return re.sub(r'[\s-]+', '-', text).strip('-')

def fetch_metadata(provider, movie_id):
    urls_to_try = [
        f"https://vidrama.asia/api/{provider}/detail?id={movie_id}&lang=id",
        f"https://vidrama.asia/api/{provider}/detail?bookId={movie_id}&lang=id",
        f"https://vidrama.asia/api/{provider}/multi-video?id={movie_id}&lang=id",
        f"https://vidrama.asia/api/{provider}/video?bookId={movie_id}&lang=id",
        f"https://vidrama.asia/api/{provider}?action=stream&id={movie_id}"
    ]
    
    for url in urls_to_try:
        try:
            res = requests.get(url, headers=WEB_HDRS, timeout=10)
            if res.status_code == 200:
                data = res.json()
                # Jika formatnya ada 'series' (seperti di multi-video)
                if 'series' in data:
                    series = data['series']
                    series['chapterCount'] = len(data.get('episodes', []))
                    return series
                # Format umum
                if 'title' in data or 'name' in data:
                    return data
        except Exception:
            pass
            
    return None

def process_cover(cover_url, slug):
    print("Mendownload dan memproses cover ke JPEG murni...")
    raw_path = TEMP_DIR / f"{slug}_raw_cover"
    r = requests.get(cover_url, headers=WEB_HDRS)
    raw_path.write_bytes(r.content)
    
    out_path = TEMP_DIR / f"{slug}_cover_hq.jpg"
    
    # Sesuai SOP: Konversi ke JPEG Murni
    cmd = ['ffmpeg', '-y', '-i', str(raw_path), '-update', '1', str(out_path)]
    subprocess.run(cmd, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    
    if not out_path.exists():
        print("Gagal convert cover! Pakai raw aja.")
        out_path = raw_path
        
    s3 = get_r2()
    r2_key = f"covers/{slug}_{int(time.time())}.jpg"
    print(f"Mengupload cover ke R2: {r2_key}")
    s3.upload_file(str(out_path), R2_BUCKET, r2_key, ExtraArgs={'ContentType': 'image/jpeg'})
    return f"{R2_PUBLIC}/{r2_key}"

def register_drama_and_episodes(detail, provider, movie_id, cover_url):
    title = detail.get('title') or detail.get('name') or 'Unknown Drama'
    slug = slugify(title)
    
    cover_r2_url = process_cover(cover_url, slug)
    
    total_eps = detail.get('chapterCount') or detail.get('total_episodes') or 1
    
    payload = {
        'title': title,
        'description': detail.get('description') or title,
        'cover': cover_r2_url,
        'genres': detail.get('tags', ['Drama']) if isinstance(detail.get('tags'), list) else ['Drama'],
        'providerName': provider,
        'sourceMovieId': str(movie_id)
    }
    
    print(f"Mendaftarkan Drama: {title}")
    res = requests.post(f"{API_BASE}/dramas", json=payload, headers=ADMIN_HDR)
    if res.status_code not in [200, 201]:
        print("Gagal membuat drama:", res.text)
        return
        
    drama_db = res.json()
    drama_id = drama_db.get('id')
    
    print(f"Mendaftarkan {total_eps} episode secara INSTAN (tanpa download mp4)...")
    
    for i in range(1, int(total_eps) + 1):
        ep_payload = {
            'dramaId': drama_id,
            'episodeNumber': i,
            'title': f'Episode {i}',
            # videoUrl kita kosongkan! Backend yang akan fetch on-the-fly
        }
        res_ep = requests.post(f"{API_BASE}/episodes", json=ep_payload, headers=ADMIN_HDR)
        if res_ep.status_code not in [200, 201]:
            print(f"Gagal tambah ep {i}: {res_ep.text}")
            
    print(f"\n--- SUKSES BESAR! ---")
    print(f"Drama '{title}' dan {total_eps} episode selesai diproses dalam beberapa detik!")
    print(f"Video tidak memakai storage R2 sama sekali.")

if __name__ == "__main__":
    print("=== HYBRID STREAMING SCRAPER ===")
    print("Cara Pakai: Abang bisa memasukkan URL lengkap dari web Vidrama, atau sekadar ketik ID-nya.")
    print("Contoh URL: https://vidrama.asia/provider/melolov3/play/7664444328231586869")
    
    user_input = input("Masukkan URL Vidrama atau Movie ID: ").strip()
    
    provider_in = None
    movie_id_in = None
    
    # Coba deteksi jika input berupa URL
    if "vidrama.asia" in user_input.lower():
        # Ekstrak provider
        prov_match = re.search(r'/provider/([^/?]+)', user_input)
        if prov_match:
            provider_in = prov_match.group(1)
        else:
            prov_match_query = re.search(r'[?&]provider=([^&]+)', user_input)
            if prov_match_query:
                provider_in = prov_match_query.group(1)
        
        # Ekstrak ID (biasanya angka panjang)
        id_match = re.search(r'/(\d{5,})', user_input)
        if id_match:
            movie_id_in = id_match.group(1)
        else:
            id_match_dash = re.search(r'--(\d{5,})', user_input)
            if id_match_dash:
                movie_id_in = id_match_dash.group(1)
            else:
                id_match_query = re.search(r'[?&]id=(\d+)', user_input)
                if id_match_query:
                    movie_id_in = id_match_query.group(1)
                
    else:
        # Jika bukan URL, anggap itu ID manual
        movie_id_in = user_input
        
    # Jika gagal deteksi provider, tanya manual
    if not provider_in:
        provider_in = input("Gagal mendeteksi provider dari URL. Masukkan nama provider (contoh: melolov3): ").strip()
        
    if not movie_id_in:
        print("Gagal mendeteksi ID. Pastikan URL atau ID benar.")
        sys.exit(1)
        
    print(f"\n[INFO] Provider Terdeteksi : {provider_in}")
    print(f"[INFO] Movie ID Terdeteksi : {movie_id_in}\n")
    
    detail_data = fetch_metadata(provider_in, movie_id_in)
    
    if not detail_data:
        print("Gagal mengambil metadata otomatis dari Vidrama. Masukkan manual:")
        title = input("Judul Drama: ")
        cover = input("Cover URL asli: ")
        eps = input("Total Episode: ")
        detail_data = {'title': title, 'coverUrl': cover, 'chapterCount': eps}
    else:
        cover = detail_data.get('coverUrl') or detail_data.get('cover_url') or detail_data.get('verticalCover') or detail_data.get('cover')
        
        # Jika benar-benar tidak ada cover, gunakan placeholder
        if not cover:
            cover = "https://via.placeholder.com/300x400.jpg?text=No+Cover"
    
    register_drama_and_episodes(detail_data, provider_in, movie_id_in, cover)
