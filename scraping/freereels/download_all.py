"""
Master Batch Downloader - All FreeReels Sulih Suara Dramas
==========================================================
Reads all_dramas_master.json and downloads ALL episodes for ALL dramas.
Runs sequentially: finishes one drama before starting the next.

Usage:
  python download_all.py                    # Download all dramas
  python download_all.py --drama 0          # Only first drama
  python download_all.py --skip-existing    # Skip dramas with existing episodes
"""
import sys, json, os, time, subprocess, argparse, uuid
import requests, psycopg2
from pathlib import Path
import boto3
from botocore.config import Config

sys.stdout.reconfigure(encoding='utf-8', errors='replace')

R2_ENDPOINT = 'https://a142d3b29a5d64943cb251157e25eaf3.r2.cloudflarestorage.com'
R2_KEY_ID   = '07c99c897986ea52703c1285308d5e2c'
R2_SECRET   = '44788d376ffb216e1e73784b6fe1ff1423607928898a87c50819b52cdfc12e44'
R2_BUCKET   = 'shortlovers'
R2_PUBLIC   = 'https://stream.shortlovers.id'
DATABASE_URL = 'postgresql://postgres:seiman21@localhost:5432/kingshort'
TEMP_DIR   = Path(os.environ.get('TEMP', '/tmp')) / 'fr_vip_dl'
TEMP_DIR.mkdir(exist_ok=True)
CDN_REFERER = 'https://m.mydramawave.com/'

def get_r2():
    return boto3.client('s3', endpoint_url=R2_ENDPOINT,
                        aws_access_key_id=R2_KEY_ID, aws_secret_access_key=R2_SECRET,
                        config=Config(signature_version='s3v4'), region_name='auto')

def r2_exists(r2c, key):
    try: r2c.head_object(Bucket=R2_BUCKET, Key=key); return True
    except: return False

def r2_upload(r2c, path, key, ct='video/mp4'):
    with open(path, 'rb') as f:
        r2c.upload_fileobj(f, R2_BUCKET, key,
                           ExtraArgs={'ContentType': ct},
                           Config=boto3.s3.transfer.TransferConfig(
                               multipart_threshold=30*1024*1024,
                               multipart_chunksize=10*1024*1024))

def download_hls(m3u8_url, output_path):
    cmd = ['ffmpeg', '-y',
           '-headers', f'Referer: {CDN_REFERER}\r\nUser-Agent: Mozilla/5.0\r\n',
           '-i', m3u8_url, '-c', 'copy', '-movflags', 'faststart',
           str(output_path)]
    result = subprocess.run(cmd, capture_output=True, text=True, timeout=600)
    if result.returncode != 0:
        return False
    return output_path.exists() and output_path.stat().st_size > 100_000

def get_duration(mp4):
    try:
        cmd = ['ffprobe', '-v', 'error', '-show_entries', 'format=duration',
               '-of', 'default=noprint_wrappers=1:nokey=1', str(mp4)]
        r = subprocess.run(cmd, capture_output=True, text=True, timeout=30)
        return int(float(r.stdout.strip()))
    except: return 60

def process_all(master_json, drama_index=None):
    with open(master_json) as f:
        dramas = json.load(f)
    
    r2c = get_r2()
    conn = psycopg2.connect(DATABASE_URL)
    cur = conn.cursor()
    
    grand_total = sum(d['episodes'] for d in dramas)
    print(f'\n{"="*60}')
    print(f'MASTER BATCH: {len(dramas)} dramas, {grand_total} episodes')
    print(f'{"="*60}\n')
    
    global_done = 0
    global_skip = 0
    global_fail = 0
    
    for di, drama in enumerate(dramas):
        if drama_index is not None and di != drama_index:
            continue
        
        title = drama['title']
        slug = drama['slug']
        drama_id = drama['drama_id']
        parsed_file = drama['parsed_json']
        
        # Load parsed episodes
        parsed_path = os.path.join(os.path.dirname(master_json), parsed_file)
        if not os.path.exists(parsed_path):
            print(f'SKIP: {parsed_file} not found')
            continue
        
        with open(parsed_path) as f:
            pdata = json.load(f)
        episodes = pdata.get('episodes', [])
        
        print(f'\n{"="*60}')
        print(f'[{di+1}/{len(dramas)}] {title} ({len(episodes)} eps)')
        print(f'  Drama ID: {drama_id}')
        print(f'{"="*60}')
        
        for ep in episodes:
            ep_num = ep['number']
            r2_key = f'freereels/{slug}/ep{ep_num:03d}.mp4'
            r2_url = f'{R2_PUBLIC}/{r2_key}'
            
            # Check DB
            cur.execute('SELECT id FROM "Episode" WHERE "dramaId" = %s AND "episodeNumber" = %s',
                        (drama_id, ep_num))
            if cur.fetchone():
                global_skip += 1
                continue
            
            # Check truncated URLs
            h264 = ep['h264']
            if '\u2026' in h264 or not h264:
                global_fail += 1
                continue
            
            print(f'  Ep {ep_num}/{len(episodes)}', end=' ', flush=True)
            
            need_download = not r2_exists(r2c, r2_key)
            duration = 60
            
            if need_download:
                mp4 = TEMP_DIR / f'ep{ep_num:03d}.mp4'
                if download_hls(h264, mp4):
                    duration = get_duration(mp4)
                    print(f'DL:{mp4.stat().st_size//1024//1024}MB', end=' ', flush=True)
                    r2_upload(r2c, mp4, r2_key)
                    mp4.unlink(missing_ok=True)
                    print('R2', end=' ', flush=True)
                else:
                    print('FAIL')
                    global_fail += 1
                    continue
            
            # Insert DB
            ep_id = str(uuid.uuid4())
            cur.execute('''
                INSERT INTO "Episode" (id, "dramaId", "episodeNumber", title, "videoUrl",
                                        "duration", "isActive", "createdAt", "updatedAt")
                VALUES (%s, %s, %s, %s, %s, %s, false, NOW(), NOW())
            ''', (ep_id, drama_id, ep_num, f'Episode {ep_num}', r2_url, duration))
            conn.commit()
            global_done += 1
            print('DB OK')
        
        # Update total episodes
        cur.execute('UPDATE "Drama" SET "totalEpisodes" = (SELECT COUNT(*) FROM "Episode" WHERE "dramaId" = %s) WHERE id = %s',
                    (drama_id, drama_id))
        conn.commit()
    
    conn.close()
    print(f'\n{"="*60}')
    print(f'MASTER BATCH COMPLETE!')
    print(f'  Done: {global_done}, Skipped: {global_skip}, Failed: {global_fail}')
    print(f'{"="*60}')

if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--master', default='all_dramas_master.json')
    parser.add_argument('--drama', type=int, default=None, help='Index of single drama to process')
    args = parser.parse_args()
    process_all(args.master, args.drama)
