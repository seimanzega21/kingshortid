# -*- coding: utf-8 -*-
"""
Patch subtitles for EP 1-21 of Aku Terlahir Terlalu Patuh
All episodes exist in DB but have NO subtitle registered.
This script fetches ID subtitle from upstream and registers it.
"""
import sys
sys.stdout.reconfigure(encoding='utf-8')
import requests
import boto3
import time
import warnings
warnings.filterwarnings('ignore')
from botocore.config import Config

API_BASE    = 'https://api.shortlovers.id/api'
ADMIN_KEY   = '00ca04e3e2702be565d7bf44e783255247708289bce9b2fb6187a2e117f87fd14'
ADMIN_HDR   = {'x-admin-key': ADMIN_KEY, 'Content-Type': 'application/json'}

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
SLUG        = 'aku-terlahir-terlalu-patuh'

# EP number -> DB episode ID (from audit above)
EPISODES_NO_SUB = {
    1:  'ntrj7uc8lujxbuo7ngjrmv76',
    2:  'sgqnqrdxz5l9fuvx2rkg6s7s',
    3:  'z1k0b2wfq3v8t00fpw83yk2h',
    4:  'mgjq3k4wf2oi2o74cwtahq5u',
    5:  'ynq7ej16s6dqbzqt1eoiz2e0',
    6:  'kqk2t0hswt0m87bvq1h0kdni',
    7:  'v9vc3q3bfq83n2tz1l6p60p9',
    8:  'dklzlpbisrxo6g1e5ezdnb1d',
    9:  'vb2zjyq5ettnqj9hg3p7nlba',
    10: 'hq7s4rkujfm6qvg8xmb4iwnr',
    11: 'ue0tkqcmkfuklvt7bsasp9a0',
    12: 'vy4j7dq0nkfui7r5jtirq52q',
    13: 'a0skg1bfap6m3f7bw8xaoxl1',
    14: 'fk5d14b6v4eknbfbm1xzpmb2',
    15: 'yap6q1mcs4w6kw4vmqq4gkx6',
    16: 'c6nit0kj7oyvzr23o8bqsqcd',
    17: 'hbmzlnj6e28v1n8lrox7jat7',
    18: '5qxhj4gp2x2lsb7r0bsxrqlm',
    19: 'uu11p6bfpfqdixoq2jjhbf3x',
    20: 'bpbih86kvafmpf05gqfpkq0h',
    21: '3h2g4vbhhx5kjyspibq6nol0',
}

def log(msg):
    ts = time.strftime('%H:%M:%S')
    print(f"[{ts}] {msg}", flush=True)

def get_r2():
    return boto3.client(
        's3', endpoint_url=R2_ENDPOINT,
        aws_access_key_id=R2_KEY_ID, aws_secret_access_key=R2_SECRET,
        config=Config(signature_version='s3v4'), region_name='auto'
    )

def fetch_id_subtitle_url(ep_no, retries=4):
    """Fetch Indonesian subtitle URL from upstream unlock API"""
    for attempt in range(retries):
        try:
            url = f"https://vidrama.asia/api/idrama2/unlock/{UPSTREAM_ID}/{ep_no}?lang=id"
            resp = requests.get(url, headers=HEADERS, verify=False, timeout=20)
            if resp.ok:
                ep_info = resp.json().get('target_ep_info', {})
                all_subs = list(ep_info.get('screentext_list') or []) + list(ep_info.get('subtitle_list') or [])
                for s in all_subs:
                    if s.get('language', '').lower() == 'id' and s.get('url'):
                        return s['url']
        except Exception as e:
            log(f"  Attempt {attempt+1} error: {e}")
        time.sleep(3)
    return None

def upload_subtitle_to_r2(r2, sub_url, ep_no):
    """Download subtitle and upload to R2"""
    resp = requests.get(sub_url, headers=HEADERS, timeout=15, verify=False)
    if not resp.ok:
        return None
    key = f"dramas/{SLUG}/ep{ep_no:03d}_id.vtt"
    r2.put_object(Bucket=R2_BUCKET, Key=key, Body=resp.content, ContentType='text/vtt')
    return f"{R2_PUBLIC}/{key}"

def register_subtitle_to_db(ep_db_id, sub_r2_url):
    """POST subtitle record to DB"""
    payload = {
        'language': 'id',
        'label': 'Bahasa Indonesia',
        'url': sub_r2_url,
        'isDefault': True
    }
    r = requests.post(
        f"{API_BASE}/episodes/{ep_db_id}/subtitles",
        headers=ADMIN_HDR, json=payload, timeout=15
    )
    return r.ok, r.status_code, r.text[:100] if not r.ok else ''

def main():
    log("=" * 55)
    log("PATCH SUBTITLES: Aku Terlahir Terlalu Patuh EP 1-21")
    log("=" * 55)

    r2 = get_r2()
    success = 0
    failed  = []

    for ep_no, ep_db_id in sorted(EPISODES_NO_SUB.items()):
        log(f"\nEP {ep_no:02d} (DB: {ep_db_id})")

        # Step 1: Get ID subtitle URL from upstream
        sub_upstream = fetch_id_subtitle_url(ep_no)
        if not sub_upstream:
            log(f"  [ERROR] No ID subtitle found in upstream for EP {ep_no}")
            failed.append(ep_no)
            continue
        log(f"  Subtitle URL: {sub_upstream[:70]}...")

        # Step 2: Upload to R2
        r2_url = upload_subtitle_to_r2(r2, sub_upstream, ep_no)
        if not r2_url:
            log(f"  [ERROR] Upload to R2 failed")
            failed.append(ep_no)
            continue
        log(f"  R2 URL: {r2_url}")

        # Step 3: Register in DB
        ok, status, body = register_subtitle_to_db(ep_db_id, r2_url)
        if ok:
            log(f"  [OK] Subtitle registered successfully!")
            success += 1
        else:
            log(f"  [ERROR] DB registration failed. Status={status}, Body={body}")
            failed.append(ep_no)

        time.sleep(0.5)

    log("\n" + "=" * 55)
    log(f"DONE! Success: {success}/21")
    if failed:
        log(f"Failed episodes: {failed}")
    else:
        log("All 21 episodes patched successfully!")
    log("=" * 55)

if __name__ == '__main__':
    main()
