import os
import sys
import requests
import subprocess
import json
import re

DRAMA_ID = 'ygjqw4e2ypmafvn5ap6249ba'
OUTPUT_DIR = r'D:\KingshortId\Download Drama\Salah Sangka Berujung Jadi Ayah'

if not os.path.exists(OUTPUT_DIR):
    os.makedirs(OUTPUT_DIR)

print(f"Fetching drama info for {DRAMA_ID}...")
headers = {'User-Agent': 'Mozilla/5.0'}
res = requests.get(f'https://api.shortlovers.id/api/dramas/{DRAMA_ID}', headers=headers)

if res.status_code != 200:
    print(f"Failed to fetch drama! Code: {res.status_code}")
    sys.exit(1)

data = res.json()
episodes = data.get('episodes', [])
if not episodes:
    print("No episodes found!")
    sys.exit(1)

print(f"Found {len(episodes)} episodes! Starting download to {OUTPUT_DIR}...")

for ep in episodes:
    ep_num = str(ep['episodeNumber']).zfill(3)
    # create safe title
    safe_title = re.sub(r'[\\/:*?"<>|]', '', ep.get('title', f"Episode {ep_num}"))
    out_file = os.path.join(OUTPUT_DIR, f"{ep_num} - {safe_title}.mp4")
    
    video_url = ep.get('videoUrl')
    if not video_url:
        print(f"Skip ep {ep_num}, no videoUrl")
        continue

    if os.path.exists(out_file):
        print(f"Skip {out_file}, already exists")
        continue

    print(f"\n--- Downloading Episode {ep_num} ---")
    print(f"URL: {video_url}")
    
    # Use FFmpeg to download M3U8/MP4 streams
    # -y overwrites (though we check exists above), -c copy keeps original quality
    cmd = [
        "ffmpeg",
        "-y",
        "-i", video_url,
        "-c", "copy",
        "-bsf:a", "aac_adtstoasc", # often needed for m3u8
        out_file
    ]
    
    try:
        subprocess.run(cmd, check=True)
    except Exception as e:
        print(f"Failed to download episode {ep_num}: {e}")

print("\nAll downloads finished!")
