#!/usr/bin/env python3
"""
Mass 540p Backfill — KingShort / ShortLovers
=============================================
Fetches ALL active episodes WITHOUT videoUrl540p from API,
downloads the 720p from R2, encodes 540p, uploads to R2, patches DB.

Features:
  - Checkpoint system: saves progress so it can auto-resume after crash
  - Skips episodes already having 540p or not on our R2
  - Logs everything to /tmp/backfill_540p.log
  - Runs as nohup background process

Usage:
  nohup python3 /tmp/backfill_540p_mass.py > /tmp/backfill_540p.log 2>&1 &
"""

import subprocess, requests, boto3, json, time, sys, os
from pathlib import Path
from botocore.config import Config

# ─── Config ─────────────────────────────────────────────────────────────────
API_BASE    = 'https://api.shortlovers.id'
ADMIN_KEY   = '00ca04e3e2702be565d7bf44e783255247708289bce9b2fb6187a2e117f87fd14'

R2_ENDPOINT = 'https://a142d3b29a5d64943cb251157e25eaf3.r2.cloudflarestorage.com'
R2_KEY_ID   = '07c99c897986ea52703c1285308d5e2c'
R2_SECRET   = '44788d376ffb216e1e73784b6fe1ff1423607928898a87c50819b52cdfc12e44'
R2_BUCKET   = 'shortlovers'
R2_PUBLIC   = 'https://stream.shortlovers.id'

TEMP_DIR        = Path('d:/kingshortid/scripts/tmp/backfill_540p_tmp')
CHECKPOINT_FILE = Path('d:/kingshortid/scripts/tmp/backfill_540p_checkpoint.json')
SKIP_FILE       = Path('d:/kingshortid/scripts/tmp/backfill_540p_skipped.json')

HEADERS = {'x-admin-key': ADMIN_KEY, 'Content-Type': 'application/json'}

TEMP_DIR.mkdir(exist_ok=True)

# ─── Helpers: R2 ─────────────────────────────────────────────────────────────
def get_r2():
    return boto3.client(
        's3', endpoint_url=R2_ENDPOINT,
        aws_access_key_id=R2_KEY_ID,
        aws_secret_access_key=R2_SECRET,
        config=Config(signature_version='s3v4'),
        region_name='auto'
    )

def r2_key_exists(r2c, key):
    """Check if a key already exists in R2 (skip re-upload)."""
    try:
        r2c.head_object(Bucket=R2_BUCKET, Key=key)
        return True
    except Exception:
        return False

def r2_upload(r2c, path, key):
    with open(path, 'rb') as f:
        r2c.upload_fileobj(
            f, R2_BUCKET, key,
            ExtraArgs={'ContentType': 'video/mp4'},
            Config=boto3.s3.transfer.TransferConfig(
                multipart_threshold=30 * 1024 * 1024,
                multipart_chunksize=10 * 1024 * 1024
            )
        )

# ─── Helpers: API ────────────────────────────────────────────────────────────
def api_get(path, params=None, retries=3):
    for attempt in range(retries):
        try:
            r = requests.get(f"{API_BASE}{path}", params=params, timeout=30)
            if r.ok:
                return r.json()
        except Exception as e:
            if attempt == retries - 1:
                raise
            time.sleep(2 ** attempt)
    return None

def fetch_all_dramas():
    """Fetch all dramas via paginated API."""
    dramas, page = [], 1
    while True:
        data = api_get('/api/dramas', {'page': page, 'limit': 100})
        if not data:
            break
        batch = data.get('dramas', data.get('data', []))
        if not batch:
            break
        dramas.extend(batch)
        total = int(data.get('total', 0))
        print(f"  Fetched page {page}: {len(batch)} dramas (total so far: {len(dramas)}/{total})")
        if len(dramas) >= total:
            break
        page += 1
        time.sleep(0.3)
    return dramas

def fetch_episodes(drama_id):
    """Fetch all episodes for a drama."""
    try:
        data = api_get(f'/api/dramas/{drama_id}/episodes')
        return data if isinstance(data, list) else []
    except Exception:
        return []

def patch_episode_540p(ep_id, url_540):
    """PATCH videoUrl540p for an episode via API."""
    try:
        r = requests.patch(
            f"{API_BASE}/api/episodes/{ep_id}",
            headers=HEADERS,
            json={"videoUrl540p": url_540},
            timeout=30
        )
        return r.ok, r.status_code
    except Exception as e:
        return False, str(e)

# ─── 540p key derivation ─────────────────────────────────────────────────────
def derive_540p_key(video_url):
    """
    Given 720p URL like:
      https://stream.shortlovers.id/drama-slug/ep001.mp4
    Returns R2 key:
      drama-slug/ep001_540p.mp4
    """
    prefix = R2_PUBLIC + '/'
    if not video_url.startswith(prefix):
        return None  # not our R2, skip
    key_720 = video_url[len(prefix):]
    if not key_720.endswith('.mp4'):
        return None
    key_540 = key_720[:-4] + '_540p.mp4'
    return key_540

# ─── Checkpoint ──────────────────────────────────────────────────────────────
def load_checkpoint():
    if CHECKPOINT_FILE.exists():
        try:
            return json.loads(CHECKPOINT_FILE.read_text())
        except Exception:
            pass
    return {'processed_ep_ids': [], 'success': 0, 'failed': 0, 'skipped': 0}

def save_checkpoint(cp):
    CHECKPOINT_FILE.write_text(json.dumps(cp))

def load_skipped():
    if SKIP_FILE.exists():
        try:
            return set(json.loads(SKIP_FILE.read_text()))
        except Exception:
            pass
    return set()

def save_skipped(skip_set):
    SKIP_FILE.write_text(json.dumps(list(skip_set)))

# ─── Core: encode + upload + patch ───────────────────────────────────────────
def process_episode(r2c, ep, drama_title, cp, skip_set):
    ep_id     = ep.get('id', '')
    ep_num    = ep.get('episodeNumber', ep.get('episode_number', 0))
    video_url = ep.get('videoUrl', ep.get('video_url', ''))
    video_540 = ep.get('videoUrl540p', ep.get('video_url_540p'))

    # Already has 540p in DB
    if video_540:
        return 'already_has_540p'

    # Not on our R2
    if R2_PUBLIC not in video_url:
        return 'not_on_r2'

    # Derive 540p key
    key_540 = derive_540p_key(video_url)
    if not key_540:
        return 'cant_derive_key'

    url_540 = f"{R2_PUBLIC}/{key_540}"
    t_540   = TEMP_DIR / f"tmp540_{ep_id[:12]}.mp4"

    try:
        # Check if 540p already exists on R2 (just missing DB record)
        if r2_key_exists(r2c, key_540):
            print(f"    -> 540p already on R2, just patching DB...")
            ok, st = patch_episode_540p(ep_id, url_540)
            if ok:
                return 'patched_existing'
            else:
                print(f"    [!] PATCH failed HTTP {st}")
                return 'patch_failed'

        # Download 720p from R2 and encode 540p
        print(f"    Encoding 540p from: {video_url[-60:]}")
        cmd = [
            'ffmpeg', '-y',
            '-i', video_url,
            '-vf', 'scale=-2:540',
            '-c:v', 'libx264', '-crf', '28', '-preset', 'fast',
            '-c:a', 'aac', '-b:a', '128k',
            '-movflags', '+faststart',
            str(t_540)
        ]
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=900)
        if result.returncode != 0 or not t_540.exists():
            print(f"    [!] ffmpeg failed: {result.stderr[-200:]}")
            return 'encode_failed'

        # Upload to R2
        r2_upload(r2c, t_540, key_540)

        # Patch DB
        ok, st = patch_episode_540p(ep_id, url_540)
        if ok:
            return 'success'
        else:
            print(f"    [!] PATCH failed HTTP {st}")
            return 'patch_failed'

    except subprocess.TimeoutExpired:
        print(f"    [!] Timeout on ep {ep_num}")
        return 'timeout'
    except Exception as e:
        print(f"    [!] Error: {e}")
        return 'error'
    finally:
        if t_540.exists():
            t_540.unlink()


# ─── Main ─────────────────────────────────────────────────────────────────────
def main():
    start_time = time.time()

    print("=" * 65)
    print("  MASS 540p BACKFILL - KingShort")
    print(f"  Started: {time.strftime('%Y-%m-%d %H:%M:%S')}")
    print("=" * 65)

    # Load checkpoint (resume support)
    cp       = load_checkpoint()
    skip_set = load_skipped()
    done_ids = set(cp.get('processed_ep_ids', []))
    print(f"\n  Checkpoint: {len(done_ids)} episodes already done")
    print(f"  Stats so far -> success: {cp['success']}, failed: {cp['failed']}, skipped: {cp['skipped']}\n")

    r2c = get_r2()

    # Fetch all dramas
    print("Fetching drama list from API...")
    dramas = fetch_all_dramas()
    print(f"Total dramas: {len(dramas)}\n")

    total_processed = 0

    for drama_idx, drama in enumerate(dramas):
        drama_id    = drama.get('id', '')
        drama_title = drama.get('title', '?')

        episodes = fetch_episodes(drama_id)
        # Only episodes without 540p
        to_process = [
            ep for ep in episodes
            if not ep.get('videoUrl540p') and not ep.get('video_url_540p')
            and ep.get('id') not in done_ids
            and ep.get('id') not in skip_set
        ]

        if not to_process:
            continue

        print(f"\n[Drama {drama_idx+1}/{len(dramas)}] {drama_title} - {len(to_process)} ep(s) need 540p")

        for ep in to_process:
            ep_id  = ep.get('id', '')
            ep_num = ep.get('episodeNumber', ep.get('episode_number', 0))
            print(f"  Ep{ep_num:03d} ({ep_id[:8]})...", end=' ', flush=True)

            result = process_episode(r2c, ep, drama_title, cp, skip_set)
            total_processed += 1

            if result == 'success':
                print("[+]")
                cp['success'] += 1
            elif result == 'patched_existing':
                print("[+] (was already on R2)")
                cp['success'] += 1
            elif result == 'already_has_540p':
                print("[>] skip (already has 540p)")
                cp['skipped'] += 1
            elif result == 'not_on_r2':
                print("[>] skip (external URL)")
                cp['skipped'] += 1
                skip_set.add(ep_id)
            elif result == 'cant_derive_key':
                print("[>] skip (can't derive key)")
                cp['skipped'] += 1
                skip_set.add(ep_id)
            else:
                print(f"[!] {result}")
                cp['failed'] += 1

            # Mark as processed & save checkpoint every 10 episodes
            done_ids.add(ep_id)
            cp['processed_ep_ids'] = list(done_ids)
            if total_processed % 10 == 0:
                save_checkpoint(cp)
                save_skipped(skip_set)
                elapsed = (time.time() - start_time) / 60
                rate    = total_processed / elapsed if elapsed > 0 else 0
                print(f"\n  -- Checkpoint: {total_processed} processed | "
                      f"[+]{cp['success']} [!]{cp['failed']} [>]{cp['skipped']} | "
                      f"{rate:.1f} ep/min | elapsed {elapsed:.0f}min --\n")

        time.sleep(0.2)  # polite rate-limiting between dramas

    # Final save
    save_checkpoint(cp)
    save_skipped(skip_set)

    elapsed = (time.time() - start_time) / 60
    print("\n" + "=" * 65)
    print("  BACKFILL COMPLETE!")
    print(f"  Total processed : {total_processed}")
    print(f"  [+] Success     : {cp['success']}")
    print(f"  [!] Failed      : {cp['failed']}")
    print(f"  [>] Skipped     : {cp['skipped']}")
    print(f"  Time elapsed    : {elapsed:.0f} min ({elapsed/60:.1f} hours)")
    print(f"  Finished: {time.strftime('%Y-%m-%d %H:%M:%S')}")
    print("=" * 65)


if __name__ == '__main__':
    main()
