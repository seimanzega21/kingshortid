#!/usr/bin/env python3
"""Compare R2 dramas vs D1 registered dramas for melolo provider."""
import boto3, os, requests, json
from dotenv import load_dotenv

load_dotenv()

BACKEND_URL = "https://api.shortlovers.id/api"
R2_PUBLIC = "https://stream.shortlovers.id"

# 1. Get all drama slugs from R2 (under dramas/melolo/)
print("=== Checking R2 dramas ===", flush=True)
s3 = boto3.client('s3',
    endpoint_url=os.getenv('R2_ENDPOINT'),
    aws_access_key_id=os.getenv('R2_ACCESS_KEY_ID'),
    aws_secret_access_key=os.getenv('R2_SECRET_ACCESS_KEY'),
    region_name='auto'
)

r2_dramas = {}  # slug -> list of files
paginator = s3.get_paginator('list_objects_v2')
for page in paginator.paginate(Bucket='shortlovers', Prefix='dramas/melolo/'):
    for obj in page.get('Contents', []):
        key = obj['Key']  # dramas/melolo/{slug}/ep001.mp4 or cover.webp
        parts = key.split('/')
        if len(parts) >= 4:
            slug = parts[2]
            filename = parts[3]
            if slug not in r2_dramas:
                r2_dramas[slug] = {"eps": [], "has_cover": False}
            if filename == "cover.webp":
                r2_dramas[slug]["has_cover"] = True
            elif filename.endswith(".mp4"):
                r2_dramas[slug]["eps"].append(filename)

print(f"R2: {len(r2_dramas)} drama slugs found\n", flush=True)

# 2. Get all dramas from D1 via API
print("=== Checking D1 dramas ===", flush=True)
d1_dramas = []
try:
    r = requests.get(f"{BACKEND_URL}/dramas?limit=1000", timeout=15)
    if r.status_code == 200:
        data = r.json()
        d1_dramas = data if isinstance(data, list) else data.get("dramas", [])
except Exception as e:
    print(f"ERROR fetching from D1: {e}")

print(f"D1: {len(d1_dramas)} dramas registered\n", flush=True)

# Build a set of slugs from D1 cover URLs (extract slug from cover URL)
d1_slugs = set()
d1_by_slug = {}
for d in d1_dramas:
    cover = d.get("cover", "") or ""
    # Cover format: https://stream.shortlovers.id/dramas/melolo/{slug}/cover.webp
    if "/dramas/melolo/" in cover:
        slug = cover.split("/dramas/melolo/")[1].split("/")[0]
        d1_slugs.add(slug)
        d1_by_slug[slug] = d
    # Also try matching by title slug
    title = d.get("title", "")
    provider = d.get("provider", "")
    if provider == "melolo":
        d1_by_slug[title] = d

# 3. Compare: R2 dramas NOT in D1
r2_slugs = set(r2_dramas.keys())
not_registered = r2_slugs - d1_slugs
registered = r2_slugs & d1_slugs

print("=" * 60)
print(f"  SUMMARY")
print("=" * 60)
print(f"  R2 dramas (melolo):        {len(r2_slugs)}")
print(f"  D1 registered (melolo):    {len(registered)}")
print(f"  NOT registered in D1:      {len(not_registered)}")
print("=" * 60)

if not_registered:
    print(f"\n  Dramas in R2 but NOT in D1:")
    for slug in sorted(not_registered):
        info = r2_dramas[slug]
        ep_count = len(info["eps"])
        cover = "cover OK" if info["has_cover"] else "NO cover"
        print(f"    - {slug} ({ep_count} eps, {cover})")

# 4. Also check: D1 dramas with melolo provider but NOT in R2
d1_melolo_not_in_r2 = []
for d in d1_dramas:
    if d.get("provider") == "melolo":
        cover = d.get("cover", "") or ""
        if "/dramas/melolo/" in cover:
            slug = cover.split("/dramas/melolo/")[1].split("/")[0]
            if slug not in r2_slugs:
                d1_melolo_not_in_r2.append({"title": d["title"], "slug": slug, "id": d.get("id")})

if d1_melolo_not_in_r2:
    print(f"\n  D1 dramas (melolo) but NOT in R2:")
    for d in d1_melolo_not_in_r2:
        print(f"    - {d['title']} (slug: {d['slug']}, id: {d['id']})")

# 5. Check episode count mismatches
print(f"\n  Checking episode count mismatches...")
mismatches = []
for slug in sorted(registered):
    r2_ep_count = len(r2_dramas[slug]["eps"])
    d1_info = d1_by_slug.get(slug)
    if d1_info:
        d1_total = d1_info.get("totalEpisodes", 0)
        if r2_ep_count != d1_total and d1_total > 0:
            mismatches.append({
                "slug": slug,
                "title": d1_info.get("title", slug),
                "r2_eps": r2_ep_count,
                "d1_eps": d1_total,
            })

if mismatches:
    print(f"\n  Episode count mismatches (R2 != D1):")
    for m in mismatches:
        print(f"    - {m['title']}: R2={m['r2_eps']} vs D1={m['d1_eps']}")
else:
    print("  No episode count mismatches found.")

print("\nDone!", flush=True)
