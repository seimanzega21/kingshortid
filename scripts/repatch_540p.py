#!/usr/bin/env python3
"""
Re-patch all episodes whose 540p file is already on R2 but DB has null.
This fixes the root cause: the backfill ran but PATCH /api/episodes/:id didn't exist.

Deploy this to VPS: python3 /tmp/repatch_540p.py

Logic:
  1. Fetch all dramas from API
  2. For each episode WITHOUT videoUrl540p in DB:
     a. Derive the 540p R2 key from 720p URL
     b. Check if the file EXISTS on R2
     c. If yes: PATCH the episode DB with the 540p URL (no re-encoding needed!)
     d. If no: leave it (main backfill script will handle it)
"""

import sys, time, requests, boto3
from botocore.config import Config

API_BASE  = 'https://api.shortlovers.id'
ADMIN_KEY = '00ca04e3e2702be565d7bf44e783255247708289bce9b2fb6187a2e117f87fd14'
R2_ENDPOINT = 'https://a142d3b29a5d64943cb251157e25eaf3.r2.cloudflarestorage.com'
R2_KEY_ID   = '07c99c897986ea52703c1285308d5e2c'
R2_SECRET   = '44788d376ffb216e1e73784b6fe1ff1423607928898a87c50819b52cdfc12e44'
R2_BUCKET   = 'shortlovers'
R2_PUBLIC   = 'https://stream.shortlovers.id'

HEADERS = {'x-admin-key': ADMIN_KEY, 'Content-Type': 'application/json'}

def get_r2():
    return boto3.client(
        's3', endpoint_url=R2_ENDPOINT,
        aws_access_key_id=R2_KEY_ID,
        aws_secret_access_key=R2_SECRET,
        config=Config(signature_version='s3v4'),
        region_name='auto'
    )

def r2_exists(r2c, key):
    try:
        r2c.head_object(Bucket=R2_BUCKET, Key=key)
        return True
    except Exception:
        return False

def patch_540p(ep_id, url_540):
    try:
        r = requests.patch(
            f"{API_BASE}/api/episodes/{ep_id}",
            headers=HEADERS,
            json={"videoUrl540p": url_540},
            timeout=15
        )
        return r.ok, r.status_code
    except Exception as e:
        return False, str(e)

def derive_540_key(video_url):
    prefix = R2_PUBLIC + '/'
    if not video_url.startswith(prefix):
        return None
    key_720 = video_url[len(prefix):]
    if not key_720.endswith('.mp4'):
        return None
    return key_720[:-4] + '_540p.mp4'

def main():
    print("="*60)
    print("RE-PATCH 540p: Fix episodes where R2 has file but DB is null")
    print("="*60)

    r2c = get_r2()
    patched = skipped = no_r2 = errors = 0
    page = 1

    while True:
        try:
            resp = requests.get(f"{API_BASE}/api/dramas", params={'page': page, 'limit': 100}, timeout=20)
            data = resp.json()
        except Exception as e:
            print(f"Error fetching dramas page {page}: {e}")
            break

        dramas = data.get('dramas', [])
        if not dramas:
            break
        total = data.get('total', 0)
        print(f"\nPage {page}: {len(dramas)} dramas (total: {total})")

        for drama in dramas:
            drama_id = drama['id']
            title = drama.get('title', '?')

            try:
                eps_resp = requests.get(f"{API_BASE}/api/dramas/{drama_id}/episodes", timeout=15)
                episodes = eps_resp.json() if eps_resp.ok else []
            except Exception:
                continue

            # Only episodes without 540p
            missing = [ep for ep in episodes if not ep.get('videoUrl540p')]
            if not missing:
                continue

            print(f"  {title}: {len(missing)} ep(s) missing 540p")

            for ep in missing:
                ep_id = ep['id']
                video_url = ep.get('videoUrl', '')
                ep_num = ep.get('episodeNumber', '?')

                key_540 = derive_540_key(video_url)
                if not key_540:
                    skipped += 1
                    continue

                if not r2_exists(r2c, key_540):
                    no_r2 += 1
                    continue  # file not on R2 yet

                url_540 = f"{R2_PUBLIC}/{key_540}"
                ok, status = patch_540p(ep_id, url_540)

                if ok:
                    patched += 1
                    print(f"    ✅ Ep{ep_num} patched")
                else:
                    errors += 1
                    print(f"    ❌ Ep{ep_num} PATCH failed: {status}")

                time.sleep(0.05)

        page += 1
        if len(dramas) * page > total + 100:
            break
        time.sleep(0.3)

    print(f"\n{'='*60}")
    print(f"DONE! Patched: {patched}, No R2 file: {no_r2}, Errors: {errors}, Skipped: {skipped}")
    print(f"Episodes now with 540p in DB: {patched}")
    print(f"{'='*60}")

if __name__ == '__main__':
    main()
