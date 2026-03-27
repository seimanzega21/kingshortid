"""
FreeReels VIP Batch Downloader
==============================
Downloads all VIP episodes from parsed_episodes.json,
converts HLS to MP4 via ffmpeg, and uploads to R2.

Usage:
  python download_vip.py                # Download all
  python download_vip.py --start 1      # Start from episode 1
  python download_vip.py --limit 5      # Only 5 episodes
  python download_vip.py --json file.json  # Use specific JSON
"""
import sys, json, os, time, subprocess, argparse, re, uuid
import requests, psycopg2
from pathlib import Path
import boto3
from botocore.config import Config

sys.stdout.reconfigure(encoding='utf-8', errors='replace')

# ── CONFIG ────────────────────────────────────────────────────────────────────
R2_ENDPOINT = 'https://a142d3b29a5d64943cb251157e25eaf3.r2.cloudflarestorage.com'
R2_KEY_ID   = '07c99c897986ea52703c1285308d5e2c'
R2_SECRET   = '44788d376ffb216e1e73784b6fe1ff1423607928898a87c50819b52cdfc12e44'
R2_BUCKET   = 'shortlovers'
R2_PUBLIC   = 'https://stream.shortlovers.id'
DATABASE_URL = 'postgresql://postgres:seiman21@localhost:5432/kingshort'
TEMP_DIR   = Path(os.environ.get('TEMP', '/tmp')) / 'fr_vip_dl'
TEMP_DIR.mkdir(exist_ok=True)

CDN_REFERER = 'https://m.mydramawave.com/'
CDN_HEADERS = {'Referer': CDN_REFERER, 'User-Agent': 'Mozilla/5.0'}

# ── R2 ────────────────────────────────────────────────────────────────────────
def get_r2():
    return boto3.client('s3', endpoint_url=R2_ENDPOINT,
                        aws_access_key_id=R2_KEY_ID, aws_secret_access_key=R2_SECRET,
                        config=Config(signature_version='s3v4'), region_name='auto')

def r2_exists(r2c, key):
    try: r2c.head_object(Bucket=R2_BUCKET, Key=key); return True
    except: return False

def r2_upload_file(r2c, path, key, ct='video/mp4'):
    with open(path, 'rb') as f:
        r2c.upload_fileobj(f, R2_BUCKET, key,
                           ExtraArgs={'ContentType': ct},
                           Config=boto3.s3.transfer.TransferConfig(
                               multipart_threshold=30*1024*1024,
                               multipart_chunksize=10*1024*1024))
    return f'{R2_PUBLIC}/{key}'

# ── DOWNLOAD episodes ────────────────────────────────────────────────────────
def download_hls(m3u8_url, output_path):
    """Download HLS stream and convert to MP4 via ffmpeg"""
    cmd = [
        'ffmpeg', '-y',
        '-headers', f'Referer: {CDN_REFERER}\r\nUser-Agent: Mozilla/5.0\r\n',
        '-i', m3u8_url,
        '-c', 'copy',  # No re-encoding, just remux
        '-movflags', 'faststart',
        str(output_path)
    ]
    print(f'    ffmpeg downloading...')
    result = subprocess.run(cmd, capture_output=True, text=True, timeout=600)
    if result.returncode != 0:
        print(f'    ffmpeg error: {result.stderr[-200:]}')
        return False
    size = output_path.stat().st_size if output_path.exists() else 0
    print(f'    Done: {size / 1024 / 1024:.1f} MB')
    return size > 100_000  # > 100KB

def download_subtitle(srt_url, output_path):
    """Download SRT subtitle file"""
    try:
        r = requests.get(srt_url, headers=CDN_HEADERS, timeout=30)
        if r.status_code == 200 and len(r.content) > 10:
            output_path.write_bytes(r.content)
            return True
    except:
        pass
    return False

def get_duration_seconds(mp4_path):
    """Get video duration via ffprobe"""
    try:
        cmd = ['ffprobe', '-v', 'error', '-show_entries', 'format=duration',
               '-of', 'default=noprint_wrappers=1:nokey=1', str(mp4_path)]
        r = subprocess.run(cmd, capture_output=True, text=True, timeout=30)
        return int(float(r.stdout.strip()))
    except:
        return 0

def process_drama(json_path, drama_slug, fr_key, start=1, limit=None):
    """Process all episodes from a parsed JSON file"""
    with open(json_path) as f:
        data = json.load(f)
    
    drama_name = data.get('drama', drama_slug)
    episodes = data.get('episodes', [])
    total = len(episodes)
    
    print(f'\n{"="*60}')
    print(f'Drama: {drama_name}')
    print(f'Total episodes: {total}')
    print(f'Starting from: {start}')
    if limit:
        print(f'Limit: {limit}')
    print(f'{"="*60}\n')

    r2c = get_r2()
    conn = psycopg2.connect(DATABASE_URL)
    cur = conn.cursor()
    
    # Find drama_id from FRkey in DB
    cur.execute("SELECT id, title FROM \"Drama\" WHERE description LIKE %s", (f'%[FRkey:{fr_key}]%',))
    row = cur.fetchone()
    if not row:
        print(f'Drama not found in DB with FRkey:{fr_key}')
        print(f'Available FRkey dramas:')
        cur.execute("SELECT id, title, substring(description from '\\[FRkey:([^\\]]+)\\]') FROM \"Drama\" WHERE description LIKE '%[FRkey:%'")
        for r in cur.fetchall():
            print(f'  {r[0]}: {r[1]} - FRkey:{r[2]}')
        conn.close()
        return
    
    drama_id = row[0]
    print(f'DB Drama: {row[1]} (id={drama_id})')
    
    processed = 0
    skipped = 0
    failed = 0
    
    for ep in episodes:
        ep_num = ep['number']
        if ep_num < start:
            continue
        if limit and processed >= limit:
            break
        
        print(f'\n--- Episode {ep_num}/{total} ---')
        
        # Check if already exists in DB
        r2_key = f'freereels/{drama_slug}/ep{ep_num:03d}.mp4'
        r2_url = f'{R2_PUBLIC}/{r2_key}'
        
        cur.execute('SELECT id FROM "Episode" WHERE "dramaId" = %s AND "episodeNumber" = %s',
                     (drama_id, ep_num))
        existing = cur.fetchone()
        if existing:
            print(f'  Already in DB (id={existing[0]}), skipping')
            skipped += 1
            continue
        
        # Check R2
        if r2_exists(r2c, r2_key):
            print(f'  Already in R2, inserting DB only')
            duration = 60  # default
        else:
            # Download HLS
            mp4_path = TEMP_DIR / f'ep{ep_num:03d}.mp4'
            h264_url = ep['h264']
            
            # Fix truncated URLs (Chrome console truncates with ...)
            if '…' in h264_url:
                print(f'  WARNING: Truncated URL, skipping')
                failed += 1
                continue
            
            if not download_hls(h264_url, mp4_path):
                print(f'  Download failed!')
                failed += 1
                continue
            
            duration = get_duration_seconds(mp4_path)
            print(f'  Duration: {duration}s')
            
            # Upload to R2
            print(f'  Uploading to R2: {r2_key}')
            r2_upload_file(r2c, mp4_path, r2_key)
            print(f'  Uploaded!')
            
            # Clean up temp
            mp4_path.unlink(missing_ok=True)
        
        # Upload subtitles
        sub_urls = []
        for i, srt_url in enumerate(ep.get('subtitles', [])):
            if '…' in srt_url:
                continue
            srt_key = f'freereels/{drama_slug}/ep{ep_num:03d}_sub{i}.srt'
            if not r2_exists(r2c, srt_key):
                srt_path = TEMP_DIR / f'ep{ep_num:03d}_sub{i}.srt'
                if download_subtitle(srt_url, srt_path):
                    r2c.put_object(Bucket=R2_BUCKET, Key=srt_key,
                                   Body=srt_path.read_bytes(),
                                   ContentType='application/x-subrip')
                    srt_path.unlink(missing_ok=True)
            sub_urls.append(f'{R2_PUBLIC}/{srt_key}')
        
        # Insert into DB
        sub_json = json.dumps(sub_urls) if sub_urls else None
        ep_id = str(uuid.uuid4())
        ep_title = f'Episode {ep_num}'
        cur.execute('''
            INSERT INTO "Episode" (id, "dramaId", "episodeNumber", title, "videoUrl",
                                    "duration", "isActive",
                                    "createdAt", "updatedAt")
            VALUES (%s, %s, %s, %s, %s, %s, false, NOW(), NOW())
            RETURNING id
        ''', (ep_id, drama_id, ep_num, ep_title, r2_url, duration))
        new_id = cur.fetchone()[0]
        conn.commit()
        print(f'  DB: Episode {ep_num} inserted (id={new_id})')
        processed += 1
    
    # Update total episodes
    cur.execute('UPDATE "Drama" SET "totalEpisodes" = (SELECT COUNT(*) FROM "Episode" WHERE "dramaId" = %s) WHERE id = %s',
                (drama_id, drama_id))
    conn.commit()
    conn.close()
    
    print(f'\n{"="*60}')
    print(f'DONE! Processed: {processed}, Skipped: {skipped}, Failed: {failed}')
    print(f'{"="*60}')

if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--json', default='parsed_episodes.json')
    parser.add_argument('--slug', default='bos-kuliah-lagi')
    parser.add_argument('--frkey', default='eNFDnztZRb')
    parser.add_argument('--start', type=int, default=1)
    parser.add_argument('--limit', type=int, default=None)
    args = parser.parse_args()
    
    process_drama(args.json, args.slug, args.frkey, args.start, args.limit)
