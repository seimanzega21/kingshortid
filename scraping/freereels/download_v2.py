"""
Download Pipeline v2 — Uses parsed JSON files (no FreeReels API needed)
For each parsed_*.json:
  1. Download cover from FreeReels CDN → upload to R2
  2. For each episode: HLS m3u8 → ffmpeg → MP4 → R2
  3. Update local DB with R2 video URLs
  4. Save pipeline status for resume

Resume-safe: skips episodes already uploaded to R2.
Run: python download_v2.py [--limit N] [--dry-run] [--drama NAME]
"""
import sys, json, time, os, re, subprocess, tempfile, glob
import psycopg2, requests, boto3
from pathlib import Path
from botocore.config import Config

sys.stdout.reconfigure(encoding='utf-8', errors='replace')

# ── R2 CONFIG ─────────────────────────────────────────────────────────────────
R2_ENDPOINT = 'https://a142d3b29a5d64943cb251157e25eaf3.r2.cloudflarestorage.com'
R2_KEY_ID   = '07c99c897986ea52703c1285308d5e2c'
R2_SECRET   = '44788d376ffb216e1e73784b6fe1ff1423607928898a87c50819b52cdfc12e44'
R2_BUCKET   = 'shortlovers'
R2_PUBLIC   = 'https://stream.shortlovers.id'

LOCAL_DB = 'postgresql://postgres:seiman21@localhost:5432/kingshort'

FFMPEG_CMD = 'ffmpeg'
FFMPEG_OPTS = [
    '-c:v', 'libx264', '-crf', '28', '-preset', 'fast',
    '-profile:v', 'baseline', '-level', '3.1',
    '-c:a', 'aac', '-b:a', '96k', '-ar', '44100',
    '-vf', 'scale=-2:720',
    '-movflags', 'faststart', '-y',
]
TEMP_DIR = Path(tempfile.gettempdir()) / 'freereels_dl'
TEMP_DIR.mkdir(exist_ok=True)
STATUS_FILE = Path(__file__).parent / 'pipeline_v2_status.json'

# ── R2 CLIENT ─────────────────────────────────────────────────────────────────
def get_r2():
    return boto3.client('s3', endpoint_url=R2_ENDPOINT,
        aws_access_key_id=R2_KEY_ID, aws_secret_access_key=R2_SECRET,
        config=Config(signature_version='s3v4'), region_name='auto')

def r2_exists(r2, key):
    try: r2.head_object(Bucket=R2_BUCKET, Key=key); return True
    except: return False

def r2_upload(r2, path, key, ct='video/mp4'):
    with open(path, 'rb') as f:
        r2.upload_fileobj(f, R2_BUCKET, key,
            ExtraArgs={'ContentType': ct},
            Config=boto3.s3.transfer.TransferConfig(multipart_threshold=50*1024*1024))
    return f"{R2_PUBLIC}/{key}"

def r2_upload_bytes(r2, data, key, ct):
    r2.put_object(Bucket=R2_BUCKET, Key=key, Body=data, ContentType=ct)
    return f"{R2_PUBLIC}/{key}"

# ── FFMPEG ────────────────────────────────────────────────────────────────────
def download_episode(hls_url, out_mp4):
    """HLS m3u8 → MP4 via ffmpeg."""
    cmd = [FFMPEG_CMD, '-i', hls_url, *FFMPEG_OPTS, str(out_mp4)]
    try:
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=600,
                              encoding='utf-8', errors='replace')
        if result.returncode != 0:
            # Fallback: stream copy (no re-encode)
            cmd2 = [FFMPEG_CMD, '-i', hls_url, '-c', 'copy', '-movflags', 'faststart',
                    '-y', str(out_mp4)]
            result2 = subprocess.run(cmd2, capture_output=True, text=True, timeout=600,
                                    encoding='utf-8', errors='replace')
            if result2.returncode != 0:
                return False, result.stderr[-200:] if result.stderr else '?'
        if not out_mp4.exists() or out_mp4.stat().st_size < 10000:
            return False, 'output too small'
        return True, f'{out_mp4.stat().st_size/1024/1024:.1f}MB'
    except subprocess.TimeoutExpired:
        return False, 'timeout 600s'
    except Exception as e:
        return False, str(e)

# ── HELPERS ───────────────────────────────────────────────────────────────────
def safe_folder(title):
    s = re.sub(r'\(Sulih Suara\)', '', title, flags=re.IGNORECASE).strip()
    s = re.sub(r'[^\w\s-]', '', s.lower())
    return re.sub(r'[\s_-]+', '_', s).strip('_')[:50] or 'drama'

def load_status():
    if STATUS_FILE.exists():
        return json.loads(STATUS_FILE.read_text(encoding='utf-8'))
    return {}

def save_status(status):
    STATUS_FILE.write_text(json.dumps(status, ensure_ascii=False, indent=2), encoding='utf-8')

def download_cover_img(url):
    try:
        r = requests.get(url, timeout=15, headers={'User-Agent': 'Mozilla/5.0'})
        if r.ok and len(r.content) > 1000: return r.content
    except: pass
    return None

# ── COVER URL MAPPING ─────────────────────────────────────────────────────────
_cover_map = None
def get_cover_url(title):
    """Find cover URL from freereels_series_ids.json by matching title."""
    global _cover_map
    if _cover_map is None:
        ids_file = Path(__file__).parent / 'freereels_series_ids.json'
        if ids_file.exists():
            raw = json.loads(ids_file.read_text(encoding='utf-8'))
            _cover_map = {}
            for k, v in raw.items():
                if isinstance(v, dict) and v.get('cover'):
                    key = v.get('title', k).lower().strip()
                    _cover_map[key] = v['cover']
        else:
            _cover_map = {}
    
    # Try exact match first
    t = title.lower().strip()
    if t in _cover_map: return _cover_map[t]
    
    # Try partial match
    for k, url in _cover_map.items():
        # Remove "(Sulih Suara)" for comparison
        clean_k = re.sub(r'\(sulih suara\)', '', k, flags=re.IGNORECASE).strip()
        clean_t = re.sub(r'\(sulih suara\)', '', t, flags=re.IGNORECASE).strip()
        if clean_k and clean_t and (clean_k in clean_t or clean_t in clean_k):
            return url
    return ''

# ── PROCESS ONE DRAMA ─────────────────────────────────────────────────────────
def process_drama(r2, parsed_file, status, dry_run=False):
    data = json.loads(Path(parsed_file).read_text(encoding='utf-8'))
    title = data.get('drama', 'Unknown')
    episodes = data.get('episodes', [])
    folder = safe_folder(title)
    prefix = f'freereels/{folder}'
    drama_key = os.path.basename(parsed_file)

    print(f'\n  Drama: {title}')
    print(f'  R2 prefix: {prefix}')
    print(f'  Episodes: {len(episodes)}')

    if drama_key in status and status[drama_key].get('complete'):
        print(f'  SKIP: already complete')
        return status.get(drama_key, {})

    drama_status = status.get(drama_key, {
        'title': title, 'folder': folder, 'total': len(episodes),
        'uploaded': 0, 'cover_uploaded': False, 'complete': False,
        'r2_urls': {}
    })

    # 1. Download and upload cover
    if not drama_status.get('cover_uploaded') and not dry_run:
        cover_key = f'{prefix}/cover.jpg'
        if r2_exists(r2, cover_key):
            drama_status['cover_uploaded'] = True
            drama_status['cover_url'] = f'{R2_PUBLIC}/{cover_key}'
            print(f'  Cover: already in R2')
        else:
            # Try to fetch cover from FreeReels CDN
            cover_url = data.get('cover', '') or get_cover_url(title)
            if cover_url:
                img = download_cover_img(cover_url)
                if img:
                    r2_upload_bytes(r2, img, cover_key, 'image/jpeg')
                    drama_status['cover_uploaded'] = True
                    drama_status['cover_url'] = f'{R2_PUBLIC}/{cover_key}'
                    print(f'  Cover: uploaded ✓')
                else:
                    print(f'  Cover: download failed')
            else:
                print(f'  Cover: no URL in parsed JSON')

    # 2. Process episodes
    success = 0
    for i, ep in enumerate(episodes, 1):
        ep_num = ep.get('number', i)
        h264 = ep.get('h264', '')
        ep_key = f'ep_{ep_num:03d}'
        r2_key = f'{prefix}/ep_{ep_num:03d}.mp4'

        # Skip if already done
        if ep_key in drama_status.get('r2_urls', {}):
            success += 1
            continue

        if not h264:
            print(f'  [{i:03d}/{len(episodes)}] ep{ep_num:03d} — no HLS URL')
            continue

        if dry_run:
            drama_status['r2_urls'][ep_key] = f'{R2_PUBLIC}/{r2_key}'
            success += 1
            continue

        # Check if already in R2
        if r2_exists(r2, r2_key):
            drama_status['r2_urls'][ep_key] = f'{R2_PUBLIC}/{r2_key}'
            success += 1
            print(f'  [{i:03d}/{len(episodes)}] ep{ep_num:03d} — already in R2 ✓')
            continue

        # Download + convert
        out_mp4 = TEMP_DIR / f'{folder}_ep{ep_num:03d}.mp4'
        print(f'  [{i:03d}/{len(episodes)}] ep{ep_num:03d} — downloading...', end=' ', flush=True)
        ok, info = download_episode(h264, out_mp4)

        if ok:
            # Upload to R2
            url = r2_upload(r2, out_mp4, r2_key)
            drama_status['r2_urls'][ep_key] = url
            success += 1
            print(f'✓ {info} → R2')
            try: out_mp4.unlink()
            except: pass
        else:
            print(f'✗ {info}')

        # Save progress after each episode
        drama_status['uploaded'] = success
        status[drama_key] = drama_status
        save_status(status)
        time.sleep(0.5)

    drama_status['uploaded'] = success
    drama_status['complete'] = success == len(episodes)
    status[drama_key] = drama_status
    save_status(status)

    print(f'  Result: {success}/{len(episodes)} episodes')
    return drama_status

# ── DB UPDATE ─────────────────────────────────────────────────────────────────
def update_db(status):
    """Update local DB with R2 video URLs and cover URLs."""
    conn = psycopg2.connect(LOCAL_DB)
    cur = conn.cursor()
    updated_eps = 0
    updated_covers = 0

    for drama_key, info in status.items():
        title = info.get('title', '')
        folder = info.get('folder', '')
        cover_url = info.get('cover_url', '')
        r2_urls = info.get('r2_urls', {})

        if not title: continue

        # Find drama in DB by title (fuzzy match)
        cur.execute("""SELECT id, title FROM "Drama" 
                      WHERE title ILIKE %s LIMIT 1""", (f'%{title[:30]}%',))
        drama = cur.fetchone()
        if not drama:
            print(f'  DB: {title[:40]} — not found')
            continue

        drama_id = drama[0]

        # Update cover
        if cover_url:
            cur.execute('UPDATE "Drama" SET cover = %s WHERE id = %s AND (cover IS NULL OR cover = %s OR cover LIKE %s)',
                       (cover_url, drama_id, '', '%freereels%'))
            if cur.rowcount:
                updated_covers += 1

        # Update episode videoUrls
        for ep_key, r2_url in r2_urls.items():
            ep_num = int(ep_key.split('_')[1])
            cur.execute("""UPDATE "Episode" SET "videoUrl" = %s 
                          WHERE "dramaId" = %s AND "episodeNumber" = %s""",
                       (r2_url, drama_id, ep_num))
            if cur.rowcount:
                updated_eps += 1

    conn.commit()
    conn.close()
    print(f'\n  DB Updated: {updated_covers} covers, {updated_eps} episodes')

# ── MAIN ──────────────────────────────────────────────────────────────────────
import threading
_status_lock = threading.Lock()

def save_status_safe(status):
    with _status_lock:
        save_status(status)

def process_drama_safe(parsed_file, status, dry_run=False):
    """Thread-safe wrapper — each thread gets its own R2 client."""
    r2 = None if dry_run else get_r2()
    data = json.loads(Path(parsed_file).read_text(encoding='utf-8'))
    title = data.get('drama', 'Unknown')
    episodes = data.get('episodes', [])
    folder = safe_folder(title)
    prefix = f'freereels/{folder}'
    drama_key = os.path.basename(parsed_file)

    print(f'\n  🎬 [{drama_key}] {title}')
    print(f'     R2: {prefix} | Episodes: {len(episodes)}')

    with _status_lock:
        if drama_key in status and status[drama_key].get('complete'):
            print(f'     SKIP: already complete')
            return status.get(drama_key, {})

        drama_status = status.get(drama_key, {
            'title': title, 'folder': folder, 'total': len(episodes),
            'uploaded': 0, 'cover_uploaded': False, 'complete': False,
            'r2_urls': {}
        })

    # 1. Cover
    if not drama_status.get('cover_uploaded') and not dry_run:
        cover_key = f'{prefix}/cover.jpg'
        if r2_exists(r2, cover_key):
            drama_status['cover_uploaded'] = True
            drama_status['cover_url'] = f'{R2_PUBLIC}/{cover_key}'
            print(f'     Cover: already in R2')
        else:
            cover_url = data.get('cover', '') or get_cover_url(title)
            if cover_url:
                img = download_cover_img(cover_url)
                if img:
                    r2_upload_bytes(r2, img, cover_key, 'image/jpeg')
                    drama_status['cover_uploaded'] = True
                    drama_status['cover_url'] = f'{R2_PUBLIC}/{cover_key}'
                    print(f'     Cover: uploaded ✓')
                else:
                    print(f'     Cover: download failed from {cover_url[:60]}')
            else:
                print(f'     Cover: no URL found')

    # 2. Episodes
    success = 0
    for i, ep in enumerate(episodes, 1):
        ep_num = ep.get('number', i)
        h264 = ep.get('h264', '')
        ep_key = f'ep_{ep_num:03d}'
        r2_key = f'{prefix}/ep_{ep_num:03d}.mp4'

        if ep_key in drama_status.get('r2_urls', {}):
            success += 1
            continue

        if not h264:
            continue

        if dry_run:
            drama_status['r2_urls'][ep_key] = f'{R2_PUBLIC}/{r2_key}'
            success += 1
            continue

        if r2_exists(r2, r2_key):
            drama_status['r2_urls'][ep_key] = f'{R2_PUBLIC}/{r2_key}'
            success += 1
            print(f'     [{i:03d}/{len(episodes)}] ep{ep_num:03d} — R2 ✓')
            continue

        out_mp4 = TEMP_DIR / f'{folder}_ep{ep_num:03d}.mp4'
        print(f'     [{i:03d}/{len(episodes)}] ep{ep_num:03d} — dl...', end=' ', flush=True)
        ok, info = download_episode(h264, out_mp4)

        if ok:
            url = r2_upload(r2, out_mp4, r2_key)
            drama_status['r2_urls'][ep_key] = url
            success += 1
            print(f'✓ {info}')
            try: out_mp4.unlink()
            except: pass
        else:
            print(f'✗ {info[:60]}')

        drama_status['uploaded'] = success
        with _status_lock:
            status[drama_key] = drama_status
            save_status(status)
        time.sleep(0.3)

    drama_status['uploaded'] = success
    drama_status['complete'] = success == len(episodes)
    with _status_lock:
        status[drama_key] = drama_status
        save_status(status)

    print(f'     ✅ {title[:40]}: {success}/{len(episodes)} episodes')
    return drama_status

def main():
    import argparse
    from concurrent.futures import ThreadPoolExecutor, as_completed

    p = argparse.ArgumentParser(description='FreeReels Download Pipeline v2')
    p.add_argument('--limit', type=int, help='Max dramas to process')
    p.add_argument('--drama', help='Partial drama name to filter')
    p.add_argument('--dry-run', action='store_true', help='Dry run')
    p.add_argument('--update-db', action='store_true', help='Update DB with R2 URLs')
    p.add_argument('--workers', type=int, default=4, help='Parallel workers (default 4)')
    a = p.parse_args()

    print('=' * 55)
    print('  FreeReels Download Pipeline v2 (Parallel)')
    print('=' * 55)
    print(f'  Mode:    {"DRY-RUN" if a.dry_run else "PRODUCTION"}')
    print(f'  Workers: {a.workers}')
    print(f'  ffmpeg:  {FFMPEG_CMD}')
    print(f'  R2:      {R2_BUCKET}')

    parsed_dir = Path(__file__).parent
    parsed_files = sorted(parsed_dir.glob('parsed_*.json'))

    if a.drama:
        parsed_files = [f for f in parsed_files if a.drama.lower() in f.stem.lower()]
    if a.limit:
        parsed_files = parsed_files[:a.limit]

    print(f'  Dramas:  {len(parsed_files)}')

    status = load_status()

    ok = fail = skip = 0
    start_time = time.time()

    with ThreadPoolExecutor(max_workers=a.workers) as pool:
        futures = {}
        for pf in parsed_files:
            f = pool.submit(process_drama_safe, str(pf), status, a.dry_run)
            futures[f] = pf.stem

        for future in as_completed(futures):
            name = futures[future]
            try:
                res = future.result()
                if res and res.get('uploaded', 0) > 0:
                    ok += 1
                else:
                    skip += 1
            except Exception as e:
                import traceback; traceback.print_exc()
                fail += 1

    elapsed = time.time() - start_time
    print(f'\n{"=" * 55}')
    print(f'  ✓ Processed: {ok}  ⊘ Skipped: {skip}  ✗ Failed: {fail}')
    print(f'  ⏱ Time: {elapsed/60:.1f} minutes')

    if a.update_db and not a.dry_run:
        print('\n  Updating database...')
        update_db(status)

    print(f'\n  Status → {STATUS_FILE}')

if __name__ == '__main__':
    main()

