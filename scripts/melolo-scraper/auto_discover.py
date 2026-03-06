#!/usr/bin/env python3
"""
MELOLO AUTO-DISCOVERY SCRAPER
==============================
Discovers ALL dramas on the Melolo platform automatically, without needing 
to manually browse them in the app. Uses the bookmall/cell/change API to 
paginate through the catalog, then fetches episode lists and video URLs.

Strategy:
  1. Extract API auth from HAR (headers, cookies, device params)
  2. Call bookmall/cell/change/v1/ in a loop (offset pagination) to discover dramas
  3. For each discovered drama, call video_detail/v1/ to get episode vid list
  4. For each batch of vids, call multi_video_model/v1/ to get MP4 URLs
  5. Download + convert to HLS (reuse auto_scraper logic)

Usage:
    python auto_discover.py melolo4.har             # Discover + scrape ALL
    python auto_discover.py melolo4.har --discover   # Discovery only (list dramas)
    python auto_discover.py melolo4.har --max 10     # First 10 new dramas only
    python auto_discover.py melolo4.har --upload     # Scrape + upload to R2
"""

import json
import sys
import io
import os
import re
import time
import subprocess
import threading
from concurrent.futures import ThreadPoolExecutor, as_completed
import shutil
import requests
import boto3
from pathlib import Path
from urllib.parse import urlparse, parse_qs, urlencode
from dotenv import load_dotenv

load_dotenv(Path(__file__).parent / '.env')

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')

# ─── Config ───────────────────────────────────────────────────────────────────
SCRIPT_DIR = Path(__file__).parent
OUTPUT_DIR = SCRIPT_DIR / "r2_ready" / "melolo"
DOWNLOAD_DIR = SCRIPT_DIR / "downloads"
HLS_SEGMENT_DURATION = 6
BATCH_SIZE = 8
API_DELAY = 2.0
DISCOVERY_DELAY = 1.5  # seconds between paginated discover calls
MAX_DISCOVER_PAGES = 100  # safety limit
API_MAX_RETRIES = 3
API_BACKOFF_BASE = 30

# R2 Config
R2_ENDPOINT = os.getenv("R2_ENDPOINT", "")
R2_ACCESS_KEY_ID = os.getenv("R2_ACCESS_KEY_ID", "")
R2_SECRET_ACCESS_KEY = os.getenv("R2_SECRET_ACCESS_KEY", "")
R2_BUCKET = os.getenv("R2_BUCKET_NAME", "shortlovers")
R2_PUBLIC_URL = os.getenv("R2_PUBLIC_URL", "https://stream.shortlovers.id")

CONTENT_TYPES = {
    '.jpg': 'image/jpeg', '.jpeg': 'image/jpeg', '.png': 'image/png',
    '.json': 'application/json', '.m3u8': 'application/vnd.apple.mpegurl',
    '.ts': 'video/mp2t', '.mp4': 'video/mp4',
}

# Thread-safe API rate limiter (shared across workers)
api_semaphore = threading.Semaphore(3)  # max 3 concurrent API calls
print_lock = threading.Lock()

def safe_print(*args, **kwargs):
    with print_lock:
        print(*args, **kwargs, flush=True)


def slugify(text: str) -> str:
    text = text.lower().strip()
    text = re.sub(r'[^\w\s-]', '', text)
    text = re.sub(r'[\s_]+', '-', text)
    text = re.sub(r'-+', '-', text)
    return text[:60].rstrip('-')


# ─── Phase 1: Extract auth templates from HAR ────────────────────────────────

def extract_auth_from_har(har_path: Path) -> dict:
    """Extract all API request templates from HAR file"""
    print(f"\n{'='*60}")
    print(f"  PHASE 1: EXTRACTING AUTH FROM HAR")
    print(f"{'='*60}\n")

    with open(har_path, 'r', encoding='utf-8') as f:
        har = json.load(f)

    entries = har['log']['entries']
    templates = {}

    for entry in entries:
        url = entry['request']['url']
        req = entry['request']
        parsed = urlparse(url)
        headers = {h['name']: h['value'] for h in req['headers']}
        params = {k: v[0] for k, v in parse_qs(parsed.query).items()}

        # bookmall/cell/change template
        if 'bookmall/cell/change/v1/' in url and 'cell_change' not in templates:
            templates['cell_change'] = {
                'base_url': f"{parsed.scheme}://{parsed.netloc}{parsed.path}",
                'headers': headers,
                'params': params,
                'method': req['method'],
            }

        # bookmall/tab template (to get initial cell_id)
        if 'bookmall/tab/v1/' in url and 'tab' not in templates:
            templates['tab'] = {
                'base_url': f"{parsed.scheme}://{parsed.netloc}{parsed.path}",
                'headers': headers,
                'params': params,
                'method': req['method'],
            }

        # video_detail template
        if 'video_detail/v1/' in url and 'multi' not in url and 'video_detail' not in templates:
            body = {}
            if 'postData' in req:
                try:
                    body = json.loads(req['postData'].get('text', '{}'))
                except:
                    pass
            templates['video_detail'] = {
                'base_url': f"{parsed.scheme}://{parsed.netloc}{parsed.path}",
                'headers': headers,
                'params': params,
                'method': 'POST',
                'body_template': body,
            }

        # multi_video_model template (reuse from auto_scraper)
        if 'multi_video_model' in url and 'video_model' not in templates:
            templates['video_model'] = {
                'base_url': url.split('?')[0],
                'headers': {h['name'].lower(): h['value'] for h in req['headers']},
                'params': params,
            }

    # Also extract book metadata from HAR responses
    book_meta = {}
    for entry in entries:
        mime = entry['response']['content'].get('mimeType', '')
        if 'json' not in mime:
            continue
        text = entry['response']['content'].get('text', '')
        if not text:
            continue
        try:
            data = json.loads(text)
        except:
            continue

        def _extract(obj, depth=0):
            if depth > 6 or not isinstance(obj, (dict, list)):
                return
            if isinstance(obj, dict):
                bid = str(obj.get('book_id', ''))
                bname = obj.get('book_name', '')
                if bid and bname and len(bid) > 10:
                    if bid not in book_meta or (bname and not book_meta[bid].get('title')):
                        cats = []
                        ci = obj.get('category_info', '')
                        if isinstance(ci, str) and ci.startswith('['):
                            try:
                                cats = [c.get('Name', '') for c in json.loads(ci) if c.get('Name')]
                            except:
                                pass
                        book_meta[bid] = {
                            'title': bname,
                            'abstract': obj.get('abstract', ''),
                            'author': obj.get('author', ''),
                            'thumb_url': obj.get('thumb_url', ''),
                            'serial_count': obj.get('serial_count', obj.get('last_chapter_index', '')),
                            'categories': cats,
                            'language': obj.get('language', ''),
                        }
                for v in obj.values():
                    _extract(v, depth + 1)
            elif isinstance(obj, list):
                for item in obj[:200]:
                    _extract(item, depth + 1)

        _extract(data)

    found = [k for k in ['cell_change', 'tab', 'video_detail', 'video_model'] if k in templates]
    print(f"  Extracted templates: {', '.join(found)}")
    print(f"  Book metadata from HAR: {len(book_meta)} titles")

    return {'templates': templates, 'book_meta': book_meta}


# ─── Phase 2: Discover dramas via bookmall pagination ────────────────────────

def discover_dramas(auth: dict, existing_ids: set = None) -> list:
    """Paginate through bookmall/cell/change to discover ALL dramas"""
    print(f"\n{'='*60}")
    print(f"  PHASE 2: DISCOVERING DRAMAS VIA BOOKMALL")
    print(f"{'='*60}\n")

    if existing_ids is None:
        existing_ids = set()

    templates = auth['templates']
    
    # First try to get cell_id from tab endpoint
    cell_id = None
    if 'cell_change' in templates:
        cell_id = templates['cell_change']['params'].get('cell_id', '')
    
    if not cell_id and 'tab' in templates:
        # Fetch tab to get cell_id
        t = templates['tab']
        try:
            resp = requests.get(t['base_url'], params=t['params'], headers=t['headers'], timeout=15)
            data = resp.json()
            tabs = data.get('data', {}).get('book_tab_infos', [])
            for tab in tabs:
                for cell in tab.get('cells', []):
                    cid = cell.get('id', cell.get('cid', cell.get('cell_id', '')))
                    if cid:
                        cell_id = str(cid)
                        break
        except Exception as e:
            print(f"  ⚠ Tab fetch failed: {e}")
    
    if not cell_id:
        # Fallback: use cell_id from HAR params
        cell_id = '7450059162446200848'
        print(f"  Using fallback cell_id: {cell_id}")
    else:
        print(f"  Using cell_id: {cell_id}")

    # Paginate through cell/change
    discovered = {}  # book_id -> metadata
    offset = 0
    page = 0
    
    # Merge book_meta from HAR first
    for bid, meta in auth.get('book_meta', {}).items():
        discovered[bid] = meta

    print(f"  Pre-loaded {len(discovered)} dramas from HAR metadata")
    print(f"  Now discovering via API pagination...\n")

    if 'cell_change' not in templates:
        print("  ⚠ No cell_change template in HAR. Using HAR metadata only.")
        return list(discovered.items())

    t = templates['cell_change']
    
    while page < MAX_DISCOVER_PAGES:
        page += 1
        params = dict(t['params'])
        params['cell_id'] = cell_id
        params['offset'] = str(offset)
        params['_rticket'] = str(int(time.time() * 1000))

        try:
            resp = requests.get(
                t['base_url'], 
                params=params,
                headers=t['headers'],
                timeout=15
            )
            
            if resp.status_code == 429:
                print(f"  ⚠ Rate limited! Waiting 60s...")
                time.sleep(60)
                continue
            
            data = resp.json()
            cell_data = data.get('data', {})
            cell = cell_data.get('cell', {})
            has_more = cell_data.get('has_more', False)
            next_offset = cell_data.get('next_offset', offset + 18)

            # Extract books from cell
            books = cell.get('books', [])
            if not books:
                # Try cell_data inside cell
                cd = cell.get('cell_data', [])
                if isinstance(cd, list):
                    for item in cd:
                        if isinstance(item, dict):
                            bks = item.get('books', [])
                            if isinstance(bks, list):
                                books.extend(bks)

            new_in_page = 0
            for book in books:
                if not isinstance(book, dict):
                    continue
                bid = str(book.get('book_id', ''))
                if not bid or len(bid) < 10:
                    continue
                if bid not in discovered:
                    new_in_page += 1
                    cats = []
                    ci = book.get('category_info', '')
                    if isinstance(ci, str) and ci.startswith('['):
                        try:
                            cats = [c.get('Name', '') for c in json.loads(ci) if c.get('Name')]
                        except:
                            pass
                    discovered[bid] = {
                        'title': book.get('book_name', ''),
                        'abstract': book.get('abstract', ''),
                        'author': book.get('author', ''),
                        'thumb_url': book.get('thumb_url', ''),
                        'serial_count': book.get('serial_count', book.get('last_chapter_index', '')),
                        'categories': cats,
                        'language': book.get('language', ''),
                    }

            status = "✓" if new_in_page > 0 else "·"
            print(f"  Page {page:3d} | offset={offset:4d} | {len(books):2d} books | {new_in_page} new | Total: {len(discovered)} | {status}")

            if not has_more:
                print(f"\n  ✅ Reached end of catalog!")
                break
            
            offset = next_offset
            time.sleep(DISCOVERY_DELAY)

        except requests.exceptions.Timeout:
            print(f"  ⚠ Timeout on page {page}, retrying...")
            time.sleep(10)
            continue
        except Exception as e:
            print(f"  ✗ Error on page {page}: {e}")
            time.sleep(5)
            continue

    # Filter out existing
    new_dramas = {bid: meta for bid, meta in discovered.items() if bid not in existing_ids}
    
    print(f"\n  📊 Discovery Summary:")
    print(f"     Total discovered: {len(discovered)}")
    print(f"     Already scraped:  {len(existing_ids)}")
    print(f"     New dramas:       {len(new_dramas)}")

    return list(discovered.items())


# ─── Phase 3: Get episode lists via video_detail ─────────────────────────────

def fetch_episode_list(auth: dict, series_id: str) -> list:
    """Fetch episode vid list for a series via video_detail/v1/"""
    t = auth['templates'].get('video_detail')
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
                resp = requests.post(
                    t['base_url'],
                    params=params,
                    headers=t['headers'],
                    json=body,
                    timeout=20
                )
            finally:
                api_semaphore.release()
            
            if resp.status_code == 429:
                wait = API_BACKOFF_BASE * (attempt + 1)
                print(f"      ⚠ Rate limited, waiting {wait}s...")
                time.sleep(wait)
                continue
            
            data = resp.json()
            
            # Extract video_list - can be nested under series_id key or directly
            vd = data.get('data', {})
            
            # Try direct video_data
            video_data = vd.get('video_data', {})
            if isinstance(video_data, dict) and video_data.get('video_list'):
                return video_data['video_list']
            
            # Try nested under series_id key
            for key, val in vd.items():
                if isinstance(val, dict):
                    inner_vd = val.get('video_data', {})
                    if isinstance(inner_vd, dict) and inner_vd.get('video_list'):
                        return inner_vd['video_list']
            
            return []
            
        except requests.exceptions.Timeout:
            print(f"      ⚠ Timeout (attempt {attempt+1}/{API_MAX_RETRIES})")
            time.sleep(10 * (attempt + 1))
        except Exception as e:
            print(f"      ✗ Error: {e}")
            time.sleep(5)
    
    return []


# ─── Phase 4: Fetch video URLs (reused from auto_scraper) ────────────────────

def fetch_video_urls(vids: list, api_template: dict) -> dict:
    """Fetch MP4 URLs for a batch of vids via multi_video_model POST API"""
    url = api_template['base_url']
    
    # Headers (skip transport-level headers)
    headers = {}
    skip = {'accept-encoding', 'content-length', 'host', 'connection', 'content-encoding'}
    for k, v in api_template['headers'].items():
        if k.lower() not in skip:
            headers[k] = v

    # POST body with video_id (comma-separated)
    body = {
        "biz_param": {
            "detail_page_version": 0,
            "device_level": 3,
            "need_all_video_definition": True,
            "need_mp4_align": False,
            "use_os_player": False,
            "use_server_dns": False,
            "video_platform": 1024
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
                wait = API_BACKOFF_BASE * (2 ** attempt)
                wait = min(wait, 180)
                print(f"      ⚠ HTTP {resp.status_code}, cooldown {wait}s...", flush=True)
                time.sleep(wait)
                continue

            data = resp.json()
            results = {}
            
            # Response structure: data.{vid_id}.main_url
            if isinstance(data.get('data'), dict):
                for vid_id, vinfo in data['data'].items():
                    if isinstance(vinfo, dict) and vinfo.get('main_url'):
                        results[vid_id] = vinfo['main_url']
                    elif isinstance(vinfo, dict) and vinfo.get('backup_url'):
                        results[vid_id] = vinfo['backup_url']

            return results

        except (requests.exceptions.Timeout, requests.exceptions.ConnectionError):
            wait = API_BACKOFF_BASE * (2 ** attempt)
            print(f"      ⚠ Timeout, cooldown {wait}s...", flush=True)
            time.sleep(min(wait, 180))
        except Exception as e:
            print(f"      ✗ Error: {e}", flush=True)
            time.sleep(5)

    return {}


# ─── Phase 5: Download + HLS convert ────────────────────────────────────────

def download_video(url: str, out_path: Path) -> bool:
    """Download MP4 video"""
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
    except Exception as e:
        print(f"        DL error: {e}")
        return False


def convert_to_hls(mp4_path: Path, hls_dir: Path) -> bool:
    """Convert MP4 to HLS segments"""
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
        '-f', 'hls',
        str(playlist)
    ]
    
    try:
        result = subprocess.run(cmd, capture_output=True, timeout=120)
        return playlist.exists()
    except:
        return False


# ─── Phase R2: Upload to R2 ──────────────────────────────────────────────────

def get_r2_client():
    """Create R2 S3 client"""
    if not all([R2_ENDPOINT, R2_ACCESS_KEY_ID, R2_SECRET_ACCESS_KEY]):
        return None
    return boto3.client(
        's3', endpoint_url=R2_ENDPOINT,
        aws_access_key_id=R2_ACCESS_KEY_ID,
        aws_secret_access_key=R2_SECRET_ACCESS_KEY,
        region_name='auto'
    )


def upload_drama_to_r2(s3, drama_dir: Path) -> dict:
    """Upload a complete drama folder to R2"""
    slug = drama_dir.name
    r2_prefix = f"melolo/{slug}"
    result = {'uploaded': 0, 'bytes': 0, 'errors': 0}
    
    for fpath in sorted(drama_dir.rglob('*')):
        if not fpath.is_file() or fpath.stat().st_size == 0:
            continue
        rel = fpath.relative_to(drama_dir)
        r2_key = f"{r2_prefix}/{rel.as_posix()}"
        ct = CONTENT_TYPES.get(fpath.suffix.lower(), 'application/octet-stream')
        try:
            s3.upload_file(str(fpath), R2_BUCKET, r2_key, ExtraArgs={'ContentType': ct})
            result['uploaded'] += 1
            result['bytes'] += fpath.stat().st_size
        except Exception as e:
            result['errors'] += 1
    return result


# ─── Phase 6: Process all discovered dramas ──────────────────────────────────

def get_existing_series_ids() -> set:
    """Get series IDs of already-scraped dramas"""
    ids = set()
    if OUTPUT_DIR.exists():
        for drama_dir in OUTPUT_DIR.iterdir():
            if not drama_dir.is_dir():
                continue
            meta_file = drama_dir / 'metadata.json'
            if meta_file.exists():
                try:
                    with open(meta_file, 'r', encoding='utf-8') as f:
                        meta = json.load(f)
                    sid = meta.get('series_id', '')
                    if sid:
                        ids.add(sid)
                except:
                    pass
    return ids


def process_drama(auth: dict, book_id: str, meta: dict, drama_num: int, total: int, r2_client=None):
    """Process a single drama: episodes → video URLs → download → HLS"""
    title = meta.get('title', f'Drama {book_id[-8:]}')
    slug = slugify(title) if title else f'drama-{book_id[-8:]}'
    drama_dir = OUTPUT_DIR / slug

    print(f"\n  [{drama_num}/{total}] {title}")
    print(f"    Series ID: {book_id}")
    print(f"    Episodes:  ~{meta.get('serial_count', '?')}")

    # Skip if already fully scraped
    if drama_dir.exists():
        meta_file = drama_dir / 'metadata.json'
        if meta_file.exists():
            try:
                existing = json.load(open(meta_file, 'r', encoding='utf-8'))
                if existing.get('scrape_complete'):
                    print(f"    ✓ Already complete, skipping")
                    return
            except:
                pass

    # Step 1: Get episode list via video_detail
    print(f"    Fetching episode list...")
    episodes = fetch_episode_list(auth, book_id)
    
    if not episodes:
        print(f"    ✗ No episodes found! Skipping.")
        return
    
    print(f"    Found {len(episodes)} episodes")

    # Create output directory
    drama_dir.mkdir(parents=True, exist_ok=True)

    # Save/download cover
    cover_path = drama_dir / 'cover.jpg'
    if not cover_path.exists() and meta.get('thumb_url'):
        try:
            cover_url = meta['thumb_url']
            # Convert heic URL to jpg
            if 'tplv-resize' in cover_url:
                cover_url = cover_url.split('~')[0] + '~tplv-resize:570:810.jpg'
            resp = requests.get(cover_url, timeout=15)
            if resp.status_code == 200 and len(resp.content) > 1000:
                with open(cover_path, 'wb') as f:
                    f.write(resp.content)
                print(f"    ✓ Cover downloaded")
        except Exception as e:
            print(f"    ⚠ Cover download failed: {e}")

    # Step 2: Get vid IDs from episodes
    vid_ids = []
    for ep in episodes:
        vid = ep.get('vid', '')
        if vid:
            vid_ids.append(str(vid))

    if not vid_ids:
        print(f"    ✗ No vid IDs in episode list!")
        return

    # Step 3: Fetch video URLs in batches
    video_model_tmpl = auth['templates'].get('video_model')
    if not video_model_tmpl:
        print(f"    ✗ No video_model template!")
        return

    all_urls = {}
    for batch_start in range(0, len(vid_ids), BATCH_SIZE):
        batch = vid_ids[batch_start:batch_start + BATCH_SIZE]
        batch_num = batch_start // BATCH_SIZE + 1
        total_batches = (len(vid_ids) + BATCH_SIZE - 1) // BATCH_SIZE

        urls = fetch_video_urls(batch, video_model_tmpl)
        all_urls.update(urls)
        
        print(f"    Batch {batch_num}/{total_batches}: {len(urls)}/{len(batch)} URLs")
        time.sleep(API_DELAY)

    print(f"    Total URLs: {len(all_urls)}/{len(vid_ids)}")

    # Step 4: Download + convert each episode
    successful = 0
    for ep_idx, ep in enumerate(episodes, 1):
        vid = str(ep.get('vid', ''))
        url = all_urls.get(vid, '')
        if not url:
            continue

        ep_dir = drama_dir / f"ep{ep_idx:03d}"
        mp4_path = DOWNLOAD_DIR / slug / f"ep{ep_idx:03d}.mp4"

        # Check if already converted
        if (ep_dir / 'playlist.m3u8').exists():
            successful += 1
            continue

        # Download
        if download_video(url, mp4_path):
            # Convert to HLS
            if convert_to_hls(mp4_path, ep_dir):
                successful += 1
                # Clean up MP4
                try:
                    mp4_path.unlink()
                except:
                    pass

    print(f"    ✓ Episodes: {successful}/{len(episodes)} complete")

    # Save metadata
    metadata = {
        'source': 'melolo',
        'series_id': book_id,
        'title': title,
        'slug': slug,
        'author': meta.get('author', ''),
        'description': meta.get('abstract', ''),
        'categories': meta.get('categories', []),
        'language': meta.get('language', 'id'),
        'cover_url': meta.get('thumb_url', ''),
        'total_episodes': len(episodes),
        'episodes_scraped': successful,
        'scrape_complete': successful == len(episodes),
        'discovered_via': 'auto_discover',
        'scraped_at': time.strftime('%Y-%m-%dT%H:%M:%S'),
    }

    with open(drama_dir / 'metadata.json', 'w', encoding='utf-8') as f:
        json.dump(metadata, f, indent=2, ensure_ascii=False)

    # Upload to R2 if client available
    if r2_client and successful > 0:
        print(f"    📤 Uploading to R2...")
        r2_result = upload_drama_to_r2(r2_client, drama_dir)
        size_mb = r2_result['bytes'] / (1024 * 1024)
        print(f"    ✅ R2: {r2_result['uploaded']} files ({size_mb:.1f} MB)")
        if r2_result['errors']:
            print(f"    ⚠ R2 errors: {r2_result['errors']}")


# ─── Main ────────────────────────────────────────────────────────────────────

def main():
    if len(sys.argv) < 2:
        print("Usage: python auto_discover.py <har_file> [--discover] [--max N] [--workers N] [--upload]")
        sys.exit(1)

    har_path = Path(sys.argv[1])
    if not har_path.exists():
        print(f"HAR file not found: {har_path}")
        sys.exit(1)

    discover_only = '--discover' in sys.argv
    upload_to_r2 = '--upload' in sys.argv
    max_dramas = 0
    num_workers = 1
    if '--max' in sys.argv:
        idx = sys.argv.index('--max')
        if idx + 1 < len(sys.argv):
            max_dramas = int(sys.argv[idx + 1])
    if '--workers' in sys.argv:
        idx = sys.argv.index('--workers')
        if idx + 1 < len(sys.argv):
            num_workers = int(sys.argv[idx + 1])

    # Phase 1: Extract auth
    auth = extract_auth_from_har(har_path)
    
    # Get existing scraped series
    existing_ids = get_existing_series_ids()
    print(f"\n  Already scraped: {len(existing_ids)} dramas")

    # Phase 2: Discover
    all_dramas = discover_dramas(auth, existing_ids)

    # Filter to only new dramas (not yet scraped)
    new_dramas = [(bid, meta) for bid, meta in all_dramas if bid not in existing_ids]
    
    # Sort by episode count (highest first)
    def ep_count(item):
        try:
            return int(item[1].get('serial_count', 0))
        except (ValueError, TypeError):
            return 0
    new_dramas.sort(key=ep_count, reverse=True)

    print(f"\n{'='*60}")
    print(f"  DISCOVERED DRAMAS ({len(new_dramas)} new)")
    print(f"{'='*60}\n")

    for i, (bid, meta) in enumerate(new_dramas[:50], 1):
        eps = meta.get('serial_count', '?')
        title = meta.get('title', 'Unknown')
        cats = ', '.join(meta.get('categories', [])[:3])
        print(f"  {i:3d}. {title} ({eps} eps) [{cats}]")
        print(f"       ID: {bid}")

    if len(new_dramas) > 50:
        print(f"\n  ... and {len(new_dramas) - 50} more")

    if discover_only:
        print(f"\n  Discovery complete! Run without --discover to scrape.")
        return

    if not new_dramas:
        print(f"\n  ✅ All discovered dramas are already scraped!")
        return

    # Phase 3-6: Process each new drama
    if max_dramas > 0:
        new_dramas = new_dramas[:max_dramas]

    # Setup R2 client if uploading
    r2_client = None
    if upload_to_r2:
        print(f"\n  📤 R2 upload enabled")
        r2_client = get_r2_client()
        if r2_client:
            try:
                r2_client.head_bucket(Bucket=R2_BUCKET)
                print(f"  ✅ R2 connected: {R2_BUCKET}")
            except Exception as e:
                print(f"  ⚠ R2 connection failed: {e}")
                print(f"  Continuing without R2 upload...")
                r2_client = None
        else:
            print(f"  ⚠ R2 credentials missing, continuing without upload")

    print(f"\n{'='*60}")
    print(f"  PHASE 3-6: SCRAPING {len(new_dramas)} NEW DRAMAS ({num_workers} workers)")
    print(f"{'='*60}")

    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    DOWNLOAD_DIR.mkdir(parents=True, exist_ok=True)

    completed = 0
    failed = 0

    if num_workers <= 1:
        # Sequential mode
        for i, (bid, meta) in enumerate(new_dramas, 1):
            process_drama(auth, bid, meta, i, len(new_dramas), r2_client=r2_client)
            completed += 1
            time.sleep(1)
    else:
        # Parallel mode
        def worker(args):
            i, bid, meta = args
            try:
                process_drama(auth, bid, meta, i, len(new_dramas), r2_client=r2_client)
                return True
            except Exception as e:
                safe_print(f"    ✗ Worker error on {meta.get('title','?')}: {e}")
                return False

        work_items = [(i, bid, meta) for i, (bid, meta) in enumerate(new_dramas, 1)]

        with ThreadPoolExecutor(max_workers=num_workers) as executor:
            futures = {executor.submit(worker, item): item for item in work_items}
            for future in as_completed(futures):
                if future.result():
                    completed += 1
                else:
                    failed += 1
                safe_print(f"\n  📊 Progress: {completed + failed}/{len(new_dramas)} ({completed} ok, {failed} fail)")

    print(f"\n{'='*60}")
    print(f"  ✅ AUTO-DISCOVERY COMPLETE!")
    print(f"  Processed {completed}/{len(new_dramas)} dramas ({failed} failed)")
    if r2_client:
        print(f"  📤 All uploaded to R2: {R2_PUBLIC_URL}/melolo/")
    print(f"{'='*60}")


if __name__ == '__main__':
    main()
