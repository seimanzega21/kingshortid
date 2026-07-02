import os
import sys
import time
import requests
import subprocess
import psycopg2
import paramiko
import boto3
from botocore.config import Config
from pathlib import Path

# Workaround for paramiko DSSKey error in newer versions
if not hasattr(paramiko, 'DSSKey'):
    try:
        paramiko.DSSKey = paramiko.dsskey.DSSKey
    except Exception:
        class FakeDSSKey:
            pass
        paramiko.DSSKey = FakeDSSKey

from sshtunnel import SSHTunnelForwarder

sys.stdout.reconfigure(encoding='utf-8')

# Constants
DRAMA_ID = 'cmlisfgr8006gtlqebrmv3cwm'
DRAMA_SLUG = 'melolo/anak-fana-penakluk-langit'

SSH_HOST = '141.11.160.187'
SSH_USER = 'root'
SSH_PASS = 'Surya123!'
DB_IP = '10.0.1.25'
DB_PORT = 5432
LOCAL_PORT = 5440

DB_USER = 'supabase_admin'
DB_PASS = 'GoZViiH1AXLl73BqLdKDtpeGgwUzfW64'
DB_NAME = 'postgres'

R2_ENDPOINT = 'https://a142d3b29a5d64943cb251157e25eaf3.r2.cloudflarestorage.com'
R2_KEY_ID   = '07c99c897986ea52703c1285308d5e2c'
R2_SECRET   = '44788d376ffb216e1e73784b6fe1ff1423607928898a87c50819b52cdfc12e44'
BUCKET_NAME = 'shortlovers'
PUBLIC_BASE = 'https://stream.shortlovers.id'

TEMP_DIR = Path("d:/kingshortid/temp_transcode")
TEMP_DIR.mkdir(parents=True, exist_ok=True)

def get_r2_client():
    return boto3.client(
        's3',
        endpoint_url=R2_ENDPOINT,
        aws_access_key_id=R2_KEY_ID,
        aws_secret_access_key=R2_SECRET,
        config=Config(signature_version='s3v4'),
        region_name='auto'
    )

def transcode_to_540p(input_path, output_path):
    print(f"    Transcoding {input_path.name} to 540p (faststart)...")
    cmd = [
        'ffmpeg', '-y',
        '-err_detect', 'ignore_err',
        '-i', str(input_path),
        '-vf', 'scale=-2:540',
        '-c:v', 'libx264',
        '-crf', '30',
        '-preset', 'veryfast',
        '-maxrate', '800k',
        '-bufsize', '1600k',
        '-c:a', 'copy',
        '-movflags', '+faststart',
        '-loglevel', 'error',
        str(output_path)
    ]
    try:
        start_time = time.time()
        subprocess.run(cmd, check=True)
        duration = time.time() - start_time
        print(f"    Transcode finished in {duration:.1f} seconds. Output size: {output_path.stat().st_size / (1024*1024):.2f} MB")
        return True
    except subprocess.CalledProcessError as e:
        print(f"    FFmpeg failed: {e}")
        return False

def process_drama():
    r2 = get_r2_client()
    
    print("Starting SSH tunnel to VPS...")
    tunnel = SSHTunnelForwarder(
        (SSH_HOST, 22),
        ssh_username=SSH_USER,
        ssh_password=SSH_PASS,
        remote_bind_address=(DB_IP, DB_PORT),
        local_bind_address=('127.0.0.1', LOCAL_PORT),
        allow_agent=False,
        host_pkey_directories=[],
    )
    tunnel.start()
    print(f"SSH Tunnel active on local port {LOCAL_PORT}")
    
    try:
        # Connect to DB
        conn = psycopg2.connect(
            host='127.0.0.1',
            port=LOCAL_PORT,
            user=DB_USER,
            password=DB_PASS,
            database=DB_NAME
        )
        cur = conn.cursor()
        print("Connected to database successfully!")
        
        # Get all active episodes for the drama
        cur.execute("""
            SELECT id, episode_number, video_url, video_url_540p 
            FROM episodes 
            WHERE drama_id = %s 
            ORDER BY episode_number ASC
        """, (DRAMA_ID,))
        episodes = cur.fetchall()
        print(f"Found {len(episodes)} episodes in DB.")
        
        for ep in episodes:
            ep_id, ep_num, video_url, video_url_540p = ep
            print(f"\n[*] Processing Episode {ep_num}...")
            
            # Target R2 details
            r2_key_540 = f"{DRAMA_SLUG}/ep{ep_num:03d}_540p.mp4"
            expected_url_540 = f"{PUBLIC_BASE}/{r2_key_540}"
            
            # Check if already processed
            already_on_r2 = False
            try:
                r2.head_object(Bucket=BUCKET_NAME, Key=r2_key_540)
                already_on_r2 = True
                print(f"    540p file already exists on R2: {r2_key_540}")
            except:
                pass
                
            if already_on_r2:
                # If it's on R2, check if database matches
                if video_url_540p != expected_url_540:
                    print(f"    Updating DB: setting video_url_540p = '{expected_url_540}'")
                    cur.execute(
                        "UPDATE episodes SET video_url_540p = %s, updated_at = NOW() WHERE id = %s",
                        (expected_url_540, ep_id)
                    )
                    conn.commit()
                else:
                    print("    DB and R2 already up-to-date. Skipping.")
                continue
                
            # If not on R2, we need to download, transcode, and upload
            if not video_url:
                print("    [WARN] No 720p video URL found for this episode in DB. Skipping.")
                continue
                
            # Download 720p
            local_720 = TEMP_DIR / f"ep{ep_num:03d}_720.mp4"
            local_540 = TEMP_DIR / f"ep{ep_num:03d}_540.mp4"
            
            print(f"    Downloading original 720p video from {video_url}...")
            try:
                # Direct download stream
                r = requests.get(video_url, stream=True, timeout=30)
                if r.ok:
                    with open(local_720, 'wb') as f:
                        for chunk in r.iter_content(chunk_size=1024*1024):
                            f.write(chunk)
                    print(f"    Downloaded successfully. Size: {local_720.stat().st_size / (1024*1024):.2f} MB")
                else:
                    print(f"    [ERROR] Download failed: {r.status_code}")
                    continue
            except Exception as dl_err:
                print(f"    [ERROR] Exception during download: {dl_err}")
                if local_720.exists():
                    local_720.unlink()
                continue
                
            # Transcode
            if transcode_to_540p(local_720, local_540):
                # Upload to R2
                print(f"    Uploading 540p to R2 at key '{r2_key_540}'...")
                try:
                    r2.upload_file(
                        str(local_540), 
                        BUCKET_NAME, 
                        r2_key_540, 
                        ExtraArgs={'ContentType': 'video/mp4'}
                    )
                    print("    Upload complete!")
                    
                    # Update DB
                    print(f"    Updating DB: setting video_url_540p = '{expected_url_540}'")
                    cur.execute(
                        "UPDATE episodes SET video_url_540p = %s, updated_at = NOW() WHERE id = %s",
                        (expected_url_540, ep_id)
                    )
                    conn.commit()
                    
                except Exception as up_err:
                    print(f"    [ERROR] Upload or DB update failed: {up_err}")
            
            # Cleanup temp files
            if local_720.exists():
                local_720.unlink()
            if local_540.exists():
                local_540.unlink()
                
            # Yield for a brief period to avoid hammering resources
            time.sleep(1)
            
        print("\n[+] PROCESSING COMPLETED SUCCESSFULLY!")
        
    except Exception as e:
        print(f"Error during processing: {e}")
    finally:
        if 'conn' in locals() and conn:
            conn.close()
        tunnel.stop()
        print("SSH Tunnel closed.")

if __name__ == '__main__':
    process_drama()
