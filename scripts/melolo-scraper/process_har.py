#!/usr/bin/env python3
"""
MELOLO HAR PROCESSOR
====================
Extracts drama metadata + video URLs from captured HAR file,
downloads MP4s, converts to HLS segments via ffmpeg, and organizes
into r2_ready folder structure for upload.

Mapping:
  video_detail → video_data.video_list[].vid (episode list)
  video_model  → data[vid].main_url         (MP4 download URL)

Usage:
    python process_har.py melolo1.har        # Process all
    python process_har.py melolo1.har 3      # First 3 dramas only
"""

import json
import sys
import os
import io
import re
import subprocess
import time
from pathlib import Path
from urllib.parse import urlparse
from collections import defaultdict

# Fix encoding on Windows
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')

try:
    import requests
except ImportError:
    print("Installing requests...")
    subprocess.run([sys.executable, '-m', 'pip', 'install', 'requests'], check=True)
    import requests

SCRIPT_DIR = Path(__file__).parent
OUTPUT_DIR = SCRIPT_DIR / "r2_ready" / "melolo"
DOWNLOAD_DIR = SCRIPT_DIR / "downloads"
HLS_SEGMENT_DURATION = 6


def slugify(text: str) -> str:
    text = text.lower().strip()
    text = re.sub(r'[^\w\s-]', '', text)
    text = re.sub(r'[\s_]+', '-', text)
    text = re.sub(r'-+', '-', text)
    return text[:60].rstrip('-')


def extract_dramas_from_har(har_path: Path) -> dict:
    """Extract all drama data from HAR"""
    print(f"\n{'='*60}")
    print(f"  EXTRACTING DATA FROM HAR")
    print(f"{'='*60}\n")

    with open(har_path, 'r', encoding='utf-8') as f:
        har_data = json.load(f)

    entries = har_data['log']['entries']
    print(f"Total HAR entries: {len(entries)}")

    # STEP 1: Collect ALL video_model URLs (vid -> {main_url, backup_url, ...})
    video_urls = {}
    for entry in entries:
        url = entry['request']['url']
        mime = entry['response']['content'].get('mimeType', '')
        if 'json' not in mime:
            continue
        text = entry['response']['content'].get('text', '')
        if not text:
            continue
        if 'video_model' not in url:
            continue
        try:
            data = json.loads(text)
        except:
            continue
        if not isinstance(data.get('data'), dict):
            continue
        for vid, vinfo in data['data'].items():
            if isinstance(vinfo, dict) and 'main_url' in vinfo:
                video_urls[str(vid)] = {
                    'main_url': vinfo.get('main_url', ''),
                    'backup_url': vinfo.get('backup_url', ''),
                    'video_width': vinfo.get('video_width', 0),
                    'video_height': vinfo.get('video_height', 0),
                }

    print(f"Video URLs collected: {len(video_urls)}")

    # STEP 2: Collect drama metadata from video_detail (series -> episodes with vid)
    dramas = {}  # series_id -> drama info
    
    for entry in entries:
        url = entry['request']['url']
        mime = entry['response']['content'].get('mimeType', '')
        if 'json' not in mime:
            continue
        text = entry['response']['content'].get('text', '')
        if not text:
            continue
        if 'video_detail' not in url:
            continue
        if 'video_model' in url:
            continue
        try:
            data = json.loads(text)
        except:
            continue
        if not isinstance(data.get('data'), dict):
            continue

        for series_id, series_data in data['data'].items():
            if not isinstance(series_data, dict):
                continue
            vd = series_data.get('video_data', {})
            if not isinstance(vd, dict):
                continue
            
            video_list = vd.get('video_list', [])
            if not video_list:
                continue

            book_name = vd.get('book_name', '')
            book_id = str(vd.get('book_id', series_id))
            abstract = vd.get('abstract', '')
            cover_url = vd.get('cover_url', '')
            total_ep = vd.get('total_episode', len(video_list))

            # Parse categories
            genres = []
            cat_schema = vd.get('category_schema', '')
            if cat_schema:
                try:
                    cats = json.loads(cat_schema)
                    if isinstance(cats, list):
                        for cat in cats:
                            if isinstance(cat, dict) and cat.get('name'):
                                genres.append(cat['name'])
                except:
                    pass

            # Build episode list with download URLs
            episodes = []
            for item in video_list:
                if not isinstance(item, dict):
                    continue
                vid = str(item.get('vid', ''))
                vid_index = item.get('vid_index', 0)
                ep_cover = item.get('cover', '')

                # Check if we have the video URL for this vid
                has_url = vid in video_urls
                ep_data = {
                    'vid': vid,
                    'order': vid_index + 1,  # 1-indexed
                    'cover': ep_cover,
                    'has_url': has_url,
                }
                if has_url:
                    ep_data['main_url'] = video_urls[vid]['main_url']
                    ep_data['backup_url'] = video_urls[vid]['backup_url']
                    ep_data['width'] = video_urls[vid]['video_width']
                    ep_data['height'] = video_urls[vid]['video_height']

                episodes.append(ep_data)

            # Sort by order
            episodes.sort(key=lambda x: x['order'])
            downloadable = [e for e in episodes if e['has_url']]

            # Use series_id as key (dedup by book_name if already exists)
            existing = None
            for sid, d in dramas.items():
                if d['title'] == book_name and book_name:
                    existing = sid
                    break

            if existing:
                # Merge episodes
                existing_vids = {e['vid'] for e in dramas[existing]['episodes']}
                for ep in episodes:
                    if ep['vid'] not in existing_vids:
                        dramas[existing]['episodes'].append(ep)
                dramas[existing]['episodes'].sort(key=lambda x: x['order'])
                dl = [e for e in dramas[existing]['episodes'] if e['has_url']]
                dramas[existing]['downloadable_episodes'] = len(dl)
            else:
                slug = slugify(book_name) if book_name else f"drama-{series_id[-8:]}"
                dramas[series_id] = {
                    'series_id': series_id,
                    'book_id': book_id,
                    'title': book_name,
                    'slug': slug,
                    'abstract': abstract,
                    'genres': genres[:5],
                    'cover_url': cover_url,
                    'total_episodes': total_ep,
                    'captured_episodes': len(episodes),
                    'downloadable_episodes': len(downloadable),
                    'episodes': episodes,
                }

    # STEP 3: Also try to match via bookshelf/history for enrichment
    for entry in entries:
        url = entry['request']['url']
        mime = entry['response']['content'].get('mimeType', '')
        if 'json' not in mime:
            continue
        text = entry['response']['content'].get('text', '')
        if not text:
            continue
        if 'book_history' not in url and 'bookshelf' not in url and 'bookmall' not in url:
            continue
        try:
            data = json.loads(text)
        except:
            continue
        # Collect cover_url and other metadata by book_name for enrichment
        items = []
        if isinstance(data.get('data'), dict):
            items = data['data'].get('data_list', [])
            if not items:
                cells = data['data'].get('cells', [])
                for cell in cells:
                    items.extend(cell.get('books', []))
        
        for item in items:
            book_info = item.get('book_info', item)
            bn = book_info.get('book_name', '')
            if not bn:
                continue
            # Find matching drama by title
            for sid, drama in dramas.items():
                if drama['title'] == bn:
                    if not drama.get('abstract') and book_info.get('abstract'):
                        drama['abstract'] = book_info['abstract']
                    if not drama.get('cover_url') and book_info.get('cover_url'):
                        drama['cover_url'] = book_info['cover_url']
                    if not drama.get('author') and book_info.get('author'):
                        drama['author'] = book_info['author']

    # Summary
    print(f"\n  Extraction Summary:")
    print(f"  - Total dramas: {len(dramas)}")
    dramas_with_dl = {k: v for k, v in dramas.items() if v['downloadable_episodes'] > 0}
    print(f"  - Dramas with downloadable episodes: {len(dramas_with_dl)}")
    total_dl = sum(d['downloadable_episodes'] for d in dramas.values())
    print(f"  - Total downloadable episodes: {total_dl}")

    print(f"\n  Dramas:")
    for sid, d in sorted(dramas.items(), key=lambda x: -x[1]['downloadable_episodes']):
        status = "OK" if d['downloadable_episodes'] > 0 else "--"
        genre_str = ', '.join(d['genres'][:3]) if d['genres'] else 'Unknown'
        title = d['title'][:42] if d['title'] else f"(series {sid[-8:]})"
        print(f"  [{status}] {title:<44} DL: {d['downloadable_episodes']:>3}/{d['total_episodes']:<4} [{genre_str}]")

    return dramas


def download_cover(cover_url: str, output_path: Path) -> bool:
    """Download cover image and convert HEIC to JPG"""
    if not cover_url or (output_path.exists() and output_path.stat().st_size > 100):
        return output_path.exists()

    try:
        resp = requests.get(cover_url, timeout=30)
        resp.raise_for_status()

        raw_path = output_path.with_suffix('.raw')
        with open(raw_path, 'wb') as f:
            f.write(resp.content)

        # Convert to JPG via ffmpeg (works for HEIC, WebP, etc)
        result = subprocess.run(
            ['ffmpeg', '-y', '-i', str(raw_path), '-q:v', '2', str(output_path)],
            capture_output=True, timeout=30
        )
        if result.returncode == 0:
            raw_path.unlink(missing_ok=True)
            return True
        else:
            raw_path.rename(output_path)
            return True
    except Exception as e:
        print(f"      Cover download failed: {e}")
        return False


def download_video(url: str, backup_url: str, output_path: Path) -> bool:
    """Download MP4 video"""
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
        except Exception as e:
            continue
    return False


def convert_to_hls(mp4_path: Path, output_dir: Path) -> bool:
    """Convert MP4 to HLS segments via ffmpeg"""
    output_dir.mkdir(parents=True, exist_ok=True)
    playlist_path = output_dir / "playlist.m3u8"
    segment_pattern = output_dir / "segment_%03d.ts"

    if playlist_path.exists():
        return True

    try:
        result = subprocess.run([
            'ffmpeg', '-y',
            '-i', str(mp4_path),
            '-c:v', 'copy',
            '-c:a', 'aac',
            '-f', 'hls',
            '-hls_time', str(HLS_SEGMENT_DURATION),
            '-hls_list_size', '0',
            '-hls_segment_filename', str(segment_pattern),
            str(playlist_path)
        ], capture_output=True, timeout=300)

        if result.returncode == 0:
            segments = list(output_dir.glob('segment_*.ts'))
            return len(segments) > 0
        return False
    except Exception as e:
        return False


def process_dramas(dramas: dict, max_dramas: int = 0):
    """Download videos and convert to HLS"""
    print(f"\n{'='*60}")
    print(f"  PROCESSING DRAMAS")
    print(f"{'='*60}\n")

    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    DOWNLOAD_DIR.mkdir(parents=True, exist_ok=True)

    # Only dramas with downloadable episodes
    processable = {k: v for k, v in dramas.items() if v['downloadable_episodes'] > 0}
    if max_dramas > 0:
        processable = dict(list(processable.items())[:max_dramas])

    print(f"Processing {len(processable)} dramas\n")

    stats = {'dramas': 0, 'episodes': 0, 'covers': 0, 'errors': 0, 'skipped': 0}

    for i, (sid, drama) in enumerate(processable.items(), 1):
        slug = drama['slug']
        drama_dir = OUTPUT_DIR / slug
        drama_dir.mkdir(parents=True, exist_ok=True)
        episodes_dir = drama_dir / "episodes"
        episodes_dir.mkdir(exist_ok=True)

        title = drama['title'] or f"Drama {sid[-8:]}"
        dl_eps = [ep for ep in drama['episodes'] if ep['has_url']]

        print(f"\n{'_'*60}")
        print(f"  [{i}/{len(processable)}] {title}")
        print(f"  Episodes to download: {len(dl_eps)}")
        print(f"{'_'*60}")

        # Cover
        cover_path = drama_dir / "cover.jpg"
        if download_cover(drama['cover_url'], cover_path):
            stats['covers'] += 1
            print(f"  Cover: OK")
        else:
            print(f"  Cover: N/A")

        # Episodes
        ep_success = 0
        for ep in dl_eps:
            ep_num = f"{ep['order']:03d}"
            ep_dir = episodes_dir / ep_num
            mp4_dir = DOWNLOAD_DIR / slug
            mp4_dir.mkdir(parents=True, exist_ok=True)
            mp4_path = mp4_dir / f"ep_{ep_num}.mp4"

            print(f"  Ep {ep['order']:>3}: ", end='', flush=True)

            if download_video(ep['main_url'], ep.get('backup_url', ''), mp4_path):
                size_mb = mp4_path.stat().st_size / 1024 / 1024
                print(f"DL {size_mb:.1f}MB -> ", end='', flush=True)
                if convert_to_hls(mp4_path, ep_dir):
                    segs = len(list(ep_dir.glob('segment_*.ts')))
                    print(f"HLS {segs} segments OK")
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
            'series_id': sid,
            'book_id': drama.get('book_id', ''),
            'title': drama['title'],
            'slug': slug,
            'author': drama.get('author', ''),
            'description': drama.get('abstract', ''),
            'genres': drama.get('genres', []),
            'total_episodes': drama['total_episodes'],
            'captured_episodes': ep_success,
            'cover': 'cover.jpg' if cover_path.exists() else '',
            'episodes': [
                {
                    'number': ep['order'],
                    'path': f"episodes/{ep['order']:03d}/playlist.m3u8"
                }
                for ep in sorted(dl_eps, key=lambda x: x['order'])
                if (episodes_dir / f"{ep['order']:03d}" / "playlist.m3u8").exists()
            ]
        }
        with open(drama_dir / "metadata.json", 'w', encoding='utf-8') as f:
            json.dump(metadata, f, indent=2, ensure_ascii=False)

        stats['dramas'] += 1
        print(f"  => {ep_success} episodes done")

    # Final
    print(f"\n\n{'='*60}")
    print(f"  DONE!")
    print(f"{'='*60}")
    print(f"  Dramas: {stats['dramas']}")
    print(f"  Episodes: {stats['episodes']}")
    print(f"  Covers: {stats['covers']}")
    print(f"  Errors: {stats['errors']}")
    print(f"\n  Output: {OUTPUT_DIR}")
    print(f"  Next: python upload_to_r2.py")


if __name__ == '__main__':
    if len(sys.argv) < 2:
        print("Usage: python process_har.py <harfile.har> [max_dramas]")
        sys.exit(1)

    har_path = Path(sys.argv[1])
    max_dramas = int(sys.argv[2]) if len(sys.argv) > 2 else 0

    if not har_path.exists():
        print(f"File not found: {har_path}")
        sys.exit(1)

    # Extract
    dramas = extract_dramas_from_har(har_path)

    # Save extraction results
    extract_path = SCRIPT_DIR / "melolo_analysis" / "extracted_dramas.json"
    extract_path.parent.mkdir(exist_ok=True)
    with open(extract_path, 'w', encoding='utf-8') as f:
        json.dump(dramas, f, indent=2, ensure_ascii=False)
    print(f"\n  Saved: {extract_path}")

    # Process
    process_dramas(dramas, max_dramas)
