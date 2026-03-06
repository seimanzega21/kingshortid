#!/usr/bin/env python3
"""
REGISTER R2 DRAMAS TO DATABASE
===============================
Finds dramas in R2 that are NOT in the backend database,
verifies they have episodes (HLS or MP4), reads metadata from R2,
and registers them with proper video URLs.

Handles both:
  - MP4 episodes: melolo/{slug}/ep001.mp4
  - HLS episodes: melolo/{slug}/ep001/playlist.m3u8 (with .ts segments)

Usage:
  python register_r2_to_db.py              # Dry run (show what would be registered)
  python register_r2_to_db.py --execute    # Actually register
"""
import boto3, os, json, re, sys, requests, time
from dotenv import load_dotenv
load_dotenv()

R2_ENDPOINT = os.getenv("R2_ENDPOINT")
R2_ACCESS_KEY = os.getenv("R2_ACCESS_KEY_ID")
R2_SECRET_KEY = os.getenv("R2_SECRET_ACCESS_KEY")
R2_BUCKET = os.getenv("R2_BUCKET_NAME")
R2_PUBLIC = "https://stream.shortlovers.id"
BACKEND_URL = "http://localhost:3001/api"

s3 = boto3.client('s3',
    endpoint_url=R2_ENDPOINT,
    aws_access_key_id=R2_ACCESS_KEY,
    aws_secret_access_key=R2_SECRET_KEY)


def slugify(text):
    text = text.lower().strip()
    text = re.sub(r'[^\w\s-]', '', text)
    text = re.sub(r'[\s_]+', '-', text)
    return re.sub(r'-+', '-', text).strip('-')


def get_db_dramas():
    """Get all drama titles from backend DB."""
    try:
        r = requests.get(f"{BACKEND_URL}/dramas?limit=2000", timeout=15)
        if r.status_code == 200:
            data = r.json()
            items = data if isinstance(data, list) else data.get("dramas", [])
            return {slugify(d.get("title", "")): d for d in items}
    except Exception as e:
        print(f"  ❌ Backend error: {e}")
    return {}


def scan_r2():
    """Scan R2 and build drama info with episode details."""
    print("  Scanning R2...", flush=True)
    dramas = {}
    paginator = s3.get_paginator('list_objects_v2')
    for page in paginator.paginate(Bucket=R2_BUCKET, Prefix='melolo/'):
        for obj in page.get('Contents', []):
            key = obj['Key']
            parts = key.split('/')
            if len(parts) < 2:
                continue
            slug = parts[1]
            if not slug or slug.startswith('_'):
                continue
            if slug not in dramas:
                dramas[slug] = {
                    'mp4_eps': {},      # ep_num -> r2_key
                    'hls_eps': {},      # ep_num -> m3u8_key
                    'has_cover': False,
                    'metadata': None,
                    'meta_key': None,
                }
            # Parse episode number from key
            if key.endswith('.mp4'):
                match = re.search(r'ep(\d+)\.mp4$', key)
                if match:
                    ep_num = int(match.group(1))
                    dramas[slug]['mp4_eps'][ep_num] = key
            elif key.endswith('.m3u8') and 'ep' in key:
                match = re.search(r'ep(\d+)', key)
                if match:
                    ep_num = int(match.group(1))
                    dramas[slug]['hls_eps'][ep_num] = key
            elif 'cover' in key:
                dramas[slug]['has_cover'] = True
            elif key.endswith('metadata.json'):
                dramas[slug]['meta_key'] = key
    
    print(f"  Found {len(dramas)} drama folders in R2")
    return dramas


def get_r2_metadata(meta_key):
    """Read metadata.json from R2."""
    try:
        obj = s3.get_object(Bucket=R2_BUCKET, Key=meta_key)
        return json.loads(obj['Body'].read().decode('utf-8'))
    except:
        return None


def register_single_drama(slug, info, dry_run=True):
    """Register a single drama to the backend."""
    # Determine episode format: prefer MP4, fallback to HLS
    mp4_count = len(info['mp4_eps'])
    hls_count = len(info['hls_eps'])
    
    if mp4_count == 0 and hls_count == 0:
        return None, "no episodes"
    
    # Choose format
    if mp4_count >= hls_count:
        eps = info['mp4_eps']
        fmt = "MP4"
    else:
        eps = info['hls_eps']
        fmt = "HLS"
    
    ep_count = len(eps)
    
    # Read metadata from R2
    meta = None
    if info['meta_key']:
        meta = get_r2_metadata(info['meta_key'])
    
    # Build title from metadata or slug
    if meta and meta.get('title'):
        title = meta['title']
    else:
        # Convert slug to title case
        title = slug.replace('-', ' ').title()
    
    # Build description
    desc = ""
    if meta:
        desc = meta.get('description', '') or meta.get('desc', '') or ''
    if not desc.strip():
        desc = title
    
    # Build genres
    genres = ["Drama"]
    if meta and meta.get('genres'):
        genres = meta['genres']
    
    # Cover URL
    cover_ext = "webp"
    cover_url = f"{R2_PUBLIC}/melolo/{slug}/cover.{cover_ext}"
    
    if dry_run:
        return {
            'title': title,
            'slug': slug,
            'episodes': ep_count,
            'format': fmt,
            'cover': info['has_cover'],
        }, None
    
    # Actually register
    drama_payload = {
        "title": title,
        "description": desc.strip(),
        "cover": cover_url,
        "genres": genres,
        "status": "completed",
        "country": "China",
        "language": "Indonesia",
    }
    
    try:
        r = requests.post(f"{BACKEND_URL}/dramas", json=drama_payload, timeout=15)
        if r.status_code not in [200, 201]:
            err = r.text[:120]
            # Check if it's a duplicate title
            if "unique" in err.lower() or "already" in err.lower() or "duplicate" in err.lower():
                return None, "already exists in DB"
            return None, f"API {r.status_code}: {err}"
        
        drama_id = r.json().get("id")
        if not drama_id:
            return None, "no drama ID in response"
    except Exception as e:
        return None, f"request error: {e}"
    
    # Register episodes
    ep_fail = 0
    for ep_num in sorted(eps.keys()):
        if fmt == "MP4":
            video_url = f"{R2_PUBLIC}/{eps[ep_num]}"
        else:
            video_url = f"{R2_PUBLIC}/{eps[ep_num]}"
        
        ep_payload = {
            "dramaId": drama_id,
            "episodeNumber": ep_num,
            "title": f"Episode {ep_num}",
            "videoUrl": video_url,
            "duration": 0,
        }
        try:
            er = requests.post(f"{BACKEND_URL}/episodes", json=ep_payload, timeout=10)
            if er.status_code not in [200, 201]:
                ep_fail += 1
        except:
            ep_fail += 1
    
    result = {
        'title': title,
        'slug': slug,
        'drama_id': drama_id,
        'episodes': ep_count,
        'format': fmt,
        'ep_failures': ep_fail,
    }
    return result, None


def main():
    execute = "--execute" in sys.argv
    
    print("=" * 65)
    print("  REGISTER R2 DRAMAS TO DATABASE")
    print(f"  Mode: {'🔴 EXECUTE' if execute else '🟡 DRY RUN'}")
    print("=" * 65)
    
    # Step 1: Get current DB state
    print("\n📋 Checking database...", flush=True)
    db_dramas = get_db_dramas()
    print(f"  Database has {len(db_dramas)} dramas")
    
    # Step 2: Scan R2
    print("\n📦 Scanning R2...", flush=True)
    r2_dramas = scan_r2()
    
    # Step 3: Find unregistered dramas
    unregistered = []
    for slug, info in sorted(r2_dramas.items()):
        if slug not in db_dramas:
            ep_total = len(info['mp4_eps']) + len(info['hls_eps'])
            if ep_total > 0:
                unregistered.append((slug, info))
    
    print(f"\n  Unregistered dramas with episodes: {len(unregistered)}")
    
    if not unregistered:
        print("  Nothing to register!")
        return
    
    # Step 4: Process
    print(f"\n{'=' * 65}")
    if not execute:
        print("  DRY RUN — What would be registered:")
        print(f"{'=' * 65}")
    else:
        print("  REGISTERING...")
        print(f"{'=' * 65}")
    
    success = 0
    failed = 0
    skipped = 0
    
    for i, (slug, info) in enumerate(unregistered, 1):
        result, error = register_single_drama(slug, info, dry_run=not execute)
        
        if error:
            if "already exists" in str(error):
                skipped += 1
                print(f"  {i:3}. ⏭️  {slug} — {error}")
            else:
                failed += 1
                print(f"  {i:3}. ❌ {slug} — {error}")
        elif result:
            success += 1
            fmt = result.get('format', '?')
            ep_count = result.get('episodes', 0)
            title = result.get('title', slug)
            cover = "✅" if result.get('cover', False) or info.get('has_cover', False) else "❌"
            
            if execute:
                ep_fail = result.get('ep_failures', 0)
                fail_note = f" ({ep_fail} ep failed)" if ep_fail > 0 else ""
                print(f"  {i:3}. ✅ {title[:40]:<40} {ep_count:>3} eps [{fmt}] cover:{cover}{fail_note}")
            else:
                print(f"  {i:3}. 📋 {title[:40]:<40} {ep_count:>3} eps [{fmt}] cover:{cover}")
        
        if execute:
            time.sleep(0.2)  # Rate limit
    
    print(f"\n{'=' * 65}")
    print(f"  {'REGISTERED' if execute else 'WOULD REGISTER'}: {success}")
    print(f"  Failed: {failed}")
    print(f"  Skipped (duplicates): {skipped}")
    print(f"{'=' * 65}")
    
    if not execute:
        print(f"\n  Run with --execute to actually register these dramas.")


if __name__ == "__main__":
    main()
