#!/usr/bin/env python3
"""
fix_missing_episodes.py - Universal missing episode fixer for Netshort dramas
Usage: python fix_missing_eps_universal.py --title "Kebangkitan Raja Balap" --eps 32
       python fix_missing_eps_universal.py --title "Dikuasai Ayah Mantanku" --eps 17,18,19
       python fix_missing_eps_universal.py --title "Drama Name" --auto  (auto detect all missing)
"""
import requests, time, tempfile, subprocess, shutil, argparse
from pathlib import Path
from requests.packages.urllib3.exceptions import InsecureRequestWarning
requests.packages.urllib3.disable_warnings(InsecureRequestWarning)
import os, sys, re
from dotenv import load_dotenv
import boto3

load_dotenv('d:\\kingshortid\\scripts\\melolo-scraper\\.env')
R2_ENDPOINT = os.getenv('R2_ENDPOINT')
R2_ACCESS_KEY = os.getenv('R2_ACCESS_KEY_ID')
R2_SECRET_KEY = os.getenv('R2_SECRET_ACCESS_KEY')
R2_BUCKET = os.getenv('R2_BUCKET_NAME', 'shortlovers')
R2_PUBLIC = 'https://stream.shortlovers.id'
BACKEND_URL = 'https://api.shortlovers.id/api'
LOCAL_URL = 'http://localhost:3000/api'
ADMIN_KEY = '00ca04e3e2702be565d7bf44e783255247708289bce9b2fb6187a2e117f87fd14'
HEADERS_AUTH = {'Authorization': f'Bearer {ADMIN_KEY}'}
NETSHORT_HEADERS = {'User-Agent': 'Mozilla/5.0', 'Accept': 'application/json',
                    'Origin': 'https://vidrama.asia', 'Referer': 'https://vidrama.asia/'}
WATCH_CODE = '84C818C7FB184A62D5BC784A85E1401B'

def get_s3():
    return boto3.client('s3', endpoint_url=R2_ENDPOINT,
                        aws_access_key_id=R2_ACCESS_KEY,
                        aws_secret_access_key=R2_SECRET_KEY, region_name='auto')

def slugify(text):
    text = text.lower().strip()
    text = re.sub(r'[^\w\s-]', '', text)
    text = re.sub(r'[\s_]+', '-', text)
    return re.sub(r'-+', '-', text).strip('-')[:60]

def find_backend_drama(title_keyword):
    r = requests.get(f'{LOCAL_URL}/dramas', headers=HEADERS_AUTH,
                     params={'limit': 500, 'includeInactive': 'true'})
    dramas = r.json().get('dramas', [])
    keyword = title_keyword.lower()
    # Exact match first
    for d in dramas:
        t = d.get('title', '').lower()
        if keyword == t:
            return d
    # Partial match
    for d in dramas:
        t = d.get('title', '').lower()
        if keyword in t:
            return d
    return None

def find_netshort_id(title_keyword):
    r = requests.get('https://vidrama.asia/api/netshort/api/search',
                     headers=NETSHORT_HEADERS, params={'lang': 'in', 'q': title_keyword, 'page': 1})
    data = r.json()
    dd = (data.get('data') or {})
    for key in ['searchCodeSearchResult','searchOnCaseSearchResult','simpleSearchResult','contentInfos']:
        items = dd.get(key, [])
        if items:
            kw = title_keyword.lower()
            # Best match: all keywords present
            for it in items:
                if not isinstance(it, dict): continue
                name = (it.get('shortPlayName') or it.get('name') or '').lower()
                words = [w for w in kw.split() if len(w) > 2]
                if sum(1 for w in words if w in name) >= len(words):
                    return str(it.get('shortPlayId') or it.get('id') or ''), \
                           (it.get('shortPlayName') or it.get('name') or '')
            # Fallback: partial
            for it in items:
                if not isinstance(it, dict): continue
                name = (it.get('shortPlayName') or it.get('name') or '').lower()
                if any(w in name for w in kw.split() if len(w) > 3):
                    return str(it.get('shortPlayId') or it.get('id') or ''), \
                           (it.get('shortPlayName') or it.get('name') or '')
            break
    return None, None

def get_total_eps(netshort_drama_id):
    r = requests.get(f'https://vidrama.asia/api/netshort/api/watch/{netshort_drama_id}/1',
                     headers=NETSHORT_HEADERS, params={'lang': 'in', 'code': WATCH_CODE}, verify=False)
    data = r.json()
    if isinstance(data, dict):
        result = data.get('data', data)
        if isinstance(result, dict):
            return int(result.get('maxEps', 0))
    return 0

def process_episode(ep_num, netshort_drama_id, backend_drama_id, slug, s3, temp_dir):
    r = requests.get(f'https://vidrama.asia/api/netshort/api/watch/{netshort_drama_id}/{ep_num}',
                     headers=NETSHORT_HEADERS, params={'lang': 'in', 'code': WATCH_CODE}, verify=False)
    data = r.json()
    if not isinstance(data, dict):
        print(f'  SKIP: bad response'); return False
    result = data.get('data', data)
    if not isinstance(result, dict): result = data

    video_url = result.get('videoUrl', '')
    if not video_url: print(f'  SKIP: no video URL'); return False
    if result.get('isLocked'): print(f'  SKIP: locked'); return False

    # Download
    ep_path = temp_dir / f'ep{ep_num:03d}.mp4'
    r4 = requests.get(video_url, headers=NETSHORT_HEADERS, stream=True, timeout=180, verify=False)
    with open(ep_path, 'wb') as f:
        for chunk in r4.iter_content(8192): f.write(chunk)

    # Faststart
    fs_path = temp_dir / f'ep{ep_num:03d}_fs.mp4'
    subprocess.run(['ffmpeg', '-y', '-i', str(ep_path), '-c', 'copy', '-movflags', '+faststart', str(fs_path)],
                   capture_output=True, timeout=120)
    if fs_path.exists() and fs_path.stat().st_size > 1000:
        ep_path.unlink(missing_ok=True)
        fs_path.rename(ep_path)

    size_mb = ep_path.stat().st_size / 1024 / 1024
    r2_key = f'dramas/netshort/{slug}/ep{ep_num:03d}.mp4'
    s3.upload_file(str(ep_path), R2_BUCKET, r2_key, ExtraArgs={'ContentType': 'video/mp4'})
    ep_r2_url = f'{R2_PUBLIC}/{r2_key}'
    ep_path.unlink(missing_ok=True)

    payload = {'dramaId': backend_drama_id, 'episodeNumber': ep_num,
               'videoUrl': ep_r2_url, 'title': f'Episode {ep_num}', 'duration': 0}
    r5 = requests.post(f'{BACKEND_URL}/episodes', json=payload, timeout=30)
    if r5.status_code not in [200, 201]:
        print(f'  ❌ Register failed: {r5.status_code}'); return False
    
    ep_id = r5.json().get('id')
    print(f'  ✅ Ep {ep_num}: {size_mb:.1f}MB uploaded')

    # Subtitles
    subs = result.get('subtitles', [])
    if result.get('subtitle'): subs = [{'language': 'id_ID', 'url': result['subtitle']}]
    for sub in subs:
        sub_url = sub.get('url') or sub.get('src', '')
        sub_lang = sub.get('language', 'id_ID')
        if not sub_url: continue
        try:
            sub_path = temp_dir / f'ep{ep_num:03d}_sub_tmp'
            rs = requests.get(sub_url, headers=NETSHORT_HEADERS, stream=True, verify=False, timeout=30)
            with open(sub_path, 'wb') as f: f.write(rs.content)
            head = open(sub_path, 'r', encoding='utf-8', errors='ignore').read(20)
            ext = 'vtt' if 'WEBVTT' in head else 'srt'
            sub_final = temp_dir / f'ep{ep_num:03d}_{sub_lang}.{ext}'
            sub_path.rename(sub_final)
            sub_key = f'dramas/netshort/{slug}/subs/ep{ep_num:03d}_{sub_lang}.{ext}'
            s3.upload_file(str(sub_final), R2_BUCKET, sub_key, ExtraArgs={'ContentType': f'text/{ext}'})
            sub_r2_url = f'{R2_PUBLIC}/{sub_key}'
            sub_final.unlink(missing_ok=True)
            requests.post(f'{BACKEND_URL}/episodes/{ep_id}/subtitles',
                          json={'language': sub_lang, 'label': 'Indonesian',
                                'url': sub_r2_url, 'isDefault': 'id' in sub_lang.lower()}, timeout=15)
            print(f'     Sub ✅')
        except Exception as e:
            print(f'     Sub ⚠️ {e}')
    return True

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--title', required=True, help='Drama title keyword to search')
    parser.add_argument('--eps', type=str, help='Episode numbers to fix, e.g. "32" or "17,18,19"')
    parser.add_argument('--auto', action='store_true', help='Auto-detect all missing episodes')
    parser.add_argument('--slug', type=str, help='R2 slug (auto-generated if not provided)')
    args = parser.parse_args()

    print(f'\n=== Finding drama: {args.title} ===')
    backend_drama = find_backend_drama(args.title)
    if not backend_drama:
        print(f'ERROR: "{args.title}" not found in local backend!'); sys.exit(1)
    
    backend_id = backend_drama['id']
    backend_title = backend_drama['title']
    cover = backend_drama.get('cover', '')
    
    # Derive slug from cover URL or title
    slug = args.slug
    if not slug and 'netshort/' in cover:
        slug = cover.split('netshort/')[1].split('/')[0]
    if not slug:
        slug = slugify(backend_title.replace('(Sulih suara)', '').replace('(sulih suara)', '').strip())
    
    print(f'Backend ID: {backend_id} | Title: {backend_title} | Slug: {slug}')

    # Find Netshort ID
    netshort_id, ns_name = find_netshort_id(args.title)
    if not netshort_id:
        print(f'ERROR: Netshort ID not found for "{args.title}"!'); sys.exit(1)
    print(f'Netshort ID: {netshort_id} | Name: {ns_name}')

    # Determine missing episodes
    if args.auto:
        total_eps = get_total_eps(netshort_id)
        r = requests.get(f'{LOCAL_URL}/dramas/{backend_id}', headers=HEADERS_AUTH,
                         params={'includeInactive': 'true'})
        existing = {ep['episodeNumber'] for ep in r.json().get('episodes', [])}
        missing = [n for n in range(1, total_eps + 1) if n not in existing]
        print(f'Total: {total_eps} | Existing: {len(existing)} | Missing: {missing}')
    elif args.eps:
        missing = [int(x.strip()) for x in args.eps.split(',')]
        print(f'Fixing episodes: {missing}')
    else:
        print('ERROR: Provide --eps or --auto'); sys.exit(1)

    if not missing:
        print('No missing episodes!'); return

    s3 = get_s3()
    temp_dir = Path(tempfile.gettempdir()) / f'fix_{slug[:15]}'
    temp_dir.mkdir(exist_ok=True)

    ok, fail = 0, 0
    for ep in missing:
        try:
            success = process_episode(ep, netshort_id, backend_id, slug, s3, temp_dir)
            if success: ok += 1
            else: fail += 1
        except Exception as e:
            print(f'  ❌ Ep {ep}: {e}'); fail += 1
        time.sleep(0.5)

    shutil.rmtree(temp_dir, ignore_errors=True)
    print(f'\nDone! ✅ {ok} success | ❌ {fail} failed')

if __name__ == '__main__':
    main()
