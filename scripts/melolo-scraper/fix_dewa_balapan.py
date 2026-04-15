import os
import requests
import json
import subprocess
import boto3
from pathlib import Path
from dotenv import load_dotenv

load_dotenv('d:\\kingshortid\\cf-backend\\.env.production')

s3 = boto3.client(
    "s3",
    endpoint_url=os.getenv("R2_ENDPOINT"),
    aws_access_key_id=os.getenv("R2_ACCESS_KEY_ID"),
    aws_secret_access_key=os.getenv("R2_SECRET_ACCESS_KEY"),
)

DRAMA_ID = "cmleext6402nghx5eh2fnx9ps"

def fix_dewa_balapan():
    print("Fetching episodes...")
    res = requests.get(f'https://api.shortlovers.id/api/dramas/{DRAMA_ID}/episodes')
    episodes = res.json()
    
    print(f"Total episodes: {len(episodes)}")
    
    R2_BUCKET = os.getenv("R2_BUCKET", "shortlovers-media")
    TEMP_DIR = Path("C:/tmp/microdrama_fix")
    os.makedirs(TEMP_DIR, exist_ok=True)
    
    sql_queries = []
    
    for ep in episodes:
        video_url = ep.get('videoUrl')
        if not video_url or 'playlist.m3u8' not in video_url:
            print(f"Skipping episode {ep['episodeNumber']}, not m3u8: {video_url}")
            continue
            
        print(f"\nProcessing Episode {ep['episodeNumber']}...")
        
        # Download and merge m3u8 directly to mp4 using ffmpeg
        output_mp4 = TEMP_DIR / f"ep{ep['episodeNumber']:03d}.mp4"
        
        cmd = [
            "ffmpeg", "-y",
            "-i", video_url,
            "-c:v", "libx264", "-preset", "fast", "-crf", "23",
            "-c:a", "aac", "-b:a", "128k",
            "-movflags", "+faststart",
            str(output_mp4)
        ]
        
        try:
            print(f"    [~] Running FFmpeg for ep {ep['episodeNumber']}...")
            subprocess.run(cmd, capture_output=True, text=True, check=True)
            print(f"    [+] FFmpeg success!")
        except Exception as e:
            print(f"    [!] FFmpeg failed: {e}")
            continue
            
        # Upload to R2
        r2_key = f"vidrama/microdrama/dewa-balapan/ep{ep['episodeNumber']:03d}.mp4"
        print(f"    [~] Uploading to R2: {r2_key}")
        try:
            s3.upload_file(
                Filename=str(output_mp4),
                Bucket=R2_BUCKET,
                Key=r2_key,
                ExtraArgs={
                    "ContentType": "video/mp4",
                    "CacheControl": "public, max-age=31536000, immutable"
                }
            )
            r2_url = f"https://stream.shortlovers.id/{r2_key}"
            print(f"    [+] Uploaded successfully! -> {r2_url}")
            
            # Generate SQL update
            sql_queries.append(f"UPDATE episodes SET video_url = '{r2_url}' WHERE id = '{ep['id']}';")
            
        except Exception as e:
            print(f"    [!] Upload failed: {e}")
            
        # Cleanup
        try:
            os.remove(output_mp4)
        except:
            pass

    # Save SQL
    sql_file = Path("d:/kingshortid/scripts/melolo-scraper/update_dewa_balapan.sql")
    if sql_queries:
        with open(sql_file, "w") as f:
            f.write("\n".join(sql_queries))
        print(f"\n[+] Saved {len(sql_queries)} SQL updates to {sql_file}")
    else:
        print("\n[!] No SQL updates generated.")
        
if __name__ == "__main__":
    fix_dewa_balapan()
