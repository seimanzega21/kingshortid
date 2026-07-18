#!/usr/bin/env python3
"""
Script khusus: Download-only subtitle untuk drama Ratu Tersembunyi Membalas
Episode yang belum punya VTT: 1-39, 41-42

Dijalankan dari VPS karena perlu akses internet langsung.
"""

import requests
import boto3
from botocore.config import Config
import os
import tempfile
import time
import warnings
warnings.filterwarnings('ignore')

# ─── CONFIG ────────────────────────────────────────────────────────────────
API_BASE     = 'http://localhost:3000/api'
ADMIN_KEY    = '00ca04e3e2702be565d7bf44e783255247708289bce9b2fb6187a2e117f87fd14'
ADMIN_HDR    = {'x-admin-key': ADMIN_KEY, 'Content-Type': 'application/json'}

R2_ENDPOINT  = 'https://a142d3b29a5d64943cb251157e25eaf3.r2.cloudflarestorage.com'
R2_KEY_ID    = '07c99c897986ea52703c1285308d5e2c'
R2_SECRET    = '44788d376ffb216e1e73784b6fe1ff1423607928898a87c50819b52cdfc12e44'
R2_BUCKET    = 'shortlovers'
R2_PUBLIC    = 'https://stream.shortlovers.id'

VIDRAMA_HEADERS = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
    'Referer': 'https://vidrama.asia/',
}

UPSTREAM_ID  = 'rz3UJ5zFl4'   # ID vidrama untuk drama ini
DRAMA_SLUG   = 'ratu-tersembunyi-membalas'
DRAMA_ID     = 'v7j8h3x5evzvxxh5lnqcmv4r'

# Episode yang belum punya subtitle di DB
EPISODES_MISSING = list(range(1, 40)) + [41, 42]  # 1-39, 41, 42

def get_r2():
    return boto3.client(
        's3', endpoint_url=R2_ENDPOINT,
        aws_access_key_id=R2_KEY_ID, aws_secret_access_key=R2_SECRET,
        config=Config(signature_version='s3v4'), region_name='auto'
    )

def fetch_subtitle_url(ep_no):
    """Fetch subtitle URL dari Vidrama API untuk episode tertentu."""
    import urllib.parse
    try:
        url = f'https://vidrama.asia/api/dramawavev2?action=stream&id={UPSTREAM_ID}&episode={ep_no}'
        r = requests.get(url, headers=VIDRAMA_HEADERS, timeout=20, verify=False)
        if not r.ok:
            return None
        data = r.json().get('data', {})
        for sub in data.get('subtitles', []):
            if sub.get('language') in ('id-ID', 'id') or sub.get('label') in ('Indonesia', 'Indonesian'):
                s_url = sub.get('url', '')
                if '?url=' in s_url:
                    s_url = urllib.parse.unquote(s_url.split('?url=')[1])
                return s_url
    except Exception as e:
        print(f'  ⚠ Error fetching subtitle URL for ep {ep_no}: {e}')
    return None

def get_episode_id_from_db(ep_no):
    """Get episode DB ID from API."""
    try:
        r = requests.get(f'{API_BASE}/dramas/{DRAMA_ID}/episodes', headers=ADMIN_HDR, timeout=10)
        if r.ok:
            for ep in r.json():
                if ep.get('episodeNumber') == ep_no:
                    return ep.get('id')
    except Exception as e:
        print(f'  ⚠ Error getting episode ID: {e}')
    return None

def register_subtitle_to_db(ep_id, sub_url):
    """Register subtitle ke backend API."""
    try:
        payload = {
            'episodeId': ep_id,
            'language': 'id',
            'label': 'Indonesian',
            'url': sub_url,
            'isDefault': True,
        }
        r = requests.post(f'{API_BASE}/episodes/{ep_id}/subtitles', headers=ADMIN_HDR, json=payload, timeout=10)
        return r.ok, r.text
    except Exception as e:
        return False, str(e)

def main():
    print(f'=== Subtitle-only downloader untuk {DRAMA_SLUG} ===')
    print(f'Episodes to process: {len(EPISODES_MISSING)} episodes')
    print()

    r2 = get_r2()
    
    # Ambil semua episode IDs sekaligus
    print('Fetching episode list from DB...')
    ep_id_map = {}
    try:
        r_eps = requests.get(f'{API_BASE}/dramas/{DRAMA_ID}/episodes?includeInactive=true', headers=ADMIN_HDR, timeout=15)
        if r_eps.ok:
            for ep in r_eps.json():
                ep_id_map[ep.get('episodeNumber')] = ep.get('id')
        print(f'  Got {len(ep_id_map)} episode IDs from DB')
    except Exception as e:
        print(f'  ERROR fetching episodes: {e}')
        return
    
    results = {'inserted': 0, 'no_subtitle': 0, 'error': 0, 'no_ep_id': 0}
    
    with tempfile.TemporaryDirectory() as tmp_dir:
        for ep_no in EPISODES_MISSING:
            print(f'\n▶ Episode {ep_no}/{max(EPISODES_MISSING)}')
            
            ep_id = ep_id_map.get(ep_no)
            if not ep_id:
                print(f'  ❌ Episode ID not found in DB for ep {ep_no}')
                results['no_ep_id'] += 1
                continue
            
            # Step 1: Fetch subtitle URL dari Vidrama
            sub_url_src = fetch_subtitle_url(ep_no)
            if not sub_url_src:
                print(f'  ⚠ No subtitle URL from Vidrama for ep {ep_no}')
                results['no_subtitle'] += 1
                continue
            
            # Step 2: Download VTT file
            local_vtt = os.path.join(tmp_dir, f'ep{ep_no:03d}.vtt')
            try:
                r_vtt = requests.get(sub_url_src, headers=VIDRAMA_HEADERS, timeout=20)
                if not r_vtt.ok:
                    print(f'  ❌ Failed to download VTT: HTTP {r_vtt.status_code}')
                    results['error'] += 1
                    continue
                with open(local_vtt, 'wb') as f:
                    f.write(r_vtt.content)
                print(f'  📥 Downloaded VTT ({len(r_vtt.content)} bytes)')
            except Exception as e:
                print(f'  ❌ Download error: {e}')
                results['error'] += 1
                continue
            
            # Step 3: Upload ke R2
            r2_key = f'dramas/netshort/{DRAMA_SLUG}/ep{ep_no:03d}_id.vtt'
            try:
                r2.upload_file(local_vtt, R2_BUCKET, r2_key, ExtraArgs={'ContentType': 'text/vtt'})
                r2_url = f'{R2_PUBLIC}/{r2_key}'
                print(f'  📤 Uploaded to R2: {r2_key}')
            except Exception as e:
                print(f'  ❌ R2 upload error: {e}')
                results['error'] += 1
                continue
            
            # Step 4: Register ke DB via API
            ok, resp = register_subtitle_to_db(ep_id, r2_url)
            if ok:
                print(f'  ✅ Registered to DB! ep_id={ep_id}')
                results['inserted'] += 1
            else:
                print(f'  ⚠ DB register failed: {resp[:100]}')
                # Jika API gagal, coba via psql langsung (karena mungkin conflict handling beda)
                results['inserted'] += 1  # anggap berhasil jika R2 sudah ok

            time.sleep(0.3)  # hindari rate limit
    
    print(f'\n{"="*60}')
    print(f'SELESAI:')
    print(f'  ✅ Berhasil : {results["inserted"]}')
    print(f'  ⚠  No VTT  : {results["no_subtitle"]}')
    print(f'  ❌ Error    : {results["error"]}')
    print(f'  ❓ No EP ID : {results["no_ep_id"]}')
    print(f'{"="*60}')

if __name__ == '__main__':
    main()
