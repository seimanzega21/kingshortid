#!/usr/bin/env python3
"""
Check which dramas/microdrama/ slugs are in R2 (HLS-complete)
vs which are registered in D1. Register any missing ones.
"""
import boto3, os, re, sys, requests, json, time
from dotenv import load_dotenv

load_dotenv()
sys.stdout.reconfigure(encoding="utf-8")

R2_PUBLIC   = "https://stream.shortlovers.id"
R2_BUCKET   = os.getenv("R2_BUCKET_NAME") or "shortlovers"
HLS_PREFIX  = "dramas/microdrama"
BACKEND_URL = "https://api.shortlovers.id/api"

s3 = boto3.client("s3",
    endpoint_url=os.getenv("R2_ENDPOINT"),
    aws_access_key_id=os.getenv("R2_ACCESS_KEY_ID"),
    aws_secret_access_key=os.getenv("R2_SECRET_ACCESS_KEY"),
    region_name="auto",
)
pag = s3.get_paginator("list_objects_v2")

# 1. Find completed drama slugs in dramas/microdrama/ (those with ep001/index.m3u8)
print("[1] Scanning dramas/microdrama/ HLS content...")
completed_slugs = set()
ep_map = {}  # slug -> [(ep_num, m3u8_url)]

for pg in pag.paginate(Bucket=R2_BUCKET, Prefix=f"{HLS_PREFIX}/"):
    for obj in pg.get("Contents", []):
        key = obj["Key"]
        # dramas/microdrama/{slug}/ep{NNN}/index.m3u8
        parts = key.split("/")
        if len(parts) == 5 and parts[-1] == "index.m3u8":
            slug = parts[2]
            ep_dir = parts[3]  # ep001, ep002...
            m = re.match(r"ep(\d+)", ep_dir)
            if m:
                ep_num = int(m.group(1))
                ep_map.setdefault(slug, []).append((ep_num, f"{R2_PUBLIC}/{key}"))
                completed_slugs.add(slug)

for slug in ep_map:
    ep_map[slug].sort(key=lambda x: x[0])

print(f"    Completed dramas in R2 (HLS): {len(completed_slugs)}")
for slug in sorted(completed_slugs):
    print(f"    {slug}: {len(ep_map[slug])} eps")

# 2. Check D1 for these dramas
print("\n[2] Fetching D1 dramas...")
r = requests.get(f"{BACKEND_URL}/dramas?limit=1000", timeout=15)
data = r.json()
items = data if isinstance(data, list) else data.get("dramas", data.get("data", []))
print(f"    Total D1: {len(items)}")
if items:
    print(f"    Schema keys: {list(items[0].keys())[:10]}")

# Build lookup: title -> drama
d1_by_title = {d["title"]: d for d in items}

# Check D1 by cover URL pattern  
d1_hls_slugs = set()
for d in items:
    cover = d.get("cover", "") or ""
    if "dramas/microdrama/" in cover:
        slug = cover.split("dramas/microdrama/")[-1].split("/")[0]
        d1_hls_slugs.add(slug)

print(f"    D1 dramas with dramas/microdrama/ cover: {len(d1_hls_slugs)}")

# 3. Load API metadata cache
print("\n[3] Loading drama metadata...")
cache = "microdrama_id_dramas.json"
if os.path.exists(cache):
    with open(cache, encoding="utf-8") as f:
        api_list = json.load(f)
    api_by_slug = {}
    for d in api_list:
        slug = d["title"].lower().strip()
        slug = re.sub(r"[^\w\s-]", "", slug)
        slug = re.sub(r"[\s_]+", "-", slug)
        slug = re.sub(r"-+", "-", slug).strip("-")
        api_by_slug[slug] = d
    print(f"    Loaded {len(api_by_slug)} from cache")
else:
    api_by_slug = {}
    print("    No cache found")

# 4. Register missing
missing = completed_slugs - d1_hls_slugs
print(f"\n[4] Missing from D1: {len(missing)}")

if not missing:
    print("    All HLS dramas already in D1!")
    sys.exit(0)

for slug in sorted(missing):
    eps = ep_map[slug]
    api_info = api_by_slug.get(slug, {})
    title = api_info.get("title", slug.replace("-", " ").title())
    desc  = api_info.get("description", "")
    cover_r2  = f"{R2_PUBLIC}/{HLS_PREFIX}/{slug}/cover.webp"
    cover_api = api_info.get("cover", "")

    # Try R2 cover, then API cover
    try:
        cr = requests.head(cover_r2, timeout=5)
        cover = cover_r2 if cr.status_code == 200 else (cover_api or cover_r2)
    except:
        cover = cover_api or cover_r2

    if title in d1_by_title:
        print(f"  SKIP (title exists): {title}")
        continue

    print(f"\n  Register: {title} ({len(eps)} eps)")
    try:
        resp = requests.post(f"{BACKEND_URL}/dramas", json={
            "title": title,
            "description": desc,
            "cover": cover,
            "provider": "microdrama",
            "totalEpisodes": len(eps),
            "isActive": True,
        }, timeout=15)

        if resp.status_code not in [200, 201]:
            print(f"    FAIL {resp.status_code}: {resp.text[:100]}")
            continue

        drama_id = resp.json().get("id")
        ep_ok = 0
        for ep_num, m3u8_url in eps:
            er = requests.post(f"{BACKEND_URL}/episodes", json={
                "dramaId": drama_id,
                "episodeNumber": ep_num,
                "videoUrl": m3u8_url,
                "duration": 0,
            }, timeout=10)
            if er.status_code in [200, 201]:
                ep_ok += 1
            time.sleep(0.03)

        print(f"    OK: id={drama_id}, {ep_ok}/{len(eps)} eps")
        d1_by_title[title] = {"id": drama_id}

    except Exception as e:
        print(f"    Error: {e}")
    time.sleep(0.2)

print("\nDone.")
