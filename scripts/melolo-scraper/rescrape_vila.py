#!/usr/bin/env python3
"""
Quick re-scrape for vila-portal-dunia-lain episode 036
"""
import json, sys, io, os, time, subprocess, requests
from pathlib import Path
from dotenv import load_dotenv

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
sys.stdout.reconfigure(line_buffering=True)

load_dotenv(Path(__file__).parent / '.env')

# Configuration
DRAMA_SLUG = "vila-portal-dunia-lain"
EPISODE_TO_FETCH = 36
SCRIPT_DIR = Path(__file__).parent
OUTPUT_DIR = SCRIPT_DIR / "r2_ready" / "melolo" / DRAMA_SLUG
DOWNLOAD_DIR = SCRIPT_DIR / "downloads" / DRAMA_SLUG
HLS_SEGMENT_DURATION = 6

print("=" * 60)
print(f"  RE-SCRAPE: {DRAMA_SLUG} Episode {EPISODE_TO_FETCH}")
print("=" * 60)

# Load metadata
meta_path = OUTPUT_DIR / "metadata.json"
if not meta_path.exists():
    print(f"❌ Drama not found: {meta_path}")
    sys.exit(1)

with open(meta_path, 'r', encoding='utf-8') as f:
    meta = json.load(f)

series_id = meta.get('series_id', '')
print(f"\nDrama: {meta.get('title', DRAMA_SLUG)}")
print(f"Series ID: {series_id}")

# Find vid for episode 036 from HAR files
print(f"\n🔍 Searching for episode {EPISODE_TO_FETCH} vid in HAR files...")

target_vid = None
api_template = None

for har_name in ['melolo1.har', 'melolo2.har', 'melolo3.har', 'melolo4.har']:
    har_path = SCRIPT_DIR / har_name
    if not har_path.exists():
        continue
    
    print(f"  Checking {har_name}...", end='', flush=True)
    
    with open(har_path, 'r', encoding='utf-8') as f:
        har = json.load(f)
    
    for entry in har['log']['entries']:
        url = entry['request']['url']
        
        # Capture API template
        if 'multi_video_model' in url and api_template is None:
            from urllib.parse import urlparse
            parsed = urlparse(url)
            params = {}
            if parsed.query:
                for p in parsed.query.split('&'):
                    if '=' in p:
                        k, v = p.split('=', 1)
                        params[k] = v
            req_headers = {h['name']: h['value'] for h in entry['request'].get('headers', [])}
            api_template = {
                'base_url': f"{parsed.scheme}://{parsed.hostname}{parsed.path}",
                'params': params,
                'headers': req_headers,
            }
        
        if 'video_detail' not in url:
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
        
        # Extract video_data
        for key, value in data['data'].items():
            if not isinstance(value, dict):
                continue
            
            vd = value.get('video_data')
            if not isinstance(vd, dict):
                continue
            
            sid = str(vd.get('series_id', ''))
            if sid != series_id:
                continue
            
            # Found matching series, search for episode 36
            for item in vd.get('video_list', []):
                if isinstance(item, dict):
                    ep_index = item.get('vid_index', -1)
                    if ep_index == EPISODE_TO_FETCH - 1:  # index is 0-based
                        target_vid = str(item.get('vid', ''))
                        print(f" ✅ Found! vid={target_vid}")
                        break
            
            if target_vid:
                break
    
    if target_vid:
        break

if not target_vid:
    print(f"\n❌ Episode {EPISODE_TO_FETCH} vid not found in HAR files!")
    sys.exit(1)

if not api_template:
    print(f"\n❌ API template not found in HAR files!")
    sys.exit(1)

# Fetch video URL from API
print(f"\n📡 Fetching video URL from API...")

url = api_template['base_url']
headers = {}
skip_headers = {'accept-encoding', 'content-length', 'host', 'connection', 'content-encoding'}
for k, v in api_template['headers'].items():
    if k.lower() not in skip_headers:
        headers[k] = v

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
    "video_id": target_vid
}

params = dict(api_template['params'])
params['_rticket'] = str(int(time.time() * 1000))

try:
    resp = requests.post(url, params=params, headers=headers, json=body, timeout=30)
    resp.raise_for_status()
    data = resp.json()
    
    video_url = None
    backup_url = None
    
    if isinstance(data.get('data'), dict):
        for vid, vinfo in data['data'].items():
            if vid == target_vid and isinstance(vinfo, dict):
                video_url = vinfo.get('main_url', '')
                backup_url = vinfo.get('backup_url', '')
                break
    
    if not video_url:
        print(f"❌ Video URL not found in API response!")
        sys.exit(1)
    
    print(f"✅ Got video URL")
    
except Exception as e:
    print(f"❌ API request failed: {e}")
    sys.exit(1)

# Download video
print(f"\n📥 Downloading episode {EPISODE_TO_FETCH}...")

DOWNLOAD_DIR.mkdir(parents=True, exist_ok=True)
mp4_path = DOWNLOAD_DIR / f"ep_{EPISODE_TO_FETCH:03d}.mp4"

for url_to_try in [video_url, backup_url]:
    if not url_to_try:
        continue
    
    print(f"  Trying URL...", end='', flush=True)
    
    try:
        resp = requests.get(url_to_try, timeout=120, stream=True)
        resp.raise_for_status()
        
        total_mb = 0
        with open(mp4_path, 'wb') as f:
            for chunk in resp.iter_content(chunk_size=1024 * 1024):
                f.write(chunk)
                total_mb += len(chunk) / (1024 * 1024)
        
        if mp4_path.stat().st_size > 1000:
            print(f" ✅ Downloaded {total_mb:.1f} MB")
            break
    except Exception as e:
        print(f" ❌ Failed: {e}")
        continue
else:
    print(f"\n❌ Download failed for all URLs!")
    sys.exit(1)

# Convert to HLS
print(f"\n🎬 Converting to HLS...")

ep_dir = OUTPUT_DIR / "episodes" / f"{EPISODE_TO_FETCH:03d}"
ep_dir.mkdir(parents=True, exist_ok=True)
playlist = ep_dir / "playlist.m3u8"

try:
    result = subprocess.run([
        'ffmpeg', '-y', '-i', str(mp4_path),
        '-c:v', 'copy', '-c:a', 'aac',
        '-f', 'hls', '-hls_time', str(HLS_SEGMENT_DURATION),
        '-hls_list_size', '0',
        '-hls_segment_filename', str(ep_dir / 'segment_%03d.ts'),
        str(playlist)
    ], capture_output=True, timeout=300)
    
    if result.returncode == 0:
        segments = len(list(ep_dir.glob('segment_*.ts')))
        print(f"✅ HLS created: {segments} segments")
        
        # Clean up MP4
        mp4_path.unlink(missing_ok=True)
        
        # Update metadata
        with open(meta_path, 'r', encoding='utf-8') as f:
            meta = json.load(f)
        
        # Re-scan episodes
        eps_dir = OUTPUT_DIR / "episodes"
        all_eps = []
        if eps_dir.exists():
            for ep_d in sorted(eps_dir.iterdir()):
                if ep_d.is_dir() and (ep_d / 'playlist.m3u8').exists():
                    try:
                        ep_num = int(ep_d.name)
                        all_eps.append({
                            'number': ep_num,
                            'path': f"episodes/{ep_d.name}/playlist.m3u8"
                        })
                    except:
                        pass
        
        meta['captured_episodes'] = len(all_eps)
        meta['episodes'] = all_eps
        
        with open(meta_path, 'w', encoding='utf-8') as f:
            json.dump(meta, f, indent=2, ensure_ascii=False)
        
        print(f"\n✅ Episode {EPISODE_TO_FETCH} successfully added!")
        print(f"   Total episodes: {len(all_eps)}")
        
    else:
        print(f"❌ FFmpeg conversion failed!")
        print(result.stderr.decode('utf-8', errors='replace')[-500:])
        sys.exit(1)
        
except Exception as e:
    print(f"❌ Conversion error: {e}")
    sys.exit(1)

print("\n" + "=" * 60)
print("  RE-SCRAPE COMPLETE!")
print("=" * 60)
