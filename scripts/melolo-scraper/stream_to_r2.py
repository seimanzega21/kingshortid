#!/usr/bin/env python3
"""
STREAM-TO-R2: Direct MP4 upload without local storage
=====================================================
Downloads MP4 from Melolo CDN and streams directly to R2 via multipart upload.
Zero local disk usage. ~2x faster than HLS pipeline.
"""
import json, sys, io, os, time, re, threading, requests, boto3
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
BATCH_SIZE = 8
API_DELAY = 1.5
API_MAX_RETRIES = 3
API_BACKOFF_BASE = 30
CHUNK_SIZE = 8 * 1024 * 1024  # 8MB chunks for multipart upload

R2_ENDPOINT = os.getenv("R2_ENDPOINT", "")
R2_ACCESS_KEY_ID = os.getenv("R2_ACCESS_KEY_ID", "")
R2_SECRET_ACCESS_KEY = os.getenv("R2_SECRET_ACCESS_KEY", "")
R2_BUCKET = os.getenv("R2_BUCKET_NAME", "shortlovers")

api_semaphore = threading.Semaphore(6)
print_lock = threading.Lock()
stats_lock = threading.Lock()
stats = {'completed': 0, 'failed': 0, 'episodes': 0, 'bytes': 0}


def safe_print(*args, **kwargs):
    with print_lock:
        print(*args, **kwargs, flush=True)


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


# ─── Stream MP4 directly to R2 ──────────────────────────────────────────────
def stream_mp4_to_r2(s3, video_url, r2_key):
    """Stream MP4 from CDN directly to R2 via multipart upload. Zero local disk."""
    try:
        resp = requests.get(video_url, stream=True, timeout=120)
        resp.raise_for_status()

        content_length = int(resp.headers.get('content-length', 0))

        # For small files (<8MB), use simple put_object
        if content_length > 0 and content_length < CHUNK_SIZE:
            data = resp.content
            s3.put_object(Bucket=R2_BUCKET, Key=r2_key, Body=data,
                          ContentType='video/mp4')
            return len(data)

        # For larger files, use multipart upload
        mpu = s3.create_multipart_upload(Bucket=R2_BUCKET, Key=r2_key,
                                          ContentType='video/mp4')
        upload_id = mpu['UploadId']
        parts = []
        part_num = 1
        total_bytes = 0
        buffer = b''

        try:
            for chunk in resp.iter_content(CHUNK_SIZE):
                buffer += chunk
                if len(buffer) >= CHUNK_SIZE:
                    part = s3.upload_part(
                        Bucket=R2_BUCKET, Key=r2_key,
                        UploadId=upload_id, PartNumber=part_num,
                        Body=buffer
                    )
                    parts.append({'PartNumber': part_num, 'ETag': part['ETag']})
                    total_bytes += len(buffer)
                    buffer = b''
                    part_num += 1

            # Upload remaining buffer
            if buffer:
                # Multipart requires minimum 5MB parts except last
                # If only 1 part and it's small, abort and use put_object
                if part_num == 1 and len(buffer) < 5 * 1024 * 1024:
                    s3.abort_multipart_upload(Bucket=R2_BUCKET, Key=r2_key,
                                               UploadId=upload_id)
                    s3.put_object(Bucket=R2_BUCKET, Key=r2_key, Body=buffer,
                                  ContentType='video/mp4')
                    return len(buffer)
                else:
                    part = s3.upload_part(
                        Bucket=R2_BUCKET, Key=r2_key,
                        UploadId=upload_id, PartNumber=part_num,
                        Body=buffer
                    )
                    parts.append({'PartNumber': part_num, 'ETag': part['ETag']})
                    total_bytes += len(buffer)

            s3.complete_multipart_upload(
                Bucket=R2_BUCKET, Key=r2_key, UploadId=upload_id,
                MultipartUpload={'Parts': parts}
            )
            return total_bytes

        except Exception as e:
            s3.abort_multipart_upload(Bucket=R2_BUCKET, Key=r2_key,
                                       UploadId=upload_id)
            raise e

    except Exception as e:
        safe_print('      Stream error: ' + str(e))
        return 0


def upload_json_to_r2(s3, data, r2_key):
    body = json.dumps(data, indent=2, ensure_ascii=False).encode('utf-8')
    s3.put_object(Bucket=R2_BUCKET, Key=r2_key, Body=body,
                  ContentType='application/json')
    return len(body)


def upload_cover_to_r2(s3, cover_url, r2_key):
    """Download cover, convert HEIC→JPEG if needed, upload to R2."""
    import subprocess, tempfile
    try:
        resp = requests.get(cover_url, timeout=15)
        if resp.status_code != 200 or len(resp.content) < 1000:
            return 0
        data = resp.content

        # Check if HEIC (magic bytes 0x0000001C or 0x00000018)
        if data[:4] in (bytes([0x00, 0x00, 0x00, 0x1C]), bytes([0x00, 0x00, 0x00, 0x18])):
            # Convert HEIC→JPEG via ffmpeg
            with tempfile.NamedTemporaryFile(suffix='.heic', delete=False) as tmp_in:
                tmp_in.write(data)
                tmp_in_path = tmp_in.name
            tmp_out_path = tmp_in_path.replace('.heic', '.jpg')
            try:
                subprocess.run(['ffmpeg', '-i', tmp_in_path, '-y', tmp_out_path],
                              capture_output=True, timeout=30)
                data = open(tmp_out_path, 'rb').read()
            finally:
                for p in (tmp_in_path, tmp_out_path):
                    try: os.unlink(p)
                    except: pass

        # Verify it's a valid image (JPEG or PNG)
        if data[:3] != bytes([0xFF, 0xD8, 0xFF]) and data[:4] != bytes([0x89, 0x50, 0x4E, 0x47]):
            return 0

        s3.put_object(Bucket=R2_BUCKET, Key=r2_key, Body=data,
                      ContentType='image/jpeg')
        return len(data)
    except:
        pass
    return 0


def find_cover_in_api_response(data):
    """Deep search for cover image URL in video_detail API response."""
    def _search(obj, depth=0):
        if depth > 8: return None
        if isinstance(obj, dict):
            for k, v in obj.items():
                if k in ('cover', 'horizontal_cover', 'poster_url', 'vertical_cover'):
                    if isinstance(v, str) and 'http' in v:
                        return v
                result = _search(v, depth + 1)
                if result: return result
        elif isinstance(obj, list):
            for item in obj:
                result = _search(item, depth + 1)
                if result: return result
        return None
    return _search(data)


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
                if ef.is_dir() and (list(ef.glob('*.m3u8')) or list(ef.glob('*.mp4'))):
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


# ─── Check R2 for already-uploaded episodes ──────────────────────────────────
def get_r2_episode_count(s3, slug):
    """Check how many MP4 episodes already exist on R2 for this drama."""
    prefix = 'melolo/' + slug + '/episodes/'
    try:
        paginator = s3.get_paginator('list_objects_v2')
        count = 0
        for page in paginator.paginate(Bucket=R2_BUCKET, Prefix=prefix):
            for obj in page.get('Contents', []):
                if obj['Key'].endswith('.mp4'):
                    count += 1
        return count
    except:
        return 0


# ─── Process a single drama ──────────────────────────────────────────────────
def process_drama(templates, drama_info, index, total, s3):
    slug = drama_info['slug']
    series_id = drama_info['series_id']
    title = drama_info['title']

    safe_print('\n  [' + str(index) + '/' + str(total) + '] ' + title)
    safe_print('    Series ID: ' + series_id)

    if not series_id:
        safe_print('    SKIP: no series_id')
        return False

    # Check R2 for existing episodes
    existing = get_r2_episode_count(s3, slug)
    if existing > 0:
        safe_print('    SKIP: already has ' + str(existing) + ' episodes on R2')
        with stats_lock:
            stats['completed'] += 1
        return True

    # Fetch episode list from API
    safe_print('    Fetching episodes...')
    episodes = fetch_episode_list(templates, series_id)

    if not episodes:
        safe_print('    FAIL: no episodes from API')
        with stats_lock:
            stats['failed'] += 1
        return False

    safe_print('    Found ' + str(len(episodes)) + ' episodes')

    # Upload cover directly to R2
    cover_url = drama_info.get('cover_url', '')
    r2_prefix = 'melolo/' + slug

    # If no cover_url from metadata, try to extract from API response
    if not cover_url and episodes:
        api_cover = find_cover_in_api_response({'video_list': episodes})
        if api_cover:
            cover_url = api_cover
            safe_print('    Cover found in API response')

    if cover_url:
        cover_bytes = upload_cover_to_r2(s3, cover_url, r2_prefix + '/poster.jpg')
        if cover_bytes > 0:
            safe_print('    Cover → R2 (' + str(round(cover_bytes / 1024, 1)) + ' KB)')
        else:
            safe_print('    ⚠ Cover upload failed')

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
        safe_print('    URLs ' + str(batch_num) + '/' + str(total_batches) +
                   ': ' + str(len(urls)) + '/' + str(len(batch)))
        time.sleep(API_DELAY)

    safe_print('    Total URLs: ' + str(len(all_urls)) + '/' + str(len(vid_ids)))

    # Stream each episode's MP4 directly to R2
    ep_entries = []
    successful = 0
    drama_bytes = 0

    for ep_idx, ep in enumerate(episodes, 1):
        vid = str(ep.get('vid', ''))
        url = all_urls.get(vid, '')
        if not url:
            continue

        ep_num_str = str(ep_idx + 1).zfill(3)
        r2_key = r2_prefix + '/episodes/' + ep_num_str + '.mp4'

        nbytes = stream_mp4_to_r2(s3, url, r2_key)
        if nbytes > 0:
            successful += 1
            drama_bytes += nbytes
            ep_entries.append({
                'number': ep_idx + 1,
                'path': 'episodes/' + ep_num_str + '.mp4'
            })
        if successful % 20 == 0 and successful > 0:
            mb = drama_bytes / (1024 * 1024)
            safe_print('    Progress: ' + str(successful) + '/' + str(len(episodes)) +
                       ' eps (' + str(round(mb, 1)) + ' MB)')

    mb = drama_bytes / (1024 * 1024)
    safe_print('    Done: ' + str(successful) + '/' + str(len(episodes)) +
               ' eps (' + str(round(mb, 1)) + ' MB)')

    # Upload metadata to R2
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
        'format': 'mp4',
        'cover': 'poster.jpg',
        'cover_url': cover_url,
        'episodes': ep_entries,
    }
    upload_json_to_r2(s3, metadata, r2_prefix + '/metadata.json')

    # Also save metadata locally for reference
    local_dir = OUTPUT_DIR / slug
    local_dir.mkdir(parents=True, exist_ok=True)
    with open(local_dir / 'metadata.json', 'w', encoding='utf-8') as f:
        json.dump(metadata, f, indent=2, ensure_ascii=False)

    with stats_lock:
        if successful > 0:
            stats['completed'] += 1
        else:
            stats['failed'] += 1
        stats['episodes'] += successful
        stats['bytes'] += drama_bytes

    return successful > 0


# ─── Main ────────────────────────────────────────────────────────────────────
def main():
    print('=' * 60)
    print('  STREAM-TO-R2: Direct MP4 Upload')
    print('  Zero local disk • Maximum speed')
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
        print('ERROR: Missing required API templates')
        sys.exit(1)

    # R2 client
    if not all([R2_ENDPOINT, R2_ACCESS_KEY_ID, R2_SECRET_ACCESS_KEY]):
        print('ERROR: R2 credentials not configured in .env')
        sys.exit(1)

    s3 = boto3.client('s3', endpoint_url=R2_ENDPOINT,
                      aws_access_key_id=R2_ACCESS_KEY_ID,
                      aws_secret_access_key=R2_SECRET_ACCESS_KEY,
                      region_name='auto')
    print('  R2 connected')

    # Find empty dramas
    empty = find_empty_dramas()
    print('\n  Found ' + str(len(empty)) + ' empty dramas to stream')

    num_workers = 6
    if '--workers' in sys.argv:
        idx = sys.argv.index('--workers')
        if idx + 1 < len(sys.argv):
            num_workers = int(sys.argv[idx + 1])

    print('  Workers: ' + str(num_workers))
    print('\n  Starting stream-to-R2...\n')
    start_time = time.time()

    if num_workers <= 1:
        for i, drama in enumerate(empty, 1):
            process_drama(templates, drama, i, len(empty), s3)
    else:
        def worker(args):
            idx, drama = args
            # Each worker gets its own S3 client for thread safety
            s3_w = boto3.client('s3', endpoint_url=R2_ENDPOINT,
                                aws_access_key_id=R2_ACCESS_KEY_ID,
                                aws_secret_access_key=R2_SECRET_ACCESS_KEY,
                                region_name='auto')
            return process_drama(templates, drama, idx, len(empty), s3_w)

        with ThreadPoolExecutor(max_workers=num_workers) as executor:
            futures = {executor.submit(worker, (i, d)): d for i, d in enumerate(empty, 1)}
            for future in as_completed(futures):
                try:
                    future.result()
                except Exception as e:
                    safe_print('  Worker error: ' + str(e))

    elapsed = time.time() - start_time
    gb = stats['bytes'] / (1024 ** 3)
    print('\n' + '=' * 60)
    print('  STREAM-TO-R2 COMPLETE')
    print('=' * 60)
    print('  Completed: ' + str(stats['completed']))
    print('  Failed:    ' + str(stats['failed']))
    print('  Episodes:  ' + str(stats['episodes']))
    print('  Data:      ' + str(round(gb, 2)) + ' GB')
    print('  Time:      ' + str(round(elapsed / 60, 1)) + ' min')
    print('  Speed:     ' + str(round(gb / (elapsed / 3600), 2)) + ' GB/hr')
    print('=' * 60)


if __name__ == '__main__':
    main()
