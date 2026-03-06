#!/usr/bin/env python3
"""
REPAIR SCRIPT — Fix titles, covers, and re-scrape missing episodes
===================================================================
1. Fix missing titles from HAR data  
2. Download missing cover images
3. Re-fetch episodes for 0-episode and partial dramas
"""
import json, sys, io, os, re, time, subprocess, shutil
from pathlib import Path
from urllib.parse import urlparse

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
BATCH_SIZE = 8
API_DELAY = 2.0  # Slightly slower to avoid rate limits
API_MAX_RETRIES = 3
API_BACKOFF_BASE = 30
API_BACKOFF_MAX = 180
API_CONSECUTIVE_FAIL_THRESHOLD = 3

def slugify(text):
    text = text.lower().strip()
    text = re.sub(r'[^\w\s-]', '', text)
    text = re.sub(r'[\s_]+', '-', text)
    return re.sub(r'-+', '-', text).strip('-')

# =====================================================================
#  STEP 1: Build complete title + cover map from ALL HAR files
# =====================================================================
print("=" * 60)
print("  STEP 1: BUILDING TITLE + COVER MAP FROM ALL HARs")
print("=" * 60)

# Collect series_title and cover from video_detail in all HARs
series_map = {}  # series_id -> {title, cover_url, intro, episode_cnt, vids}
api_template = None

for har_name in ['melolo1.har', 'melolo2.har', 'melolo3.har']:
    if not Path(har_name).exists():
        continue
    print(f"\n  Scanning {har_name}...")
    with open(har_name, 'r', encoding='utf-8') as f:
        har = json.load(f)
    
    for entry in har['log']['entries']:
        url = entry['request']['url']
        
        # Capture API template from video_model endpoints
        if 'multi_video_model' in url and api_template is None:
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
        
        d = data['data']
        video_datas = []
        
        if 'video_data' in d and isinstance(d['video_data'], dict):
            vd = d['video_data']
            sid = str(vd.get('series_id', '') or vd.get('series_id_str', ''))
            if sid and vd.get('video_list'):
                video_datas.append((sid, vd))
        else:
            for k, v in d.items():
                if not isinstance(v, dict):
                    continue
                vd = v.get('video_data')
                if not isinstance(vd, dict) or not vd.get('video_list'):
                    continue
                video_datas.append((k, vd))
        
        for sid, vd in video_datas:
            title = vd.get('series_title', '') or ''
            cover = vd.get('series_cover', '') or ''
            intro = vd.get('series_intro', '') or vd.get('book_name', '') or ''
            ep_cnt = vd.get('total_episode', 0) or vd.get('episode_cnt', 0) or len(vd.get('video_list', []))
            
            vids = []
            for item in vd.get('video_list', []):
                if isinstance(item, dict) and item.get('vid'):
                    vids.append({
                        'vid': str(item['vid']),
                        'index': item.get('vid_index', 0),
                    })
            
            if sid not in series_map or len(vids) > len(series_map[sid].get('vids', [])):
                series_map[sid] = {
                    'title': title or series_map.get(sid, {}).get('title', ''),
                    'cover_url': cover or series_map.get(sid, {}).get('cover_url', ''),
                    'intro': intro or series_map.get(sid, {}).get('intro', ''),
                    'episode_cnt': max(ep_cnt, series_map.get(sid, {}).get('episode_cnt', 0)),
                    'vids': vids,
                }

# Also collect book_meta for extra titles
book_meta = {}
for har_name in ['melolo1.har', 'melolo2.har', 'melolo3.har']:
    if not Path(har_name).exists():
        continue
    with open(har_name, 'r', encoding='utf-8') as f:
        har = json.load(f)
    
    for entry in har['log']['entries']:
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
                        book_meta[bid] = {
                            'title': bname,
                            'abstract': abstract,
                        }
                for v in obj.values():
                    if isinstance(v, (dict, list)):
                        _extract_books(v, depth + 1)
            elif isinstance(obj, list):
                for item in obj[:50]:
                    _extract_books(item, depth + 1)
        
        _extract_books(data)

# Merge book_meta into series_map (book_id = series_id)
for sid in series_map:
    if not series_map[sid]['title'] and sid in book_meta:
        series_map[sid]['title'] = book_meta[sid]['title']
    if not series_map[sid]['intro'] and sid in book_meta:
        series_map[sid]['intro'] = book_meta[sid].get('abstract', '')

print(f"\n  Total series found: {len(series_map)}")
for sid, info in sorted(series_map.items(), key=lambda x: -x[1]['episode_cnt']):
    t = info['title'] or f"(no title {sid[-8:]})"
    c = "✅" if info['cover_url'] else "❌"
    print(f"    {t[:50]:<52} {info['episode_cnt']:>3} eps  {len(info['vids'])} vids  Cover:{c}")

# =====================================================================
#  STEP 2: Fix titles and rename folders
# =====================================================================
print(f"\n{'='*60}")
print(f"  STEP 2: FIXING TITLES & RENAMING FOLDERS")
print(f"{'='*60}")

for d in sorted(OUTPUT_DIR.iterdir()):
    if not d.is_dir():
        continue
    meta_path = d / 'metadata.json'
    if not meta_path.exists():
        continue
    
    with open(meta_path, 'r', encoding='utf-8') as f:
        meta = json.load(f)
    
    sid = meta.get('series_id', '')
    old_title = meta.get('title', '')
    old_slug = d.name
    
    if sid in series_map and series_map[sid]['title']:
        new_title = series_map[sid]['title']
        new_slug = slugify(new_title)
        
        changed = False
        
        # Update title if empty or different
        if not old_title or old_title != new_title:
            meta['title'] = new_title
            meta['slug'] = new_slug
            changed = True
            print(f"\n  📝 Title fix: '{old_title}' → '{new_title}'")
        
        # Update description if empty
        if not meta.get('description') and series_map[sid]['intro']:
            meta['description'] = series_map[sid]['intro']
            changed = True
            print(f"     + Description added")
        
        if changed:
            with open(meta_path, 'w', encoding='utf-8') as f:
                json.dump(meta, f, indent=2, ensure_ascii=False)
        
        # Rename folder if needed
        if old_slug != new_slug and not old_slug.startswith(new_slug):
            new_dir = OUTPUT_DIR / new_slug
            if not new_dir.exists():
                d.rename(new_dir)
                print(f"     📂 Folder: '{old_slug}' → '{new_slug}'")
            else:
                print(f"     ⚠️ Cannot rename: '{new_slug}' already exists")

# =====================================================================
#  STEP 3: Download missing covers
# =====================================================================
print(f"\n{'='*60}")
print(f"  STEP 3: DOWNLOADING MISSING COVERS")
print(f"{'='*60}")

for d in sorted(OUTPUT_DIR.iterdir()):
    if not d.is_dir():
        continue
    cover_path = d / 'cover.jpg'
    if cover_path.exists() and cover_path.stat().st_size > 100:
        continue
    
    meta_path = d / 'metadata.json'
    if not meta_path.exists():
        continue
    
    with open(meta_path, 'r', encoding='utf-8') as f:
        meta = json.load(f)
    
    sid = meta.get('series_id', '')
    if sid in series_map and series_map[sid]['cover_url']:
        cover_url = series_map[sid]['cover_url']
        print(f"\n  📥 Downloading cover for {d.name}...")
        try:
            resp = requests.get(cover_url, timeout=30)
            resp.raise_for_status()
            raw = cover_path.with_suffix('.raw')
            with open(raw, 'wb') as f:
                f.write(resp.content)
            result = subprocess.run(
                ['ffmpeg', '-y', '-i', str(raw), '-q:v', '2', str(cover_path)],
                capture_output=True, timeout=30
            )
            if result.returncode == 0:
                raw.unlink(missing_ok=True)
                # Update metadata
                meta['cover'] = 'cover.jpg'
                with open(meta_path, 'w', encoding='utf-8') as f:
                    json.dump(meta, f, indent=2, ensure_ascii=False)
                print(f"     ✅ Cover saved ({cover_path.stat().st_size // 1024}KB)")
            else:
                raw.rename(cover_path)
                meta['cover'] = 'cover.jpg'
                with open(meta_path, 'w', encoding='utf-8') as f:
                    json.dump(meta, f, indent=2, ensure_ascii=False)
                print(f"     ✅ Cover saved (raw format, {cover_path.stat().st_size // 1024}KB)")
        except Exception as e:
            print(f"     ❌ Failed: {e}")
    else:
        print(f"\n  ⚠️ No cover URL available for {d.name} (series {sid})")

# =====================================================================
#  STEP 4: Re-fetch missing episodes  
# =====================================================================
print(f"\n{'='*60}")
print(f"  STEP 4: RE-FETCHING MISSING EPISODES")
print(f"{'='*60}")

if not api_template:
    print("  ❌ No API template found in HARs! Cannot re-fetch episodes.")
    sys.exit(1)

# --- Inline API functions (avoid importing auto_scraper due to stdout conflict) ---

def fetch_video_urls(api_template, vids, retry_state=None):
    url = api_template['base_url']
    headers = {}
    skip = {'accept-encoding', 'content-length', 'host', 'connection', 'content-encoding'}
    for k, v in api_template['headers'].items():
        if k.lower() not in skip:
            headers[k] = v
    body = {
        "biz_param": {"detail_page_version": 0, "device_level": 3, "need_all_video_definition": True,
                       "need_mp4_align": False, "use_os_player": False, "use_server_dns": False, "video_platform": 1024},
        "video_id": ",".join(vids)
    }
    if retry_state is None:
        retry_state = {'consecutive_fails': 0, 'current_delay': API_DELAY}
    for attempt in range(API_MAX_RETRIES + 1):
        try:
            params = dict(api_template['params'])
            params['_rticket'] = str(int(time.time() * 1000))
            resp = requests.post(url, params=params, headers=headers, json=body, timeout=30)
            if resp.status_code == 429 or resp.status_code >= 500:
                wait = min(API_BACKOFF_BASE * (2 ** attempt), API_BACKOFF_MAX)
                print(f" HTTP {resp.status_code}!", flush=True)
                print(f"      Cooldown {wait}s (attempt {attempt+1}/{API_MAX_RETRIES+1})...", end='', flush=True)
                time.sleep(wait)
                print(f" retrying", flush=True)
                continue
            data = resp.json()
            results = {}
            if isinstance(data.get('data'), dict):
                for vid, vinfo in data['data'].items():
                    if isinstance(vinfo, dict) and vinfo.get('main_url'):
                        results[vid] = {'main_url': vinfo['main_url'], 'backup_url': vinfo.get('backup_url', ''),
                                        'width': vinfo.get('video_width', 0), 'height': vinfo.get('video_height', 0)}
            if results:
                retry_state['consecutive_fails'] = 0
                retry_state['current_delay'] = max(API_DELAY, retry_state['current_delay'] * 0.8)
            else:
                retry_state['consecutive_fails'] += 1
            return results
        except (requests.exceptions.Timeout, requests.exceptions.ConnectionError):
            retry_state['consecutive_fails'] += 1
            if attempt < API_MAX_RETRIES:
                wait = min(API_BACKOFF_BASE * (2 ** attempt), API_BACKOFF_MAX)
                print(f" timeout!", flush=True)
                print(f"      Cooldown {wait}s (attempt {attempt+1}/{API_MAX_RETRIES+1})...", end='', flush=True)
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

def download_video(url, backup_url, output_path):
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

def convert_to_hls(mp4_path, output_dir):
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

dramas_to_fix = []
for d in sorted(OUTPUT_DIR.iterdir()):
    if not d.is_dir():
        continue
    meta_path = d / 'metadata.json'
    if not meta_path.exists():
        continue
    
    with open(meta_path, 'r', encoding='utf-8') as f:
        meta = json.load(f)
    
    sid = meta.get('series_id', '')
    total_eps = meta.get('total_episodes', 0)
    
    eps_dir = d / 'episodes'
    current_eps = 0
    if eps_dir.exists():
        current_eps = len([x for x in eps_dir.iterdir() if x.is_dir()])
    
    if sid in series_map and current_eps < len(series_map[sid]['vids']):
        missing = len(series_map[sid]['vids']) - current_eps
        dramas_to_fix.append({
            'dir': d,
            'sid': sid,
            'title': meta.get('title', d.name),
            'current_eps': current_eps,
            'total_eps': total_eps,
            'vids': series_map[sid]['vids'],
        })

if not dramas_to_fix:
    print("  ✅ All dramas have complete episodes!")
else:
    print(f"  Found {len(dramas_to_fix)} dramas with missing episodes:\n")
    for df in dramas_to_fix:
        print(f"    {df['title'][:45]:<47} {df['current_eps']}/{len(df['vids'])} episodes")
    
    print(f"\n  Starting re-fetch...\n")
    
    retry_state = {'consecutive_fails': 0, 'current_delay': API_DELAY}
    
    for df in dramas_to_fix:
        d = df['dir']
        eps_dir = d / 'episodes'
        eps_dir.mkdir(exist_ok=True)
        
        # Get existing episodes
        existing_eps = set()
        if eps_dir.exists():
            for ep_d in eps_dir.iterdir():
                if ep_d.is_dir() and (ep_d / 'playlist.m3u8').exists():
                    try:
                        existing_eps.add(int(ep_d.name))
                    except:
                        pass
        
        # Find which vids we still need
        missing_vids = []
        for vi in df['vids']:
            ep_num = vi['index'] + 1
            if ep_num not in existing_eps:
                missing_vids.append(vi)
        
        if not missing_vids:
            print(f"  ✅ {df['title']}: all episodes already exist")
            continue
        
        print(f"\n  {'_'*56}")
        print(f"  🔄 {df['title']}")
        print(f"     Missing: {len(missing_vids)} episodes")
        print(f"  {'_'*56}")
        
        # Fetch video URLs in batches
        vid_ids = [v['vid'] for v in missing_vids]
        video_urls = {}
        
        for batch_start in range(0, len(vid_ids), BATCH_SIZE):
            batch = vid_ids[batch_start:batch_start + BATCH_SIZE]
            batch_end = min(batch_start + BATCH_SIZE, len(vid_ids))
            
            # Check for consecutive failures
            if retry_state['consecutive_fails'] >= API_CONSECUTIVE_FAIL_THRESHOLD:
                cooldown = API_BACKOFF_BASE * 2
                print(f"    ⚠️  {retry_state['consecutive_fails']} consecutive fails — cooling down {cooldown}s...")
                time.sleep(cooldown)
                retry_state['consecutive_fails'] = 0
                retry_state['current_delay'] = API_DELAY * 3
            
            print(f"    API: ep {batch_start+1}-{batch_end}...", end='', flush=True)
            urls = fetch_video_urls(api_template, batch, retry_state)
            video_urls.update(urls)
            print(f" got {len(urls)}/{len(batch)}")
            
            if batch_end < len(vid_ids):
                time.sleep(retry_state['current_delay'])
        
        print(f"    URLs fetched: {len(video_urls)}/{len(missing_vids)}")
        
        # Download and convert
        ep_success = 0
        slug = d.name
        for vi in missing_vids:
            vid = vi['vid']
            ep_num = vi['index'] + 1
            ep_str = f"{ep_num:03d}"
            
            if vid not in video_urls:
                continue
            
            ep_dir = eps_dir / ep_str
            mp4_dir = DOWNLOAD_DIR / slug
            mp4_dir.mkdir(parents=True, exist_ok=True)
            mp4_path = mp4_dir / f"ep_{ep_str}.mp4"
            
            urls = video_urls[vid]
            print(f"    Ep {ep_num:>3}: ", end='', flush=True)
            
            if download_video(urls['main_url'], urls.get('backup_url', ''), mp4_path):
                size_mb = mp4_path.stat().st_size / 1024 / 1024
                print(f"DL {size_mb:.1f}MB -> ", end='', flush=True)
                if convert_to_hls(mp4_path, ep_dir):
                    segs = len(list(ep_dir.glob('segment_*.ts')))
                    print(f"HLS {segs} seg OK")
                    ep_success += 1
                    mp4_path.unlink(missing_ok=True)
                else:
                    print(f"HLS FAIL")
            else:
                print(f"DL FAIL")
        
        print(f"    => {df['title']}: +{ep_success} episodes recovered")
        
        # Update metadata
        meta_path = d / 'metadata.json'
        with open(meta_path, 'r', encoding='utf-8') as f:
            meta = json.load(f)
        
        # Recount episodes
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

# =====================================================================
#  FINAL REPORT
# =====================================================================
print(f"\n{'='*60}")
print(f"  REPAIR COMPLETE — FINAL STATUS")
print(f"{'='*60}")

total = 0
ok = 0
for d in sorted(OUTPUT_DIR.iterdir()):
    if not d.is_dir():
        continue
    total += 1
    meta_path = d / 'metadata.json'
    cover_path = d / 'cover.jpg'
    eps_dir = d / 'episodes'
    
    ep_count = 0
    if eps_dir.exists():
        ep_count = len([x for x in eps_dir.iterdir() if x.is_dir()])
    
    has_cover = cover_path.exists() and cover_path.stat().st_size > 100
    
    meta = {}
    if meta_path.exists():
        with open(meta_path, 'r', encoding='utf-8') as f:
            meta = json.load(f)
    
    title = meta.get('title', '')
    total_eps = meta.get('total_episodes', 0) or meta.get('captured_episodes', 0)
    
    status = "✅" if ep_count > 0 and has_cover and title else "⚠️"
    if ep_count > 0 and has_cover and title:
        ok += 1
    
    print(f"  {status} {d.name[:45]:<47} {ep_count:>3} eps  Cover:{'✅' if has_cover else '❌'}  Title:{'✅' if title else '❌'}")

print(f"\n  Total: {total} dramas | Complete: {ok} | Needs attention: {total - ok}")
