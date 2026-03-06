#!/usr/bin/env python3
"""
TARGETED RE-SCRAPE: 40 Empty Dramas
====================================
Re-scrapes dramas that have metadata.json but no episodes/covers.
Uses existing auto_discover.py pipeline functions via import.
"""
import json, sys, io, os, time, re, threading, subprocess, requests, boto3
from pathlib import Path
from concurrent.futures import ThreadPoolExecutor, as_completed
from urllib.parse import urlparse, parse_qs
from dotenv import load_dotenv

load_dotenv(Path(__file__).parent / '.env')

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
sys.stdout.reconfigure(line_buffering=True)

# ─── Config ──────────────────────────────────────────────────────────────────
SCRIPT_DIR = Path(__file__).parent
OUTPUT_DIR = SCRIPT_DIR / "r2_ready" / "melolo"
DOWNLOAD_DIR = SCRIPT_DIR / "downloads"
HLS_SEGMENT_DURATION = 6
BATCH_SIZE = 8
API_DELAY = 2.0
API_MAX_RETRIES = 3
API_BACKOFF_BASE = 30

R2_ENDPOINT = os.getenv("R2_ENDPOINT", "")
R2_ACCESS_KEY_ID = os.getenv("R2_ACCESS_KEY_ID", "")
R2_SECRET_ACCESS_KEY = os.getenv("R2_SECRET_ACCESS_KEY", "")
R2_BUCKET = os.getenv("R2_BUCKET_NAME", "shortlovers")

CONTENT_TYPES = {
    '.jpg': 'image/jpeg', '.jpeg': 'image/jpeg', '.png': 'image/png',
    '.json': 'application/json', '.m3u8': 'application/vnd.apple.mpegurl',
    '.ts': 'video/mp2t', '.mp4': 'video/mp4',
}

api_semaphore = threading.Semaphore(6)
print_lock = threading.Lock()
stats_lock = threading.Lock()
stats = {'completed': 0, 'failed': 0, 'episodes': 0, 'bytes': 0}


def safe_print(*args, **kwargs):
    with print_lock:
        print(*args, **kwargs, flush=True)


def slugify(text):
    text = text.lower().strip()
    text = re.sub(r'[^\w\s-]', '', text)
    text = re.sub(r'[\s_]+', '-', text)
    text = re.sub(r'-+', '-', text)
    return text[:60].rstrip('-')


# ─── Auth extraction ─────────────────────────────────────────────────────────
def extract_auth(har_path):
    with open(har_path, 'r', encoding='utf-8') as f:
        har = json.load(f)
    templates = {}
    for entry in har['log']['entries']:
        url = entry['request']['url']
        req = entry['request']
        parsed = urlparse(url)
        headers = {h['name']: h['value'] for h in req['headers']}
        params = {k: v[0] for k, v in parse_qs(parsed.query).items()}

        if 'video_detail/v1/' in url and 'multi' not in url and 'video_detail' not in templates:
            body = {}
            if 'postData' in req:
                try:
                    body = json.loads(req['postData'].get('text', '{}'))
                except:
                    pass
            templates['video_detail'] = {
                'base_url': parsed.scheme + '://' + parsed.netloc + parsed.path,
                'headers': headers, 'params': params, 'body_template': body,
            }
        if 'multi_video_model' in url and 'video_model' not in templates:
            templates['video_model'] = {
                'base_url': url.split('?')[0],
                'headers': {h['name'].lower(): h['value'] for h in req['headers']},
                'params': params,
            }
    return templates


# ─── API functions ────────────────────────────────────────────────────────────
def fetch_episode_list(templates, series_id):
    t = templates.get('video_detail')
    if not t:
        return []
    body = dict(t.get('body_template', {}))
    body['series_id'] = series_id
    params = dict(t['params'])
    params['_rticket'] = str(int(time.time() * 1000))

    for attempt in range(API_MAX_RETRIES):
        try:
            api_semaphore.acquire()
            try:
                resp = requests.post(t['base_url'], params=params, headers=t['headers'],
                                     json=body, timeout=20)
            finally:
                api_semaphore.release()

            if resp.status_code == 429:
                wait = API_BACKOFF_BASE * (attempt + 1)
                safe_print('      Rate limited, waiting ' + str(wait) + 's...')
                time.sleep(wait)
                continue

            data = resp.json()
            vd = data.get('data', {})
            video_data = vd.get('video_data', {})
            if isinstance(video_data, dict) and video_data.get('video_list'):
                return video_data['video_list']
            for key, val in vd.items():
                if isinstance(val, dict):
                    inner = val.get('video_data', {})
                    if isinstance(inner, dict) and inner.get('video_list'):
                        return inner['video_list']
            return []
        except requests.exceptions.Timeout:
            time.sleep(10 * (attempt + 1))
        except Exception as e:
            safe_print('      Error: ' + str(e))
            time.sleep(5)
    return []


def fetch_video_urls(vids, api_template):
    url = api_template['base_url']
    headers = {}
    skip = {'accept-encoding', 'content-length', 'host', 'connection', 'content-encoding'}
    for k, v in api_template['headers'].items():
        if k.lower() not in skip:
            headers[k] = v

    body = {
        "biz_param": {
            "detail_page_version": 0, "device_level": 3,
            "need_all_video_definition": True, "need_mp4_align": False,
            "use_os_player": False, "use_server_dns": False, "video_platform": 1024
        },
        "video_id": ",".join(str(v) for v in vids)
    }

    for attempt in range(API_MAX_RETRIES):
        try:
            params = dict(api_template['params'])
            params['_rticket'] = str(int(time.time() * 1000))
            api_semaphore.acquire()
            try:
                resp = requests.post(url, params=params, headers=headers, json=body, timeout=30)
            finally:
                api_semaphore.release()

            if resp.status_code == 429 or resp.status_code >= 500:
                wait = min(API_BACKOFF_BASE * (2 ** attempt), 180)
                safe_print('      HTTP ' + str(resp.status_code) + ', cooldown ' + str(wait) + 's...')
                time.sleep(wait)
                continue

            data = resp.json()
            results = {}
            if isinstance(data.get('data'), dict):
                for vid_id, vinfo in data['data'].items():
                    if isinstance(vinfo, dict) and vinfo.get('main_url'):
                        results[vid_id] = vinfo['main_url']
                    elif isinstance(vinfo, dict) and vinfo.get('backup_url'):
                        results[vid_id] = vinfo['backup_url']
            return results
        except (requests.exceptions.Timeout, requests.exceptions.ConnectionError):
            wait = min(API_BACKOFF_BASE * (2 ** attempt), 180)
            time.sleep(wait)
        except Exception as e:
            safe_print('      Error: ' + str(e))
            time.sleep(5)
    return {}


def download_video(url, out_path):
    if out_path.exists() and out_path.stat().st_size > 10000:
        return True
    try:
        resp = requests.get(url, stream=True, timeout=60)
        resp.raise_for_status()
        out_path.parent.mkdir(parents=True, exist_ok=True)
        with open(out_path, 'wb') as f:
            for chunk in resp.iter_content(8192):
                f.write(chunk)
        return out_path.stat().st_size > 10000
    except:
        return False


def convert_to_hls(mp4_path, hls_dir):
    hls_dir.mkdir(parents=True, exist_ok=True)
    playlist = hls_dir / 'playlist.m3u8'
    if playlist.exists():
        return True
    cmd = [
        'ffmpeg', '-i', str(mp4_path),
        '-c', 'copy',
        '-hls_time', str(HLS_SEGMENT_DURATION),
        '-hls_list_size', '0',
        '-hls_segment_filename', str(hls_dir / 'seg_%03d.ts'),
        '-f', 'hls', str(playlist)
    ]
    try:
        subprocess.run(cmd, capture_output=True, timeout=120)
        return playlist.exists()
    except:
        return False


def get_r2_client():
    if not all([R2_ENDPOINT, R2_ACCESS_KEY_ID, R2_SECRET_ACCESS_KEY]):
        return None
    return boto3.client('s3', endpoint_url=R2_ENDPOINT,
                        aws_access_key_id=R2_ACCESS_KEY_ID,
                        aws_secret_access_key=R2_SECRET_ACCESS_KEY,
                        region_name='auto')


def upload_drama_to_r2(s3, drama_dir):
    slug = drama_dir.name
    r2_prefix = 'melolo/' + slug
    result = {'uploaded': 0, 'bytes': 0, 'errors': 0}
    for fpath in sorted(drama_dir.rglob('*')):
        if not fpath.is_file() or fpath.stat().st_size == 0:
            continue
        rel = fpath.relative_to(drama_dir)
        r2_key = r2_prefix + '/' + rel.as_posix()
        ct = CONTENT_TYPES.get(fpath.suffix.lower(), 'application/octet-stream')
        try:
            s3.upload_file(str(fpath), R2_BUCKET, r2_key, ExtraArgs={'ContentType': ct})
            result['uploaded'] += 1
            result['bytes'] += fpath.stat().st_size
        except Exception as e:
            result['errors'] += 1
    return result


# ─── Find empty dramas ───────────────────────────────────────────────────────
def find_empty_dramas():
    empty = []
    for dd in sorted(OUTPUT_DIR.iterdir()):
        if not dd.is_dir():
            continue
        meta_path = dd / 'metadata.json'
        if not meta_path.exists():
            continue
        ep_dir = dd / 'episodes'
        actual = 0
        if ep_dir.exists():
            for ef in ep_dir.iterdir():
                if ef.is_dir() and list(ef.glob('*.m3u8')):
                    actual += 1
        if actual == 0:
            with open(meta_path, 'r', encoding='utf-8') as f:
                meta = json.load(f)
            empty.append({
                'slug': dd.name,
                'series_id': meta.get('series_id', ''),
                'title': meta.get('title', dd.name),
                'total_episodes': meta.get('total_episodes', 0),
                'cover_url': meta.get('cover_url', ''),
                'description': meta.get('description', ''),
                'genres': meta.get('genres', []),
                'author': meta.get('author', ''),
            })
    return empty


# ─── Process a single drama ──────────────────────────────────────────────────
def process_drama(templates, drama_info, index, total, r2_client=None):
    slug = drama_info['slug']
    series_id = drama_info['series_id']
    title = drama_info['title']
    drama_dir = OUTPUT_DIR / slug

    safe_print('\n  [' + str(index) + '/' + str(total) + '] ' + title)
    safe_print('    Series ID: ' + series_id)

    if not series_id:
        safe_print('    SKIP: no series_id')
        return False

    # Fetch episode list
    safe_print('    Fetching episodes...')
    episodes = fetch_episode_list(templates, series_id)

    if not episodes:
        safe_print('    FAIL: no episodes returned from API')
        with stats_lock:
            stats['failed'] += 1
        return False

    safe_print('    Found ' + str(len(episodes)) + ' episodes')

    drama_dir.mkdir(parents=True, exist_ok=True)

    # Download cover
    cover_path = drama_dir / 'cover.jpg'
    if not cover_path.exists() or cover_path.stat().st_size < 1000:
        cover_url = drama_info.get('cover_url', '')
        if cover_url:
            try:
                resp = requests.get(cover_url, timeout=15)
                if resp.status_code == 200 and len(resp.content) > 1000:
                    with open(cover_path, 'wb') as f:
                        f.write(resp.content)
                    safe_print('    Cover downloaded')
            except:
                safe_print('    Cover download failed')

    # Get vid IDs
    vid_ids = [str(ep.get('vid', '')) for ep in episodes if ep.get('vid')]
    if not vid_ids:
        safe_print('    FAIL: no vid IDs')
        return False

    # Fetch video URLs in batches
    vm_tmpl = templates.get('video_model')
    if not vm_tmpl:
        safe_print('    FAIL: no video_model template')
        return False

    all_urls = {}
    total_batches = (len(vid_ids) + BATCH_SIZE - 1) // BATCH_SIZE
    for batch_start in range(0, len(vid_ids), BATCH_SIZE):
        batch = vid_ids[batch_start:batch_start + BATCH_SIZE]
        batch_num = batch_start // BATCH_SIZE + 1
        urls = fetch_video_urls(batch, vm_tmpl)
        all_urls.update(urls)
        safe_print('    Batch ' + str(batch_num) + '/' + str(total_batches) +
                   ': ' + str(len(urls)) + '/' + str(len(batch)) + ' URLs')
        time.sleep(API_DELAY)

    safe_print('    Total URLs: ' + str(len(all_urls)) + '/' + str(len(vid_ids)))

    # Download + convert each episode
    ep_entries = []
    successful = 0
    for ep_idx, ep in enumerate(episodes, 1):
        vid = str(ep.get('vid', ''))
        url = all_urls.get(vid, '')
        if not url:
            continue

        ep_num_str = str(ep_idx + 1).zfill(3)  # Start from ep 2 like rest of pipeline
        ep_dir = drama_dir / 'episodes' / ep_num_str
        mp4_path = DOWNLOAD_DIR / slug / ('ep' + ep_num_str + '.mp4')

        if (ep_dir / 'playlist.m3u8').exists():
            successful += 1
            ep_entries.append({'number': ep_idx + 1, 'path': 'episodes/' + ep_num_str + '/playlist.m3u8'})
            continue

        if download_video(url, mp4_path):
            if convert_to_hls(mp4_path, ep_dir):
                successful += 1
                ep_entries.append({'number': ep_idx + 1, 'path': 'episodes/' + ep_num_str + '/playlist.m3u8'})
                try:
                    mp4_path.unlink()
                except:
                    pass

    safe_print('    Episodes: ' + str(successful) + '/' + str(len(episodes)) + ' complete')

    # Update metadata
    metadata = {
        'source': 'melolo',
        'series_id': series_id,
        'title': title,
        'slug': slug,
        'author': drama_info.get('author', ''),
        'description': drama_info.get('description', ''),
        'genres': drama_info.get('genres', []),
        'total_episodes': len(episodes),
        'captured_episodes': successful,
        'cover': 'cover.jpg',
        'cover_url': drama_info.get('cover_url', ''),
        'episodes': ep_entries,
    }

    with open(drama_dir / 'metadata.json', 'w', encoding='utf-8') as f:
        json.dump(metadata, f, indent=2, ensure_ascii=False)

    # Upload to R2
    if r2_client and successful > 0:
        safe_print('    Uploading to R2...')
        r2_result = upload_drama_to_r2(r2_client, drama_dir)
        size_mb = r2_result['bytes'] / (1024 * 1024)
        safe_print('    R2: ' + str(r2_result['uploaded']) + ' files (' +
                   str(round(size_mb, 1)) + ' MB)')

    with stats_lock:
        if successful > 0:
            stats['completed'] += 1
        else:
            stats['failed'] += 1
        stats['episodes'] += successful

    return successful > 0


# ─── Main ────────────────────────────────────────────────────────────────────
def main():
    print('=' * 60)
    print('  RE-SCRAPE 40 EMPTY MELOLO DRAMAS')
    print('=' * 60)

    har_path = Path('melolo4.har')
    if not har_path.exists():
        print('ERROR: melolo4.har not found')
        sys.exit(1)

    print('\nLoading HAR auth...')
    templates = extract_auth(har_path)
    found = [k for k in ['video_detail', 'video_model'] if k in templates]
    print('  Templates: ' + ', '.join(found))

    if 'video_detail' not in templates or 'video_model' not in templates:
        print('ERROR: Missing required API templates in HAR')
        sys.exit(1)

    # Find empty dramas
    empty = find_empty_dramas()
    print('\n  Found ' + str(len(empty)) + ' empty dramas to re-scrape')

    # R2 client
    r2 = get_r2_client()
    if r2:
        print('  R2 client ready')
    else:
        print('  WARNING: No R2 client, will save locally only')

    upload_flag = '--upload' in sys.argv

    num_workers = 3
    if '--workers' in sys.argv:
        idx = sys.argv.index('--workers')
        if idx + 1 < len(sys.argv):
            num_workers = int(sys.argv[idx + 1])

    print('  Workers: ' + str(num_workers))
    print('\n  Starting re-scrape...\n')
    start_time = time.time()

    if num_workers <= 1:
        for i, drama in enumerate(empty, 1):
            process_drama(templates, drama, i, len(empty), r2 if upload_flag else None)
    else:
        def worker(args):
            idx, drama = args
            return process_drama(templates, drama, idx, len(empty), r2 if upload_flag else None)

        with ThreadPoolExecutor(max_workers=num_workers) as executor:
            futures = {executor.submit(worker, (i, d)): d for i, d in enumerate(empty, 1)}
            for future in as_completed(futures):
                try:
                    future.result()
                except Exception as e:
                    safe_print('  Worker error: ' + str(e))

    elapsed = time.time() - start_time
    print('\n' + '=' * 60)
    print('  RE-SCRAPE COMPLETE')
    print('=' * 60)
    print('  Completed: ' + str(stats['completed']))
    print('  Failed:    ' + str(stats['failed']))
    print('  Episodes:  ' + str(stats['episodes']))
    print('  Time:      ' + str(round(elapsed / 60, 1)) + ' min')
    print('=' * 60)


if __name__ == '__main__':
    main()
