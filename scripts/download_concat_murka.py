import requests
import os
import subprocess

# --- CONFIGURATION ---
API_BASE    = 'https://api.shortlovers.id/api'
BASE_OUTPUT_DIR = r'D:\Video Drama'
OUTPUT_DIR = os.path.join(BASE_OUTPUT_DIR, 'Saat_Aku_Murka')

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
    url = f"{API_BASE}/dramas/{drama_id}/episodes"
    try:
        response = requests.get(url, timeout=15)
        if response.status_code == 200:
            return response.json()
    except Exception as e:
        print(f"Error fetching episodes: {e}")
    return []

def get_subtitles(episode_id):
    url = f"{API_BASE}/episodes/{episode_id}/subtitles"
    try:
        response = requests.get(url, timeout=10)
        if response.status_code == 200:
            subs = response.json().get('subtitles', [])
            if subs:
                # Ambil subtitle bahasa indonesia atau subtitle pertama
                indo_sub = next((s for s in subs if 'id' in s.get('language', '').lower() or 'indo' in s.get('label', '').lower()), None)
                if indo_sub:
                    return indo_sub['url']
                return subs[0]['url']
    except Exception as e:
        print(f"Error fetching subtitles for {episode_id}: {e}")
    return None

def download_and_concat():
    drama_id = find_drama_id("Saat Aku Murka")
    if not drama_id:
        print("Gagal menemukan ID drama di database.")
        return
        
    print(f"Mengambil daftar episode dan subtitle dari database...")
    episodes = get_episodes(drama_id)
    
    if not episodes:
        print(f"Episode tidak ditemukan di database.")
        return

    print(f"Ditemukan {len(episodes)} episode.")
    
    episodes = sorted(episodes, key=lambda x: x.get('episodeNumber', 0))
    
    if not os.path.exists(OUTPUT_DIR):
        os.makedirs(OUTPUT_DIR)
        
    print(f"\nMulai mendownload dan BURNING SUBTITLE (Hardsub) ke {OUTPUT_DIR}...")
    local_files = []
    
    for ep in episodes:
        ep_id = ep.get('id')
        ep_num = ep.get('episodeNumber')
        video_url = ep.get('videoUrl')
        
        if not video_url:
            continue
            
        local_filename = os.path.join(OUTPUT_DIR, f"ep_{ep_num:03d}.mp4")
        sub_filename = f"ep_{ep_num:03d}.vtt" # local name for CWD
        
        if not os.path.exists(local_filename):
            sub_url = get_subtitles(ep_id)
            if sub_url:
                print(f"Downloading Episode {ep_num} (Membakar Subtitle / Hardsub) -> ep_{ep_num:03d}.mp4")
                print(f"  -> Harap sabar, proses hardsub memakan waktu lebih lama...")
                
                # Download subtitle file locally first
                sub_path = os.path.join(OUTPUT_DIR, sub_filename)
                try:
                    r = requests.get(sub_url, timeout=10)
                    with open(sub_path, 'wb') as f:
                        f.write(r.content)
                except Exception as e:
                    print(f"  -> Gagal download subtitle: {e}")
                    continue

                # Burn subtitle via FFmpeg. We run in OUTPUT_DIR to avoid absolute path escaping hell.
                cmd = [
                    'ffmpeg', '-y', 
                    '-i', video_url, 
                    '-vf', f"subtitles={sub_filename}", 
                    '-c:v', 'libx264', 
                    '-crf', '26', 
                    '-preset', 'veryfast', 
                    '-c:a', 'copy', 
                    f"ep_{ep_num:03d}.mp4"
                ]
                subprocess.run(cmd, cwd=OUTPUT_DIR, stdout=subprocess.DEVNULL, stderr=subprocess.STDOUT)
                
                # Cleanup subtitle file
                if os.path.exists(sub_path):
                    os.remove(sub_path)
            else:
                print(f"Downloading Episode {ep_num} (Tanpa Subtitle) -> ep_{ep_num:03d}.mp4")
                cmd = ['ffmpeg', '-y', '-i', video_url, '-c', 'copy', f"ep_{ep_num:03d}.mp4"]
                subprocess.run(cmd, cwd=OUTPUT_DIR, stdout=subprocess.DEVNULL, stderr=subprocess.STDOUT)
        else:
            print(f"File ep_{ep_num:03d}.mp4 sudah ada, skip download.")
            
        if os.path.exists(local_filename):
            local_files.append((ep_num, local_filename))
        
    print("\nSemua episode berhasil didownload dan subtitle telah dibakar permanen.")
    print("Mulai menggabungkan video per 3 episode...")
    
    batch_size = 3
    for i in range(0, len(local_files), batch_size):
        batch = local_files[i:i+batch_size]
        if not batch: continue
        
        start_ep = batch[0][0]
        end_ep = batch[-1][0]
        
        output_filename = os.path.join(OUTPUT_DIR, f"Eps {start_ep}-{end_ep}.mp4")
        if os.path.exists(output_filename):
            print(f"File {output_filename} sudah ada, skip penggabungan.")
            continue
            
        print(f"Menggabungkan Eps {start_ep}-{end_ep}...")
        
        list_filename = os.path.join(OUTPUT_DIR, f"list_{start_ep}_{end_ep}.txt")
        with open(list_filename, 'w', encoding='utf-8') as f:
            for _, filepath in batch:
                safe_path = filepath.replace('\\', '/')
                f.write(f"file '{safe_path}'\n")
                
        try:
            cmd = [
                'ffmpeg', '-y', 
                '-f', 'concat', 
                '-safe', '0', 
                '-i', list_filename, 
                '-c', 'copy', 
                output_filename
            ]
            subprocess.run(cmd, check=True, stdout=subprocess.DEVNULL, stderr=subprocess.STDOUT)
            print(f"  -> Berhasil membuat {output_filename}")
        except subprocess.CalledProcessError as e:
            print(f"  -> Gagal menggabungkan Eps {start_ep}-{end_ep}: {e}")
            
        if os.path.exists(list_filename):
            os.remove(list_filename)

    print("\nSelesai! Semua video telah digabung per 3 episode dengan Hardsub.")
    print(f"Silakan cek folder: {OUTPUT_DIR}")

if __name__ == "__main__":
    download_and_concat()
