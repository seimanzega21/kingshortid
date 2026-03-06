#!/usr/bin/env python3
"""
Fix missing episodes for ALL dramas.
Scans DB dramas, compares with R2, and registers any missing episodes.
Handles 429 rate-limits with exponential backoff.
"""
import requests, boto3, os, json, time, re
from dotenv import load_dotenv
load_dotenv()

API = "http://localhost:3001/api"
R2_PUBLIC = "https://stream.shortlovers.id"
R2_BUCKET = os.getenv("R2_BUCKET_NAME")

s3 = boto3.client("s3",
    endpoint_url=os.getenv("R2_ENDPOINT"),
    aws_access_key_id=os.getenv("R2_ACCESS_KEY_ID"),
    aws_secret_access_key=os.getenv("R2_SECRET_ACCESS_KEY"))


def get_r2_episodes(slug):
    prefix = f"melolo/{slug}/"
    eps = []
    paginator = s3.get_paginator("list_objects_v2")
    for page in paginator.paginate(Bucket=R2_BUCKET, Prefix=prefix):
        for obj in page.get("Contents", []):
            name = obj["Key"].split("/")[-1]
            m = re.match(r"ep(\d+)\.mp4", name)
            if m:
                eps.append(int(m.group(1)))
    return sorted(eps)


def get_db_episodes(drama_id):
    r = requests.get(f"{API}/dramas/{drama_id}")
    d = r.json()
    eps = d.get("episodes", [])
    return sorted([e["episodeNumber"] for e in eps])


def register_episode_with_retry(payload, max_retries=5):
    """Register a single episode with retry on 429."""
    for attempt in range(max_retries):
        try:
            r = requests.post(f"{API}/episodes", json=payload, timeout=15)
            if r.status_code in [200, 201]:
                return True
            if r.status_code == 429:
                wait = min(2 ** attempt * 2, 30)  # 2, 4, 8, 16, 30s
                time.sleep(wait)
                continue
            # Other error
            return False
        except Exception:
            time.sleep(2)
    return False


def register_missing(drama_id, slug, missing_eps):
    ok = 0
    fail = 0
    batch_size = 10

    for i, ep_num in enumerate(missing_eps):
        payload = {
            "dramaId": drama_id,
            "episodeNumber": ep_num,
            "title": f"Episode {ep_num}",
            "videoUrl": f"{R2_PUBLIC}/melolo/{slug}/ep{ep_num:03d}.mp4",
            "duration": 0,
        }
        
        if register_episode_with_retry(payload):
            ok += 1
        else:
            print(f"    EP{ep_num} failed after retries")
            fail += 1

        # Slow down: 0.3s per episode, extra pause every batch
        time.sleep(0.3)
        if (i + 1) % batch_size == 0:
            time.sleep(1)

    return ok, fail


def update_total_episodes(drama_id, total):
    for attempt in range(3):
        try:
            r = requests.patch(f"{API}/dramas/{drama_id}",
                json={"totalEpisodes": total}, timeout=10)
            if r.status_code in [200, 201]:
                return True
            if r.status_code == 429:
                time.sleep(3)
                continue
        except:
            time.sleep(2)
    return False


def fix_drama(drama_id, slug, title):
    r2_eps = get_r2_episodes(slug)
    if not r2_eps:
        return 0

    db_eps = get_db_episodes(drama_id)
    missing = [e for e in r2_eps if e not in db_eps]

    if not missing:
        return 0

    print(f"\n{'─' * 60}")
    print(f"  {title}")
    print(f"  R2: {len(r2_eps)} eps | DB: {len(db_eps)} eps | Missing: {len(missing)}")

    ok, fail = register_missing(drama_id, slug, missing)
    print(f"  Registered: {ok} ✅ | Failed: {fail} ❌")

    # Update totalEpisodes to match R2
    if update_total_episodes(drama_id, len(r2_eps)):
        print(f"  Updated totalEpisodes → {len(r2_eps)}")

    return ok


# ─── MAIN ────────────────────────────────────────────────────────

print("=" * 60)
print("  FIXING MISSING EPISODES IN DB (with rate-limit handling)")
print("=" * 60)

# Get ALL dramas from DB
page_num = 1
all_dramas = []
while True:
    r = requests.get(f"{API}/dramas?page={page_num}&limit=50")
    data = r.json()
    dramas = data.get("dramas", [])
    if not dramas:
        break
    all_dramas.extend(dramas)
    if page_num * 50 >= data.get("total", 0):
        break
    page_num += 1

print(f"\n  Total dramas in DB: {len(all_dramas)}")

total_fixed = 0
dramas_fixed = 0

for idx, d in enumerate(all_dramas, 1):
    drama_id = d["id"]
    title = d["title"]
    cover = d.get("cover", "")
    if "/melolo/" in cover:
        slug = cover.split("/melolo/")[1].split("/")[0]
    else:
        slug = re.sub(r'[^\w\s-]', '', title.lower().strip())
        slug = re.sub(r'[\s_]+', '-', slug)
        slug = re.sub(r'-+', '-', slug).strip('-')

    fixed = fix_drama(drama_id, slug, title)
    if fixed > 0:
        total_fixed += fixed
        dramas_fixed += 1

    # Progress every 50 dramas
    if idx % 50 == 0:
        print(f"\n  📊 Progress: {idx}/{len(all_dramas)} checked, {dramas_fixed} fixed so far")

print(f"\n{'=' * 60}")
print(f"  DONE!")
print(f"  Fixed {dramas_fixed} dramas, registered {total_fixed} new episodes")
print(f"{'=' * 60}")
