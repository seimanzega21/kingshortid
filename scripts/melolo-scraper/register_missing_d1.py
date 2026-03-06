#!/usr/bin/env python3
"""
Register R2 dramas that are missing from D1.
Reads R2 for episode files, matches metadata from vidrama_all_dramas.json,
and registers via the backend API.
"""
import boto3, os, requests, json, re, sys, time
from dotenv import load_dotenv

load_dotenv()
sys.stdout.reconfigure(encoding="utf-8")

BACKEND_URL = "https://api.shortlovers.id/api"
R2_PUBLIC_OLD = "https://stream.shortlovers.id/melolo"
R2_PUBLIC_NEW = "https://stream.shortlovers.id/dramas/melolo"

s3 = boto3.client("s3",
    endpoint_url=os.getenv("R2_ENDPOINT"),
    aws_access_key_id=os.getenv("R2_ACCESS_KEY_ID"),
    aws_secret_access_key=os.getenv("R2_SECRET_ACCESS_KEY"),
    region_name="auto",
)
paginator = s3.get_paginator("list_objects_v2")


def slugify(text):
    text = text.lower().strip()
    text = re.sub(r"[^\w\s-]", "", text)
    text = re.sub(r"[\s_]+", "-", text)
    return re.sub(r"-+", "-", text).strip("-")


# ---- 1. Load metadata from vidrama_all_dramas.json ----
print("[1/5] Loading drama metadata...", flush=True)
meta_path = os.path.join(os.path.dirname(__file__), "vidrama_all_dramas.json")
with open(meta_path, "r", encoding="utf-8") as f:
    all_meta = json.load(f)
meta_by_slug = {}
for m in all_meta:
    slug = slugify(m["title"])
    meta_by_slug[slug] = m
print(f"  Loaded {len(meta_by_slug)} drama metadata entries", flush=True)


# ---- 2. Get R2 drama slugs (both prefixes) ----
print("[2/5] Scanning R2...", flush=True)
r2_data = {}  # slug -> {prefix, eps: [filenames], has_cover}

for page in paginator.paginate(Bucket="shortlovers", Prefix="melolo/"):
    for obj in page.get("Contents", []):
        key = obj["Key"]
        parts = key.split("/")
        if len(parts) >= 3:
            slug = parts[1]
            fname = parts[2]
            if slug not in r2_data:
                r2_data[slug] = {"prefix": "melolo", "eps": [], "has_cover": False}
            if fname == "cover.webp":
                r2_data[slug]["has_cover"] = True
            elif fname.endswith(".mp4"):
                r2_data[slug]["eps"].append(fname)

for page in paginator.paginate(Bucket="shortlovers", Prefix="dramas/melolo/"):
    for obj in page.get("Contents", []):
        key = obj["Key"]
        parts = key.split("/")
        if len(parts) >= 4:
            slug = parts[2]
            fname = parts[3]
            if slug not in r2_data:
                r2_data[slug] = {"prefix": "dramas/melolo", "eps": [], "has_cover": False}
            if fname == "cover.webp":
                r2_data[slug]["has_cover"] = True
            elif fname.endswith(".mp4"):
                r2_data[slug]["eps"].append(fname)

print(f"  R2 total: {len(r2_data)} drama slugs", flush=True)


# ---- 3. Get existing D1 slugs ----
print("[3/5] Fetching D1 dramas...", flush=True)
r = requests.get(f"{BACKEND_URL}/dramas?limit=1000", timeout=15)
data = r.json()
d1_list = data if isinstance(data, list) else data.get("dramas", [])

d1_slugs = set()
for d in d1_list:
    cover = d.get("cover", "") or ""
    if "/melolo/" in cover:
        slug = cover.split("/melolo/")[-1].split("/")[0]
        d1_slugs.add(slug)

print(f"  D1 melolo slugs: {len(d1_slugs)}", flush=True)


# ---- 4. Find missing and register ----
missing = sorted(set(r2_data.keys()) - d1_slugs)
print(f"\n[4/5] Registering {len(missing)} missing dramas...\n", flush=True)

stats = {"ok": 0, "fail": 0, "eps_total": 0, "no_meta": 0}

for i, slug in enumerate(missing, 1):
    info = r2_data[slug]
    prefix = info["prefix"]
    eps = sorted(info["eps"])
    ep_count = len(eps)

    # Get metadata
    meta = meta_by_slug.get(slug)
    if not meta:
        # Try to find by partial match
        for ms, mm in meta_by_slug.items():
            if ms == slug or slug in ms or ms in slug:
                meta = mm
                break

    if not meta:
        title = slug.replace("-", " ").title()
        description = ""
        stats["no_meta"] += 1
        print(f"  [{i}/{len(missing)}] {slug} - NO METADATA (using slug as title)", flush=True)
    else:
        title = meta["title"]
        description = meta.get("description", "")

    # Build cover URL
    cover_url = f"https://stream.shortlovers.id/{prefix}/{slug}/cover.webp"

    # Register drama
    payload = {
        "title": title,
        "description": description,
        "cover": cover_url,
        "provider": "melolo",
        "totalEpisodes": ep_count,
        "isActive": True,
    }

    try:
        resp = requests.post(f"{BACKEND_URL}/dramas", json=payload, timeout=10)
        if resp.status_code not in [200, 201]:
            print(f"  [{i}/{len(missing)}] FAIL {slug}: {resp.status_code} {resp.text[:80]}", flush=True)
            stats["fail"] += 1
            continue

        drama_id = resp.json().get("id")
        print(f"  [{i}/{len(missing)}] OK {title} (id={drama_id}, {ep_count} eps)", end="", flush=True)

        # Register episodes
        ep_ok = 0
        for ep_file in eps:
            # Extract episode number from filename like ep001.mp4 or episode_1.mp4
            m = re.search(r"(\d+)", ep_file)
            if not m:
                continue
            ep_num = int(m.group(1))
            video_url = f"https://stream.shortlovers.id/{prefix}/{slug}/{ep_file}"

            ep_resp = requests.post(f"{BACKEND_URL}/episodes", json={
                "dramaId": drama_id,
                "episodeNumber": ep_num,
                "videoUrl": video_url,
                "duration": 0,
            }, timeout=10)

            if ep_resp.status_code in [200, 201]:
                ep_ok += 1

        print(f" -> {ep_ok}/{ep_count} eps registered", flush=True)
        stats["ok"] += 1
        stats["eps_total"] += ep_ok
        time.sleep(0.3)

    except Exception as e:
        print(f"  [{i}/{len(missing)}] ERROR {slug}: {e}", flush=True)
        stats["fail"] += 1

# ---- 5. Summary ----
print(f"\n{'=' * 60}", flush=True)
print(f"  DONE", flush=True)
print(f"  Registered: {stats['ok']} dramas, {stats['eps_total']} episodes", flush=True)
print(f"  Failed: {stats['fail']}", flush=True)
print(f"  No metadata (used slug as title): {stats['no_meta']}", flush=True)
print(f"{'=' * 60}", flush=True)
