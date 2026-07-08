# -*- coding: utf-8 -*-
"""
LOCAL QUEUE DOWNLOADER: Download all 5 shortmax dramas from R2 to D:\Video Drama\Facebook
Runs in a loop to match VPS upload progress. Self-healing and supports resume.
"""
import os
import time
import requests

R2_PUBLIC = "https://stream.shortlovers.id"
BASE_DIR = r"D:\Video Drama\Facebook"

DRAMAS = [
    {
        "slug": "tuan-gelap",
        "title": "Tuan Gelap",
        "total_eps": 64,
        "folder": os.path.join(BASE_DIR, "Tuan Gelap")
    },
    {
        "slug": "dubbing-anak-miliarder-yang-memilih-susah",
        "title": "[Dubbing] Anak Miliarder yang Memilih Susah",
        "total_eps": 69,
        "folder": os.path.join(BASE_DIR, "[Dubbing] Anak Miliarder yang Memilih Susah")
    },
    {
        "slug": "dijulukitakdir-cinta-bersemi",
        "title": "[Dijuluki]Takdir Cinta Bersemi",
        "total_eps": 63,
        "folder": os.path.join(BASE_DIR, "[Dijuluki]Takdir Cinta Bersemi")
    },
    {
        "slug": "dijulukiayah-penentu-takdir",
        "title": "[Dijuluki]Ayah Penentu Takdir",
        "total_eps": 61,
        "folder": os.path.join(BASE_DIR, "[Dijuluki]Ayah Penentu Takdir")
    },
    {
        "slug": "dijulukipengantin-curian-sang-raja-mafia",
        "title": "[Dijuluki]Pengantin Curian Sang Raja Mafia",
        "total_eps": 38,
        "folder": os.path.join(BASE_DIR, "[Dijuluki]Pengantin Curian Sang Raja Mafia")
    }
]

def check_and_download_drama(d):
    os.makedirs(d["folder"], exist_ok=True)
    completed = 0
    downloaded_this_run = 0
    
    for ep in range(1, d["total_eps"] + 1):
        filename = f"ep{ep:03d}_720p.mp4"
        local_path = os.path.join(d["folder"], filename)
        
        # Check if already downloaded
        if os.path.exists(local_path) and os.path.getsize(local_path) > 1024*1024:
            completed += 1
            continue
            
        # Try to download
        r2_url = f"{R2_PUBLIC}/dramas/{d['slug']}/{filename}"
        
        try:
            head_res = requests.head(r2_url, timeout=5)
            if head_res.status_code == 200:
                print(f"[{time.strftime('%H:%M:%S')}] Downloading '{d['title']}' EP {ep}/{d['total_eps']}...")
                r = requests.get(r2_url, timeout=60, stream=True)
                if r.ok:
                    temp_path = local_path + ".tmp"
                    with open(temp_path, "wb") as f:
                        for chunk in r.iter_content(chunk_size=1024*1024):
                            if chunk:
                                f.write(chunk)
                    if os.path.exists(temp_path):
                        os.replace(temp_path, local_path)
                    print(f"   [OK] Saved {filename} ({os.path.getsize(local_path)/(1024*1024):.1f} MB)")
                    completed += 1
                    downloaded_this_run += 1
                else:
                    print(f"   [WARN] GET request failed: {r.status_code}")
        except Exception as e:
            print(f"   [ERROR] Network error checking/downloading EP {ep}: {e}")
            
    return completed

def main():
    print("=" * 65)
    print("STARTING LOCAL QUEUE DOWNLOADER FOR 5 SHORTMAX DRAMAS")
    print(f"   Destination: {BASE_DIR}")
    print("=" * 65)
    
    while True:
        try:
            all_done = True
            for d in DRAMAS:
                completed = check_and_download_drama(d)
                print(f"[{time.strftime('%H:%M:%S')}] '{d['title']}': {completed}/{d['total_eps']} episodes downloaded.")
                if completed < d["total_eps"]:
                    all_done = False
                    
            if all_done:
                print("\nALL 5 DRAMAS SUCCESSFULLY SYNCHRONIZED LOCALLY!")
                break
                
            # Sleep 30 seconds before next check
            time.sleep(30)
        except KeyboardInterrupt:
            print("\nStopped by user.")
            break
        except Exception as e:
            print(f"Error in main loop: {e}")
            time.sleep(30)

if __name__ == "__main__":
    main()
