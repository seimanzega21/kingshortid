#!/usr/bin/env python3
"""
Register microdrama/ R2 dramas into D1.
Fixed: use Vidrama API cover URL when R2 cover is not accessible.
"""
import boto3, os, re, sys, json, requests, time
from dotenv import load_dotenv

load_dotenv()
sys.stdout.reconfigure(encoding="utf-8")

R2_PUBLIC   = "https://stream.shortlovers.id"
R2_BUCKET   = os.getenv("R2_BUCKET_NAME") or "shortlovers"
R2_PREFIX   = "microdrama"
BACKEND_URL = "https://api.shortlovers.id/api"
API_URL     = "https://vidrama.asia/api/microdrama"

s3 = boto3.client("s3",
    endpoint_url=os.getenv("R2_ENDPOINT"),
    aws_access_key_id=os.getenv("R2_ACCESS_KEY_ID"),
    aws_secret_access_key=os.getenv("R2_SECRET_ACCESS_KEY"),
    region_name="auto",
)

def slugify(text):
    text = text.lower().strip()
    text = re.sub(r"[^\w\s-]", "", text)
    text = re.sub(r"[\s_]+", "-", text)
    return re.sub(r"-+", "-", text).strip("-")

def is_url_accessible(url):
    try:
        r = requests.head(url, timeout=5, allow_redirects=True)
        return r.status_code == 200
    except:
        return False

# ── Step 1: Scan R2 ──
print("[1] Scanning R2 microdrama/ ...")
pag = s3.get_paginator("list_objects_v2")
drama_episodes = {}
for pg in pag.paginate(Bucket=R2_BUCKET, Prefix=f"{R2_PREFIX}/"):
    for obj in pg.get("Contents", []):
        key = obj["Key"]
        parts = key.split("/")
        if len(parts) < 3: continue
        slug, filename = parts[1], parts[2]
        if filename.startswith("ep") and filename.endswith(".mp4"):
            m = re.match(r"ep(\d+)\.mp4", filename)
            if m:
                ep_num = int(m.group(1))
                drama_episodes.setdefault(slug, []).append((ep_num, key))

for slug in drama_episodes:
    drama_episodes[slug].sort(key=lambda x: x[0])
print(f"    {len(drama_episodes)} dramas found")

# ── Step 2: Load D1 existing ──
print("[2] Loading D1 dramas...")
r = requests.get(f"{BACKEND_URL}/dramas?limit=1000", timeout=15)
d1_data = r.json()
items = d1_data if isinstance(d1_data, list) else d1_data.get("dramas", d1_data.get("data", []))
d1_titles = {d["title"] for d in items}
print(f"    D1 has {len(d1_titles)} dramas")

# ── Step 3: Load Vidrama API metadata (use cached JSON if available) ──
print("[3] Loading Vidrama API metadata...")
cache_file = "microdrama_id_dramas.json"
if os.path.exists(cache_file):
    with open(cache_file, encoding="utf-8") as f:
        api_list = json.load(f)
    print(f"    Loaded {len(api_list)} from cache")
else:
    api_list = []
    page = 0
    while True:
        r2 = requests.get(f"{API_URL}?action=list&lang=id&limit=50&offset={page * 50}", timeout=15)
        data = r2.json()
        dramas = data.get("dramas", [])
        if not dramas: break
        api_list.extend(dramas)
        if len(api_list) >= data.get("total", 9999): break
        page += 1
        time.sleep(0.2)
    print(f"    Loaded {len(api_list)} from API")

api_by_slug = {slugify(d["title"]): d for d in api_list}

# ── Step 4: Register ──
print("\n[4] Registering dramas...\n")
stats = {"ok": 0, "skip": 0, "fail": 0, "eps": 0}

for slug, ep_list in sorted(drama_episodes.items()):
    # Get metadata
    api_info = api_by_slug.get(slug, {})
    title = api_info.get("title", slug.replace("-", " ").title())
    desc  = api_info.get("description", "")

    if title in d1_titles:
        print(f"SKIP (exists): {title}")
        stats["skip"] += 1
        continue

    # Determine best cover URL
    r2_cover = f"{R2_PUBLIC}/{R2_PREFIX}/{slug}/cover.webp"
    api_cover = api_info.get("cover", "")

    # Backend checks accessibility — test which one works
    if is_url_accessible(r2_cover):
        cover = r2_cover
        cover_src = "R2"
    elif api_cover and is_url_accessible(api_cover):
        cover = api_cover
        cover_src = "Vidrama"
    elif api_cover:
        cover = api_cover  # try anyway
        cover_src = "Vidrama(unverified)"
    else:
        cover = r2_cover
        cover_src = "R2(unverified)"

    print(f"\nRegister: {title} ({len(ep_list)} eps, cover={cover_src})")

    try:
        resp = requests.post(f"{BACKEND_URL}/dramas", json={
            "title": title,
            "description": desc,
            "cover": cover,
            "provider": "microdrama",
            "totalEpisodes": len(ep_list),
            "isActive": True,
        }, timeout=15)

        if resp.status_code not in [200, 201]:
            print(f"  FAIL {resp.status_code}: {resp.text[:100]}")
            stats["fail"] += 1
            continue

        drama_id = resp.json().get("id")
        print(f"  Drama created: id={drama_id}")

        ep_ok = 0
        for ep_num, r2_key in ep_list:
            er = requests.post(f"{BACKEND_URL}/episodes", json={
                "dramaId": drama_id,
                "episodeNumber": ep_num,
                "videoUrl": f"{R2_PUBLIC}/{r2_key}",
                "duration": 0,
            }, timeout=10)
            if er.status_code in [200, 201]:
                ep_ok += 1
            time.sleep(0.03)

        print(f"  Episodes: {ep_ok}/{len(ep_list)} OK")
        stats["ok"] += 1
        stats["eps"] += ep_ok
        d1_titles.add(title)

    except Exception as e:
        print(f"  Exception: {e}")
        stats["fail"] += 1

    time.sleep(0.2)

print(f"\n{'='*55}")
print(f"  Registered: {stats['ok']} dramas, {stats['eps']} episodes")
print(f"  Skipped:    {stats['skip']}")
print(f"  Failed:     {stats['fail']}")
print(f"{'='*55}")
