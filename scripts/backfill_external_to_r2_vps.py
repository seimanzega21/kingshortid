import os, subprocess, time, psycopg2, tempfile, sys
import boto3
from botocore.config import Config
from pathlib import Path

# =================CONFIGURATION=================
# Connects directly to PostgreSQL on the VPS
DATABASE_URL = 'postgresql://supabase_admin:GoZViiH1AXLl73BqLdKDtpeGgwUzfW64@127.0.0.1:5432/postgres'

R2_ENDPOINT = 'https://a142d3b29a5d64943cb251157e25eaf3.r2.cloudflarestorage.com'
R2_KEY_ID   = '07c99c897986ea52703c1285308d5e2c'
R2_SECRET   = '44788d376ffb216e1e73784b6fe1ff1423607928898a87c50819b52cdfc12e44'
R2_BUCKET   = 'shortlovers'
R2_PUBLIC   = 'https://stream.shortlovers.id'

TEMP_DIR = Path('/tmp/video_migration')
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

def convert_video(input_url, temp_720, temp_540):
    # 1. Download original/720p using copy
    cmd_720 = ['ffmpeg', '-y', '-i', input_url]
    if '.m3u8' in input_url:
        cmd_720 += ['-c', 'copy', '-bsf:a', 'aac_adtstoasc', '-movflags', '+faststart', str(temp_720)]
    else:
        cmd_720 += ['-c', 'copy', '-movflags', '+faststart', str(temp_720)]
        
    res1 = subprocess.run(cmd_720, capture_output=True, text=True, timeout=1200)
    if res1.returncode != 0 or not temp_720.exists():
        print(f"FFmpeg 720p Error: {res1.stderr[-300:]}")
        return False

    # 2. Scale 720p to 540p
    cmd_540 = [
        'ffmpeg', '-y', 
        '-i', str(temp_720),
        '-vf', 'scale=-2:540',
        '-c:v', 'libx264', '-crf', '28', '-preset', 'fast',
        '-c:a', 'aac', '-b:a', '128k',
        '-movflags', '+faststart',
        str(temp_540)
    ]
    res2 = subprocess.run(cmd_540, capture_output=True, text=True, timeout=1200)
    if res2.returncode != 0 or not temp_540.exists():
        print(f"FFmpeg 540p Error: {res2.stderr[-300:]}")
        return False
        
    return True

def get_prefix_from_cover(cover_url, drama_id):
    if not cover_url or cover_url.startswith('/api/uploads'):
        return f"converted/{drama_id}"
    
    # Example cover: https://stream.shortlovers.id/dramas/microdrama/salah-sangka/cover.webp
    parsed = cover_url.replace(R2_PUBLIC + "/", "").replace("cover.webp", "").replace("cover.jpg", "").replace("cover.png", "")
    parsed = parsed.strip('/')
    if not parsed:
        return f"converted/{drama_id}"
    return parsed

def run_migration():
    print("Connecting to database...")
    try:
        conn = psycopg2.connect(DATABASE_URL)
        cur = conn.cursor()
    except Exception as e:
        print(f"Failed to connect to DB: {e}")
        sys.exit(1)
        
    r2c = get_r2()
    
    try:
        cur.execute('''
            SELECT e.id, e.episode_number, e.video_url, d.cover, d.id 
            FROM episodes e
            JOIN dramas d ON e.drama_id = d.id
            WHERE e.video_url NOT LIKE '%shortlovers.id%' 
              AND e.video_url NOT LIKE '%r2.%'
              AND e.is_active = true
            ORDER BY d.created_at ASC, e.episode_number ASC
        ''')
        external_eps = cur.fetchall()
    except Exception as e:
        print(f"DB Error (trying Drizzle): {e}. Trying raw Prisma table names...")
        conn.rollback()
        cur.execute('''
            SELECT e.id, e."episodeNumber", e."videoUrl", d.cover, d.id 
            FROM "Episode" e
            JOIN "Drama" d ON e."dramaId" = d.id
            WHERE e."videoUrl" NOT LIKE '%shortlovers.id%' 
              AND e."videoUrl" NOT LIKE '%r2.%'
              AND e."isActive" = true
            ORDER BY d."createdAt" ASC, e."episodeNumber" ASC
        ''')
        external_eps = cur.fetchall()

    print(f"\n[ALERT] Found {len(external_eps)} external episodes mapped for R2 migration.")
    success, failed = 0, 0
    
    for i, ep in enumerate(external_eps):
        ep_id = ep[0]
        ep_num = ep[1]
        video_url = ep[2]
        cover_url = ep[3]
        drama_id = ep[4]
        
        prefix = get_prefix_from_cover(cover_url, drama_id)
        key_720p = f"{prefix}/ep{ep_num:03d}.mp4"
        key_540p = f"{prefix}/ep{ep_num:03d}_540p.mp4"
        
        url_720p = f"{R2_PUBLIC}/{key_720p}"
        url_540p = f"{R2_PUBLIC}/{key_540p}"
        
        print(f"[{i+1}/{len(external_eps)}] Migrating Ep {ep_num} ({prefix[:30]})... ", end='', flush=True)
        
        temp_720 = TEMP_DIR / f"tmp_720_{ep_id}.mp4"
        temp_540 = TEMP_DIR / f"tmp_540_{ep_id}.mp4"
        
        try:
            if convert_video(video_url, temp_720, temp_540):
                print(f"D/L & Encoded... ", end='', flush=True)
                
                # Upload both parts
                r2_upload(r2c, temp_720, key_720p)
                r2_upload(r2c, temp_540, key_540p)
                print(f"R2 OK... ", end='', flush=True)
                
                # Database swap
                try:
                    cur.execute('UPDATE episodes SET video_url = %s, video_url_540p = %s, updated_at = NOW() WHERE id = %s', (url_720p, url_540p, ep_id))
                except:
                    conn.rollback()
                    cur.execute('UPDATE "Episode" SET "videoUrl" = %s, "videoUrl540p" = %s, "updatedAt" = NOW() WHERE id = %s', (url_720p, url_540p, ep_id))
                
                conn.commit()
                success += 1
                print("DB OK")
            else:
                print("Failed Video Processing")
                failed += 1
        except Exception as e:
            print(f"Error: {e}")
            failed += 1
        finally:
            # Automatic Cleanup
            if temp_720.exists(): temp_720.unlink()
            if temp_540.exists(): temp_540.unlink()
                
    print(f"\n====================\nMIGRATION COMPLETE!")
    print(f"Archived Success: {success} | Failed: {failed}")
    
if __name__ == '__main__':
    run_migration()
