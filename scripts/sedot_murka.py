import requests
import boto3
import subprocess
import os
import time
from botocore.config import Config

# --- CONFIGURATION ---
API_BASE    = 'https://api.shortlovers.id/api'
ADMIN_KEY   = '00ca04e3e2702be565d7bf44e783255247708289bce9b2fb6187a2e117f87fd14'

R2_ENDPOINT = 'https://a142d3b29a5d64943cb251157e25eaf3.r2.cloudflarestorage.com'
R2_KEY_ID   = '07c99c897986ea52703c1285308d5e2c'
R2_SECRET   = '44788d376ffb216e1e73784b6fe1ff1423607928898a87c50819b52cdfc12e44'
R2_BUCKET   = 'shortlovers'
R2_PUBLIC   = 'https://stream.shortlovers.id'

HEADERS = {
    'X-Admin-Key': ADMIN_KEY,
    'Content-Type': 'application/json'
}

def get_r2():
    return boto3.client('s3', endpoint_url=R2_ENDPOINT,
                        aws_access_key_id=R2_KEY_ID, aws_secret_access_key=R2_SECRET,
                        config=Config(signature_version='s3v4'), region_name='auto')

def find_drama_id(title_query):
    print(f"Mencari ID untuk drama '{title_query}'...")
    try:
        r = requests.get(f"{API_BASE}/dramas/search?q={title_query}")
        dramas = r.json().get('dramas', [])
        if dramas:
            print(f"Ditemukan drama: {dramas[0]['title']} (ID: {dramas[0]['id']})")
            return dramas[0]['id']
    except Exception as e:
        print("Error mencari drama:", e)
    return None

def get_episodes(drama_id):
    print(f"Mengambil daftar episode untuk drama ID: {drama_id}...")
    url = f"{API_BASE}/dramas/{drama_id}/episodes"
    try:
        response = requests.get(url, timeout=15)
        if response.status_code == 200:
            return response.json()
    except Exception as e:
        print(f"Error fetching episodes: {e}")
    return []

def update_episode_db(episode_id, new_url):
    url = f"{API_BASE}/admin/system/episodes/{episode_id}"
    try:
        response = requests.put(url, headers=HEADERS, json={'videoUrl': new_url}, timeout=15)
        if response.status_code == 200:
            return True
        print(f"Gagal update DB episode {episode_id}: {response.status_code} - {response.text}")
    except Exception as e:
        print(f"Error updating DB: {e}")
    return False

def download_video(url, output_path):
    print(f"Mendownload menggunakan FFmpeg...")
    cmd = [
        'ffmpeg', '-y', 
        '-i', url, 
        '-c', 'copy', 
        '-bsf:a', 'aac_adtstoasc', 
        output_path
    ]
    try:
        result = subprocess.run(cmd, stdout=subprocess.DEVNULL, stderr=subprocess.STDOUT)
        return result.returncode == 0
    except Exception as e:
        print(f"FFmpeg error: {e}")
        return False

def main():
    r2 = get_r2()
    
    # Otomatis cari ID yang benar berdasarkan judul
    drama_id = find_drama_id("Saat Aku Murka")
    if not drama_id:
        print("Gagal menemukan ID drama di database. Pastikan judulnya benar.")
        return
        
    episodes = get_episodes(drama_id)
    if not episodes:
        print("Tidak ada episode ditemukan untuk drama ini.")
        return
        
    print(f"Ditemukan {len(episodes)} episode. Memulai proses sedot & pindah...")
    
    episodes = sorted(episodes, key=lambda x: x.get('episodeNumber', 0))
    
    temp_dir = os.path.join(os.getcwd(), 'temp_sedot')
    os.makedirs(temp_dir, exist_ok=True)
    
    success_count = 0
    skip_count = 0
    
    for ep in episodes:
        ep_id = ep.get('id')
        ep_num = ep.get('episodeNumber')
        video_url = ep.get('videoUrl')
        
        print(f"\n--- Episode {ep_num} ---")
        
        if not video_url:
            print("Tidak ada videoUrl, skip.")
            continue
            
        if 'stream.shortlovers.id' in video_url or 'r2.cloudflarestorage.com' in video_url:
            print("Video sudah menggunakan URL R2, skip.")
            skip_count += 1
            continue
            
        print(f"Video asli: {video_url[:60]}...")
        
        temp_file = os.path.join(temp_dir, f"ep_{ep_num:03d}.mp4")
        r2_key = f"dramas/{drama_id}/ep_{ep_num:03d}.mp4"
        r2_public_url = f"{R2_PUBLIC}/{r2_key}"
        
        if download_video(video_url, temp_file):
            if os.path.exists(temp_file):
                print(f"Download selesai. Uploading ke R2...")
                try:
                    r2.upload_file(temp_file, R2_BUCKET, r2_key, ExtraArgs={'ContentType': 'video/mp4'})
                    print(f"Upload berhasil!")
                    
                    if update_episode_db(ep_id, r2_public_url):
                        print(f"Database berhasil diupdate untuk Episode {ep_num} -> Menggunakan R2")
                        success_count += 1
                    
                except Exception as e:
                    print(f"Gagal upload ke R2: {e}")
                
                try:
                    os.remove(temp_file)
                except:
                    pass
        else:
            print("Gagal mendownload video.")
            
    print(f"\n{'='*50}")
    print(f"PROSES SELESAI!")
    print(f"Total berhasil disedot & dipindah ke R2: {success_count}")
    print(f"Total di-skip (sudah pakai R2): {skip_count}")

if __name__ == "__main__":
    main()
