# -*- coding: utf-8 -*-
"""
Directly check/patch episodes 1-21 subtitle for drama lsr7c0n1qxnrfse46j86n88e
The drama exists (episodes keep registering to it), so we just need to 
check and patch subtitles for EP 1-26 (before fix_patuh2 started)
"""
import sys; sys.stdout.reconfigure(encoding='utf-8')
import requests, json, time, boto3, warnings
warnings.filterwarnings('ignore')
from botocore.config import Config

API_BASE  = 'https://api.shortlovers.id/api'
ADMIN_KEY = '00ca04e3e2702be565d7bf44e783255247708289bce9b2fb6187a2e117f87fd14'
ADMIN_HDR = {'x-admin-key': ADMIN_KEY, 'Content-Type': 'application/json'}

R2_ENDPOINT = 'https://a142d3b29a5d64943cb251157e25eaf3.r2.cloudflarestorage.com'
R2_KEY_ID   = '07c99c897986ea52703c1285308d5e2c'
R2_SECRET   = '44788d376ffb216e1e73784b6fe1ff1423607928898a87c50819b52cdfc12e44'
R2_BUCKET   = 'shortlovers'
R2_PUBLIC   = 'https://stream.shortlovers.id'

HEADERS = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
    'Referer': 'https://vidrama.asia/',
}

UPSTREAM_ID = '160000641860'
DRAMA_DB_ID = 'lsr7c0n1qxnrfse46j86n88e'
SLUG        = 'aku-terlahir-terlalu-patuh'

def log(msg):
    print(f"[{time.strftime('%H:%M:%S')}] {msg}", flush=True)

def get_r2():
    return boto3.client(
        's3', endpoint_url=R2_ENDPOINT,
        aws_access_key_id=R2_KEY_ID, aws_secret_access_key=R2_SECRET,
        config=Config(signature_version='s3v4'), region_name='auto'
    )

# Step 1: Get all episodes for this drama
log(f"Fetching episodes for drama {DRAMA_DB_ID}...")
r = requests.get(f'{API_BASE}/dramas/{DRAMA_DB_ID}/episodes?includeInactive=true', headers=ADMIN_HDR, timeout=30)
log(f"Episodes endpoint: {r.status_code}")

if not r.ok:
    # Try alternate endpoint
    r = requests.get(f'{API_BASE}/admin/episodes?dramaId={DRAMA_DB_ID}', headers=ADMIN_HDR, timeout=30)
    log(f"Alt endpoint: {r.status_code}")

if r.ok:
    data = r.json()
    ep_list = data if isinstance(data, list) else data.get('episodes', data.get('data', []))
    log(f"Found {len(ep_list)} episodes")
    
    # Find episodes without subtitle
    no_sub = []
    for ep in ep_list:
        ep_no  = ep.get('episodeNumber')
        ep_id  = ep.get('id')
        subs   = ep.get('subtitles', [])
        
        # Also try fetching subtitles separately
        if not subs:
            sr = requests.get(f'{API_BASE}/episodes/{ep_id}/subtitles', headers=ADMIN_HDR, timeout=10)
            if sr.ok:
                sub_data = sr.json()
                subs = sub_data if isinstance(sub_data, list) else sub_data.get('subtitles', [])
        
        has_id = any(s.get('language') == 'id' for s in subs)
        status = 'OK' if has_id else 'NO SUB'
        log(f"  EP {ep_no:02d} [{ep_id}]: {status}")
        if not has_id:
            no_sub.append({'ep_no': ep_no, 'ep_id': ep_id})
    
    log(f"\nEpisodes without subtitle: {[x['ep_no'] for x in no_sub]}")
    
    if no_sub:
        log(f"\n--- Patching {len(no_sub)} episodes ---")
        r2 = get_r2()
        
        for item in no_sub:
            ep_no  = item['ep_no']
            ep_id  = item['ep_id']
            log(f"\nPatching EP {ep_no} [{ep_id}]...")
            
            # Fetch subtitle URL from upstream
            sub_upstream = None
            for attempt in range(4):
                try:
                    url = f"https://vidrama.asia/api/idrama2/unlock/{UPSTREAM_ID}/{ep_no}?lang=id"
                    resp = requests.get(url, headers=HEADERS, verify=False, timeout=20)
                    if resp.ok:
                        ep_info = resp.json().get('target_ep_info', {})
                        all_subs = list(ep_info.get('screentext_list') or []) + list(ep_info.get('subtitle_list') or [])
                        for s in all_subs:
                            if s.get('language', '').lower() == 'id' and s.get('url'):
                                sub_upstream = s['url']
                                break
                    if sub_upstream:
                        break
                except Exception as e:
                    log(f"  Attempt {attempt+1}: {e}")
                time.sleep(3)
            
            if not sub_upstream:
                log(f"  [SKIP] No ID subtitle in upstream for EP {ep_no}")
                continue
            
            # Download and upload to R2
            sub_resp = requests.get(sub_upstream, headers=HEADERS, timeout=15, verify=False)
            if not sub_resp.ok:
                log(f"  [ERROR] Download failed: {sub_resp.status_code}")
                continue
            
            key = f"dramas/{SLUG}/ep{ep_no:03d}_id.vtt"
            r2.put_object(Bucket=R2_BUCKET, Key=key, Body=sub_resp.content, ContentType='text/vtt')
            r2_url = f"{R2_PUBLIC}/{key}"
            log(f"  Uploaded: {r2_url}")
            
            # Register in DB
            payload = {
                'language': 'id',
                'label': 'Bahasa Indonesia',
                'url': r2_url,
                'isDefault': True
            }
            pr = requests.post(f'{API_BASE}/episodes/{ep_id}/subtitles', headers=ADMIN_HDR, json=payload, timeout=15)
            if pr.ok:
                log(f"  [OK] Subtitle registered!")
            else:
                log(f"  [ERROR] Register failed: {pr.status_code} {pr.text[:100]}")
            
            time.sleep(0.5)
    
    log("\n=== PATCH COMPLETE ===")
else:
    log(f"[ERROR] Could not get episodes. Response: {r.text[:300]}")
