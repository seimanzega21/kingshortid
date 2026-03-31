import os, subprocess, time, psycopg2, tempfile, sys
import boto3
from botocore.config import Config
from pathlib import Path

# =================CONFIGURATION=================
# On VPS, localhost is the database
DATABASE_URL = 'postgresql://supabase_admin:GoZViiH1AXLl73BqLdKDtpeGgwUzfW64@127.0.0.1:5432/postgres'

R2_ENDPOINT = 'https://a142d3b29a5d64943cb251157e25eaf3.r2.cloudflarestorage.com'
R2_KEY_ID   = '07c99c897986ea52703c1285308d5e2c'
R2_SECRET   = '44788d376ffb216e1e73784b6fe1ff1423607928898a87c50819b52cdfc12e44'
R2_BUCKET   = 'shortlovers'
R2_PUBLIC   = 'https://stream.shortlovers.id'

TEMP_DIR = Path('/tmp/video_backfill')
TEMP_DIR.mkdir(exist_ok=True)
# ===============================================

def get_r2():
    return boto3.client('s3', endpoint_url=R2_ENDPOINT,
                        aws_access_key_id=R2_KEY_ID, aws_secret_access_key=R2_SECRET,
                        config=Config(signature_version='s3v4'), region_name='auto')

def r2_upload(r2c, path, key, ct='video/mp4'):
    with open(path, 'rb') as f:
        r2c.upload_fileobj(f, R2_BUCKET, key,
                           ExtraArgs={'ContentType': ct},
                           Config=boto3.s3.transfer.TransferConfig(
                               multipart_threshold=30*1024*1024,
                               multipart_chunksize=10*1024*1024))

def convert_to_540p(input_url, output_path):
    # Uses ffmpeg to download and scale on the fly
    cmd = [
        'ffmpeg', '-y', 
        '-i', input_url,
        '-vf', 'scale=-2:540',
        '-c:v', 'libx264', '-crf', '28', '-preset', 'fast',
        '-c:a', 'aac', '-b:a', '128k',
        '-movflags', '+faststart',
        str(output_path)
    ]
    # Supress output to keep terminal clean
    result = subprocess.run(cmd, capture_output=True, text=True, timeout=1200) # 20 mins max per ep
    if result.returncode != 0:
        print(f"FFmpeg Error: {result.stderr[-500:]}")
        return False
    return output_path.exists() and output_path.stat().st_size > 100_000

def run_backfill():
    print(f"Connecting to database...")
    try:
        conn = psycopg2.connect(DATABASE_URL)
        cur = conn.cursor()
    except Exception as e:
        print(f"Failed to connect to database: {e}")
        sys.exit(1)
        
    r2c = get_r2()
    
    # Check physical column names using drizzle naming conventions
    try:
        cur.execute('''
            SELECT id, episode_number, video_url, drama_id 
            FROM episodes 
            WHERE video_url_540p IS NULL 
            AND video_url IS NOT NULL
            ORDER BY created_at DESC
        ''')
        pending_eps = cur.fetchall()
    except Exception as e:
        print(f"DB Error: {e}. Trying raw Prisma table names...")
        conn.rollback()
        cur.execute('''
            SELECT id, "episodeNumber", "videoUrl", "dramaId" 
            FROM "Episode" 
            WHERE "videoUrl540p" IS NULL 
            AND "videoUrl" IS NOT NULL
        ''')
        pending_eps = cur.fetchall()

    print(f"Found {len(pending_eps)} episodes missing 540p resolution.")
    
    success = 0
    failed = 0
    
    for i, ep in enumerate(pending_eps):
        ep_id = ep[0]
        ep_num = ep[1]
        video_url = ep[2]
        drama_id = ep[3]
        
        # Original keys format: freereels/drama-slug/ep001.mp4 
        # We'll just generate a unique name or append _540p
        # E.g. https://stream.shortlovers.id/freereels/some-drama/ep001.mp4 
        
        parsed_key = video_url.replace(R2_PUBLIC + "/", "")
        if parsed_key == video_url:
            # If it's not our R2 domain, just make a generic key
            parsed_key = f"converted/{drama_id}/ep{ep_num:03d}.mp4"
            
        key_540p = parsed_key.replace(".mp4", "_540p.mp4")
        url_540p = f"{R2_PUBLIC}/{key_540p}"
        
        print(f"[{i+1}/{len(pending_eps)}] Processing Ep {ep_num} ({ep_id[:6]})... ", end='', flush=True)
        
        temp_file = TEMP_DIR / f"temp_{ep_id}_540p.mp4"
        
        try:
            # 1. Download & Convert
            if convert_to_540p(video_url, temp_file):
                print(f"Encoded ({temp_file.stat().st_size//1024//1024}MB)... ", end='', flush=True)
                
                # 2. Upload to R2
                r2_upload(r2c, temp_file, key_540p)
                print(f"Uploaded... ", end='', flush=True)
                
                # 3. Update Database
                try:
                    cur.execute('UPDATE episodes SET video_url_540p = %s, updated_at = NOW() WHERE id = %s', (url_540p, ep_id))
                except:
                    conn.rollback()
                    cur.execute('UPDATE "Episode" SET "videoUrl540p" = %s, "updatedAt" = NOW() WHERE id = %s', (url_540p, ep_id))
                
                conn.commit()
                success += 1
                print("DB OK")
            else:
                print("Failed encoding")
                failed += 1
        except Exception as e:
            print(f"Error: {e}")
            failed += 1
        finally:
            if temp_file.exists():
                temp_file.unlink()
                
    print(f"\n====================\nDONE!")
    print(f"Success: {success} | Failed: {failed}")
    
if __name__ == '__main__':
    run_backfill()
