# D:\kingshortid\hybrid_streaming_v2\scrape_melolov3_provider_v2.py
# Ini adalah CONTOH Modifikasi Script Sedot (Super Cepat)
# Tidak ada lagi proses download MP4 atau upload ke R2 untuk episode.

import json
import requests
import time

API_BASE = 'https://api.shortlovers.id/api'
PROVIDER_NAME = 'melolov3'

def fetch_metadata(movie_id):
    """Mengambil metadata film dari Vidrama"""
    url = f"https://vidrama.asia/api/melolov3/detail?id={movie_id}&lang=id"
    headers = {'Referer': 'https://vidrama.asia/'}
    res = requests.get(url, headers=headers)
    return res.json()

def api_get_or_create_drama_v2(detail, movie_id, cover_r2_url):
    """Menyimpan Drama ke DB dengan kolom hybrid baru"""
    title = detail.get('title') or detail.get('name') or 'Unknown'
    
    payload = {
        'title': title,
        'description': detail.get('description') or title,
        'cover': cover_r2_url,
        'genres': detail.get('tags', ['Drama']) or ['Drama'],
        'totalEpisodes': detail.get('chapterCount', 0),
        'isActive': True,
        
        # --- PERUBAHAN BARU: SIMPAN ID SUMBER ---
        'providerName': PROVIDER_NAME,
        'sourceMovieId': str(movie_id)
    }
    
    # POST ke API Backend KingShort
    res = requests.post(f"{API_BASE}/dramas", json=payload)
    if res.status_code in [200, 201]:
        return res.json().get('id') # Mengembalikan internal ID dari DB KingShort
    return None

def api_upsert_episode_v2(drama_db_id, ep_no, source_episode_id):
    """Menyimpan Episode ke DB (Tanpa download video!)"""
    payload = {
        'episodeNumber': ep_no,
        'title': f'Episode {ep_no}',
        'isActive': True,
        
        # --- PERUBAHAN BARU: VIDEO URL KOSONG ---
        'videoUrl': None,  
        'videoUrl540p': None,
        'sourceEpisodeId': str(source_episode_id) if source_episode_id else None
    }
    
    res = requests.post(f"{API_BASE}/dramas/{drama_db_id}/episodes", json=payload)
    return res.status_code in [200, 201]

def ingest_movie(movie_id):
    print(f"Mulai menyedot Movie ID: {movie_id} (Tanpa Download MP4)")
    
    # 1. Ambil Metadata
    detail = fetch_metadata(movie_id)
    if not detail:
        return
        
    # 2. Download & Konversi Cover ke R2 (Tetap Wajib sesuai SOP)
    print("Mendownload Cover ke R2...")
    cover_r2_url = "https://stream.shortlovers.id/covers/contoh_cover_hq.jpg" # Dummy
    
    # 3. Buat/Update Drama di Database
    drama_db_id = api_get_or_create_drama_v2(detail, movie_id, cover_r2_url)
    if not drama_db_id:
        print("Gagal membuat Drama di DB")
        return
        
    # 4. Looping Episode dan Simpan ke DB dengan Instan!
    total_episodes = detail.get('chapterCount', 0)
    print(f"Menyimpan {total_episodes} episode ke Database (Kecepatan Tinggi)...")
    
    for i in range(1, total_episodes + 1):
        # Kita tidak lagi mendownload video atau menembak multi-video API di sini.
        # Kita biarkan Backend yang melakukannya nanti saat penonton mengeklik "Play".
        api_upsert_episode_v2(drama_db_id, i, None)
        
    print(f"SUKSES! {total_episodes} episode selesai disedot dalam hitungan detik.")

if __name__ == "__main__":
    # Contoh sedot
    ingest_movie("7664444328231586869")
