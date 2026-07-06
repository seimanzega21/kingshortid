# -*- coding: utf-8 -*-
"""
LOCAL DOWNLOADER: Download (Dub) Cinta dan Tombak Purba from R2 to D:\Video Drama\Facebook
Runs in a loop to match VPS upload progress. Self-healing and supports resume.
"""
import os
import time
import requests

DRAMA_SLUG = "cinta-dan-tombak-purba"
LOCAL_DIR = r"D:\Video Drama\Facebook\(Dub) Cinta dan Tombak Purba"
os.makedirs(LOCAL_DIR, exist_ok=True)

TOTAL_EPS = 50
R2_PUBLIC = "https://stream.shortlovers.id"

def check_and_download():
    completed = 0
    downloaded_this_run = 0
    
    for ep in range(1, TOTAL_EPS + 1):
        filename = f"ep{ep:03d}_720p.mp4"
        local_path = os.path.join(LOCAL_DIR, filename)
        
        # Check if already downloaded
        if os.path.exists(local_path) and os.path.getsize(local_path) > 1024*1024:
            completed += 1
            continue
            
        # Try to download
        r2_url = f"{R2_PUBLIC}/dramas/{DRAMA_SLUG}/{filename}"
        
        # Perform HEAD request first to verify availability
        try:
            head_res = requests.head(r2_url, timeout=5)
            if head_res.status_code == 200:
                print(f"[{time.strftime('%H:%M:%S')}] Downloading Episode {ep}/{TOTAL_EPS} from R2...")
                # Download file
                r = requests.get(r2_url, timeout=60, stream=True)
                if r.ok:
                    temp_path = local_path + ".tmp"
                    with open(temp_path, "wb") as f:
                        for chunk in r.iter_content(chunk_size=1024*1024):
                            if chunk:
                                f.write(chunk)
                    # Rename temp file to final path
                    if os.path.exists(temp_path):
                        os.replace(temp_path, local_path)
                    print(f"   [OK] Saved {filename} ({os.path.getsize(local_path)/(1024*1024):.1f} MB)")
                    completed += 1
                    downloaded_this_run += 1
                else:
                    print(f"   [WARN] GET request failed for EP {ep}: {r.status_code}")
            elif head_res.status_code == 404:
                # Not yet uploaded to R2
                pass
            else:
                print(f"   [WARN] HEAD request returned {head_res.status_code} for EP {ep}")
        except Exception as e:
            print(f"   [ERROR] Network error checking/downloading EP {ep}: {e}")
            
    return completed, downloaded_this_run

def main():
    print("=" * 65)
    print("STARTING LOCAL DOWNLOADER FOR (Dub) Cinta dan Tombak Purba")
    print(f"   Destination: {LOCAL_DIR}")
    print("=" * 65)
    
    while True:
        try:
            completed, downloaded = check_and_download()
            print(f"[{time.strftime('%H:%M:%S')}] Status: {completed}/{TOTAL_EPS} episodes downloaded locally.")
            
            if completed >= TOTAL_EPS:
                print("\nALL 50 EPISODES SUCCESSFULLY DOWNLOADED LOCALLY!")
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
