# -*- coding: utf-8 -*-
"""
LOCAL DOWNLOADER: Sync "Membela Masakan Tradisional" from R2 to local D:\Video Drama\Facebook
"""
import os
import time
import requests

R2_PUBLIC = "https://stream.shortlovers.id"
DRAMA_SLUG = "membela-masakan-tradisional"
DRAMA_TITLE = "Membela Masakan Tradisional"
TOTAL_EPS = 54
LOCAL_FOLDER = r"D:\Video Drama\Facebook\Membela Masakan Tradisional"

def main():
    print("=" * 65)
    print(f"STARTING LOCAL SYNC FOR: '{DRAMA_TITLE}'")
    print(f"   Destination: {LOCAL_FOLDER}")
    print("=" * 65)
    
    os.makedirs(LOCAL_FOLDER, exist_ok=True)
    
    while True:
        try:
            completed = 0
            for ep in range(1, TOTAL_EPS + 1):
                filename = f"ep{ep:03d}_720p.mp4"
                local_path = os.path.join(LOCAL_FOLDER, filename)
                
                # Check if already downloaded
                if os.path.exists(local_path) and os.path.getsize(local_path) > 1024*1024:
                    completed += 1
                    continue
                    
                # Try to download from R2
                r2_url = f"{R2_PUBLIC}/dramas/{DRAMA_SLUG}/{filename}?v={int(time.time())}"
                try:
                    head_res = requests.head(r2_url, timeout=5)
                    if head_res.status_code == 200:
                        print(f"[{time.strftime('%H:%M:%S')}] Downloading EP {ep}/{TOTAL_EPS}...")
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
                        else:
                            print(f"   [WARN] GET request failed: {r.status_code}")
                except Exception as e:
                    print(f"   [ERROR] Network error checking/downloading EP {ep}: {e}")
                    
            print(f"[{time.strftime('%H:%M:%S')}] Status: {completed}/{TOTAL_EPS} episodes downloaded locally.")
            
            if completed == TOTAL_EPS:
                print("\nALL EPISODES SUCCESSFULLY DOWNLOADED LOCALLY!")
                break
                
            time.sleep(30)
        except KeyboardInterrupt:
            print("\nStopped by user.")
            break
        except Exception as e:
            print(f"Error in main loop: {e}")
            time.sleep(30)

if __name__ == "__main__":
    main()
