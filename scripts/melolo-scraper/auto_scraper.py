#!/usr/bin/env python3
"""
MELOLO AUTO-SCRAPER
===================
Automatically fetches ALL episode video URLs by replaying the Melolo API
using captured headers from HAR file. Then downloads MP4s and converts 
to HLS segments.

Flow:
  1. Extract series & vid lists from HAR (video_detail)
  2. For each series, fetch all episode MP4 URLs via API (video_model)
  3. Download MP4s → convert to HLS segments → organize r2_ready

Usage:
    python auto_scraper.py melolo1.har        # All dramas
    python auto_scraper.py melolo1.har 5      # First 5 dramas only
"""

import json
import sys
import io
import os
import re
import time
import subprocess
from pathlib import Path
from urllib.parse import urlparse
from collections import defaultdict

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')

try:
    import requests
except ImportError:
    subprocess.run([sys.executable, '-m', 'pip', 'install', 'requests'], check=True)
    import requests


SCRIPT_DIR = Path(__file__).parent
OUTPUT_DIR = SCRIPT_DIR / "r2_ready" / "melolo"
DOWNLOAD_DIR = SCRIPT_DIR / "downloads"
HLS_SEGMENT_DURATION = 6
BATCH_SIZE = 8  # vids per API call (as used by the app)
API_DELAY = 1.5  # seconds between API calls (base)
API_MAX_RETRIES = 3  # retries per batch on failure
API_BACKOFF_BASE = 30  # initial cooldown seconds on rate limit
API_BACKOFF_MAX = 180  # max cooldown seconds
API_CONSECUTIVE_FAIL_THRESHOLD = 3  # consecutive fails before big cooldown


def slugify(text: str) -> str:
    text = text.lower().strip()
    text = re.sub(r'[^\w\s-]', '', text)
    text = re.sub(r'[\s_]+', '-', text)
    text = re.sub(r'-+', '-', text)
    return text[:60].rstrip('-')


def extract_replay_data(har_path: Path) -> dict:
    """Extract API headers, params, and all series data from HAR"""
    print(f"\n{'='*60}")
    print(f"  STEP 1: EXTRACTING REPLAY DATA FROM HAR")
    print(f"{'='*60}\n")

    with open(har_path, 'r', encoding='utf-8') as f:
        har = json.load(f)

    entries = har['log']['entries']
    
    # 1. Extract video_model request template (headers + params)
    api_template = None
    for entry in entries:
        url = entry['request']['url']
        if 'multi_video_model' not in url:
            continue
        req = entry['request']
        parsed = urlparse(url)
        from urllib.parse import parse_qs
        params = {k: v[0] for k, v in parse_qs(parsed.query).items()}
        
        headers = {}
        for h in req['headers']:
            headers[h['name'].lower()] = h['value']
        
        api_template = {
            'base_url': url.split('?')[0],
            'headers': headers,
            'params': params,
        }
        break

    if not api_template:
        print("ERROR: No video_model request found in HAR!")
        sys.exit(1)

    print(f"API template extracted: {api_template['base_url']}")

    # 2. Build book metadata from ALL JSON endpoints (bookmall, bookshelf, book_history, etc.)
    #    These contain the REAL titles and descriptions. book_id = series_id.
    book_meta = {}  # book_id -> {title, abstract, categories, author}
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

        def _extract_books(obj, depth=0):
            if depth > 6 or not isinstance(obj, (dict, list)):
                return
            if isinstance(obj, dict):
                bid = str(obj.get('book_id', ''))
                bname = obj.get('book_name', '')
                abstract = obj.get('abstract', '')
                if bid and bname and len(bid) > 10:
                    if bid not in book_meta or len(abstract) > len(book_meta[bid].get('abstract', '')):
                        cats = []
                        cat_info = obj.get('category_info', '')
                        if isinstance(cat_info, str) and cat_info:
                            try:
                                cl = json.loads(cat_info)
                                cats = [c['Name'] for c in cl if isinstance(c, dict) and c.get('Name')]
                            except:
                                pass
                        elif isinstance(cat_info, list):
                            cats = [c['Name'] for c in cat_info if isinstance(c, dict) and c.get('Name')]
                        book_meta[bid] = {
                            'title': bname,
                            'abstract': abstract,
                            'categories': cats[:5],
                            'author': obj.get('author', ''),
                        }
                for v in obj.values():
                    _extract_books(v, depth + 1)
            elif isinstance(obj, list):
                for item in obj[:50]:
                    _extract_books(item, depth + 1)

        _extract_books(data)

    print(f"  Book metadata from all endpoints: {len(book_meta)} titles")

    # 3. Extract all series (dramas) with their complete vid lists
    series = {}
    for entry in entries:
        url = entry['request']['url']
        if 'video_detail' not in url or 'video_model' in url:
            continue
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
        if not isinstance(data.get('data'), dict):
            continue

        # Collect all video_data dicts from this response
        # Format 1 (melolo1): data -> {series_id: {video_data: {...}}}
        # Format 2 (melolo2/3): data -> {video_data: {..., series_id, series_title}}
        video_datas = []  # list of (series_id, vd_dict)
        
        d = data['data']
        if 'video_data' in d and isinstance(d['video_data'], dict):
            # Format 2: flat structure
            vd = d['video_data']
            sid = str(vd.get('series_id', '') or vd.get('series_id_str', ''))
            if sid and vd.get('video_list'):
                video_datas.append((sid, vd))
        else:
            # Format 1: nested under series_id keys
            for k, v in d.items():
                if not isinstance(v, dict):
                    continue
                vd = v.get('video_data')
                if not isinstance(vd, dict) or not vd.get('video_list'):
                    continue
                video_datas.append((k, vd))

        for sid, vd in video_datas:
            video_list = vd['video_list']
            total_ep = vd.get('total_episode', 0) or vd.get('episode_cnt', 0) or len(video_list)
            # series_cover = drama poster from main screen (correct one)
            cover_url = vd.get('series_cover', '') or vd.get('cover_url', '')
            
            # Get title/abstract — try book_meta first, then video_data fields
            meta = book_meta.get(sid, {})
            title = meta.get('title', '') or vd.get('series_title', '')
            abstract = meta.get('abstract', '') or vd.get('series_intro', '') or vd.get('book_name', '')
            genres = meta.get('categories', [])
            author = meta.get('author', '')

            # Fallback: try to parse genres from video_data if book_meta has none
            if not genres:
                cat_str = vd.get('category_schema', '')
                if cat_str:
                    try:
                        cats = json.loads(cat_str)
                        if isinstance(cats, list):
                            for c in cats:
                                if isinstance(c, dict) and c.get('name'):
                                    genres.append(c['name'])
                    except:
                        pass

            vids = []
            for item in video_list:
                if isinstance(item, dict) and item.get('vid'):
                    vids.append({
                        'vid': item['vid'],
                        'index': item.get('vid_index', 0),
                    })

            # Dedup by series_id, keep the one with most vids
            if sid not in series or len(vids) > len(series[sid].get('vids', [])):
                series[sid] = {
                    'series_id': sid,
                    'title': title,
                    'total_episodes': total_ep,
                    'cover_url': cover_url,
                    'abstract': abstract,
                    'genres': genres[:5],
                    'author': author,
                    'vids': vids,
                }

    print(f"\nSeries found: {len(series)}")
    total_vids = sum(len(s['vids']) for s in series.values())
    print(f"Total episode vids: {total_vids}")
    with_title = sum(1 for s in series.values() if s['title'])
    print(f"With title: {with_title}/{len(series)}")
    
    for sid, info in sorted(series.items(), key=lambda x: -x[1]['total_episodes']):
        t = info['title'] or f"(series {sid[-8:]})"
        print(f"  {t[:48]:<50} Eps: {info['total_episodes']:>3}  VIDs: {len(info['vids'])}")

    return {'api_template': api_template, 'series': series}



def fetch_video_urls(api_template: dict, vids: list, retry_state: dict = None) -> dict:
    """Fetch video URLs for a batch of vids via API replay.
    Includes automatic retry with exponential backoff on rate limit/timeout.
    retry_state is a mutable dict tracking consecutive failures for adaptive behavior.
    """
    url = api_template['base_url']
    
    # Headers
    headers = {}
    skip = {'accept-encoding', 'content-length', 'host', 'connection', 'content-encoding'}
    for k, v in api_template['headers'].items():
        if k.lower() not in skip:
            headers[k] = v

    # POST body
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
        "video_id": ",".join(vids)
    }

    if retry_state is None:
        retry_state = {'consecutive_fails': 0, 'current_delay': API_DELAY}

    for attempt in range(API_MAX_RETRIES + 1):
        try:
            params = dict(api_template['params'])
            params['_rticket'] = str(int(time.time() * 1000))
            
            resp = requests.post(url, params=params, headers=headers, json=body, timeout=30)
            
            # Check for rate limit HTTP status
            if resp.status_code == 429 or resp.status_code >= 500:
                wait = API_BACKOFF_BASE * (2 ** attempt)
                wait = min(wait, API_BACKOFF_MAX)
                print(f" HTTP {resp.status_code} rate limited!", flush=True)
                print(f"      ⏳ Cooldown {wait}s (attempt {attempt+1}/{API_MAX_RETRIES+1})...", end='', flush=True)
                time.sleep(wait)
                print(f" retrying", flush=True)
                continue
            
            data = resp.json()
            
            results = {}
            if isinstance(data.get('data'), dict):
                for vid, vinfo in data['data'].items():
                    if isinstance(vinfo, dict) and vinfo.get('main_url'):
                        results[vid] = {
                            'main_url': vinfo['main_url'],
                            'backup_url': vinfo.get('backup_url', ''),
                            'width': vinfo.get('video_width', 0),
                            'height': vinfo.get('video_height', 0),
                        }
            
            if results:
                # Success — reset failure counter, reduce delay
                retry_state['consecutive_fails'] = 0
                retry_state['current_delay'] = max(API_DELAY, retry_state['current_delay'] * 0.8)
            else:
                retry_state['consecutive_fails'] += 1
            
            return results
            
        except (requests.exceptions.Timeout, requests.exceptions.ConnectionError) as e:
            retry_state['consecutive_fails'] += 1
            
            if attempt < API_MAX_RETRIES:
                wait = API_BACKOFF_BASE * (2 ** attempt)
                wait = min(wait, API_BACKOFF_MAX)
                print(f" timeout!", flush=True)
                print(f"      ⏳ Cooldown {wait}s (attempt {attempt+1}/{API_MAX_RETRIES+1})...", end='', flush=True)
                time.sleep(wait)
                print(f" retrying", flush=True)
            else:
                print(f" FAIL after {API_MAX_RETRIES+1} attempts", flush=True)
                return {}
        except Exception as e:
            print(f" API error: {e}", flush=True)
            retry_state['consecutive_fails'] += 1
            return {}
    
    return {}


def download_video(url: str, backup_url: str, output_path: Path) -> bool:
    if output_path.exists() and output_path.stat().st_size > 1000:
        return True
    for video_url in [url, backup_url]:
        if not video_url:
            continue
        try:
            resp = requests.get(video_url, timeout=120, stream=True)
            resp.raise_for_status()
            total = 0
            with open(output_path, 'wb') as f:
                for chunk in resp.iter_content(chunk_size=1024 * 1024):
                    f.write(chunk)
                    total += len(chunk)
            if total > 1000:
                return True
        except:
            continue
    return False


def convert_to_hls(mp4_path: Path, output_dir: Path) -> bool:
    output_dir.mkdir(parents=True, exist_ok=True)
    playlist = output_dir / "playlist.m3u8"
    if playlist.exists():
        return True
    try:
        result = subprocess.run([
            'ffmpeg', '-y', '-i', str(mp4_path),
            '-c:v', 'copy', '-c:a', 'aac',
            '-f', 'hls', '-hls_time', str(HLS_SEGMENT_DURATION),
            '-hls_list_size', '0',
            '-hls_segment_filename', str(output_dir / 'segment_%03d.ts'),
            str(playlist)
        ], capture_output=True, timeout=300)
        return result.returncode == 0
    except:
        return False


def download_cover(cover_url: str, output_path: Path) -> bool:
    if not cover_url or (output_path.exists() and output_path.stat().st_size > 100):
        return output_path.exists()
    try:
        resp = requests.get(cover_url, timeout=30)
        resp.raise_for_status()
        raw = output_path.with_suffix('.raw')
        with open(raw, 'wb') as f:
            f.write(resp.content)
        result = subprocess.run(
            ['ffmpeg', '-y', '-i', str(raw), '-q:v', '2', str(output_path)],
            capture_output=True, timeout=30
        )
        if result.returncode == 0:
            raw.unlink(missing_ok=True)
            return True
        raw.rename(output_path)
        return True
    except:
        return False


def process_all(replay_data: dict, max_dramas: int = 0):
    """Auto-scrape all dramas"""
    print(f"\n{'='*60}")
    print(f"  STEP 2: AUTO-SCRAPING ALL EPISODES")
    print(f"{'='*60}\n")

    api = replay_data['api_template']
    all_series = replay_data['series']
    
    # Sort by episode count (most episodes first)
    sorted_series = sorted(all_series.items(), key=lambda x: -x[1]['total_episodes'])
    if max_dramas > 0:
        sorted_series = sorted_series[:max_dramas]

    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    DOWNLOAD_DIR.mkdir(parents=True, exist_ok=True)

    stats = {'dramas': 0, 'episodes': 0, 'api_calls': 0, 'covers': 0, 'errors': 0}

    for i, (key, drama) in enumerate(sorted_series, 1):
        title = drama['title'] or f"Drama {drama['series_id'][-8:]}"
        slug = slugify(title) if drama['title'] else f"drama-{drama['series_id'][-8:]}"
        
        drama_dir = OUTPUT_DIR / slug
        drama_dir.mkdir(parents=True, exist_ok=True)
        episodes_dir = drama_dir / "episodes"
        episodes_dir.mkdir(exist_ok=True)

        all_vids = drama['vids']
        
        print(f"\n{'_'*60}")
        print(f"  [{i}/{len(sorted_series)}] {title}")
        print(f"  Series: {drama['series_id']}")
        print(f"  Episodes: {len(all_vids)}")
        print(f"  Genres: {', '.join(drama.get('genres', []))[:60]}")
        print(f"{'_'*60}")

        # Download cover (series_cover = drama poster from main browse screen)
        cover_path = drama_dir / "cover.jpg"
        if download_cover(drama.get('cover_url', ''), cover_path):
            stats['covers'] += 1
            print(f"  Cover: OK (series poster)")
        else:
            print(f"  Cover: N/A")

        # Fetch video URLs in batches (with smart rate-limit recovery)
        print(f"\n  Fetching video URLs ({len(all_vids)} episodes)...")
        video_urls = {}
        vid_ids = [v['vid'] for v in all_vids]
        retry_state = {'consecutive_fails': 0, 'current_delay': API_DELAY}
        
        for batch_start in range(0, len(vid_ids), BATCH_SIZE):
            batch = vid_ids[batch_start:batch_start + BATCH_SIZE]
            batch_end = min(batch_start + BATCH_SIZE, len(vid_ids))
            
            # Check for consecutive failures — big cooldown if API seems rate-limited
            if retry_state['consecutive_fails'] >= API_CONSECUTIVE_FAIL_THRESHOLD:
                cooldown = API_BACKOFF_BASE * 2  # 60s cooldown
                print(f"    ⚠️  {retry_state['consecutive_fails']} consecutive fails — API likely rate-limited")
                print(f"    ⏳ Big cooldown {cooldown}s to let API recover...", flush=True)
                time.sleep(cooldown)
                retry_state['consecutive_fails'] = 0  # reset after cooldown
                retry_state['current_delay'] = API_DELAY * 3  # use slower pace after recovery
            
            print(f"    API call: episodes {batch_start+1}-{batch_end}...", end='', flush=True)
            
            urls = fetch_video_urls(api, batch, retry_state)
            video_urls.update(urls)
            stats['api_calls'] += 1
            
            print(f" got {len(urls)}/{len(batch)}")
            
            if batch_end < len(vid_ids):
                delay = retry_state['current_delay']
                time.sleep(delay)

        print(f"  Total URLs fetched: {len(video_urls)}/{len(all_vids)}")

        # Download and convert
        ep_success = 0
        for vid_info in all_vids:
            vid = vid_info['vid']
            ep_num = vid_info['index'] + 1  # 1-indexed
            ep_str = f"{ep_num:03d}"
            
            if vid not in video_urls:
                continue  # URL not available

            ep_dir = episodes_dir / ep_str
            mp4_dir = DOWNLOAD_DIR / slug
            mp4_dir.mkdir(parents=True, exist_ok=True)
            mp4_path = mp4_dir / f"ep_{ep_str}.mp4"

            urls = video_urls[vid]
            
            print(f"  Ep {ep_num:>3}: ", end='', flush=True)
            
            if download_video(urls['main_url'], urls.get('backup_url', ''), mp4_path):
                size_mb = mp4_path.stat().st_size / 1024 / 1024
                print(f"DL {size_mb:.1f}MB -> ", end='', flush=True)
                if convert_to_hls(mp4_path, ep_dir):
                    segs = len(list(ep_dir.glob('segment_*.ts')))
                    print(f"HLS {segs} seg OK")
                    ep_success += 1
                else:
                    print(f"HLS FAIL")
                    stats['errors'] += 1
            else:
                print(f"DL FAIL")
                stats['errors'] += 1

        stats['episodes'] += ep_success

        # Save metadata
        metadata = {
            'source': 'melolo',
            'series_id': drama['series_id'],
            'title': drama.get('title', ''),
            'slug': slug,
            'author': drama.get('author', ''),
            'description': drama.get('abstract', ''),
            'genres': drama.get('genres', []),
            'total_episodes': drama['total_episodes'],
            'captured_episodes': ep_success,
            'cover': 'cover.jpg' if cover_path.exists() else '',
            'episodes': [
                {
                    'number': vi['index'] + 1,
                    'path': f"episodes/{vi['index']+1:03d}/playlist.m3u8"
                }
                for vi in sorted(all_vids, key=lambda x: x['index'])
                if (episodes_dir / f"{vi['index']+1:03d}" / "playlist.m3u8").exists()
            ]
        }
        with open(drama_dir / "metadata.json", 'w', encoding='utf-8') as f:
            json.dump(metadata, f, indent=2, ensure_ascii=False)

        stats['dramas'] += 1
        print(f"\n  => {title}: {ep_success}/{len(all_vids)} episodes done")

    # Final
    print(f"\n\n{'='*60}")
    print(f"  AUTO-SCRAPE COMPLETE!")
    print(f"{'='*60}")
    print(f"  Dramas: {stats['dramas']}")
    print(f"  Episodes: {stats['episodes']}")
    print(f"  API calls: {stats['api_calls']}")
    print(f"  Covers: {stats['covers']}")
    print(f"  Errors: {stats['errors']}")
    print(f"\n  Output: {OUTPUT_DIR}")
    print(f"  Next: python upload_to_r2.py")


if __name__ == '__main__':
    if len(sys.argv) < 2:
        print("Usage: python auto_scraper.py <harfile.har> [max_dramas]")
        print("\nExamples:")
        print("  python auto_scraper.py melolo1.har        # All dramas")
        print("  python auto_scraper.py melolo1.har 5      # First 5 only")
        sys.exit(1)

    har_path = Path(sys.argv[1])
    max_dramas = int(sys.argv[2]) if len(sys.argv) > 2 else 0

    if not har_path.exists():
        print(f"File not found: {har_path}")
        sys.exit(1)

    # Extract
    replay_data = extract_replay_data(har_path)

    # Save replay data
    save_path = SCRIPT_DIR / "melolo_analysis" / "replay_data.json"
    save_path.parent.mkdir(exist_ok=True)
    with open(save_path, 'w', encoding='utf-8') as f:
        json.dump(replay_data, f, indent=2, ensure_ascii=False, default=str)
    print(f"\n  Saved: {save_path}")

    # Process
    process_all(replay_data, max_dramas)
