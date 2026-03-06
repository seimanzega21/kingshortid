#!/usr/bin/env python3
"""
Task 1: Delete 5 failed dramas from R2
Task 2: Scrape 5 specific dramas from Vidrama
"""
import boto3, os, requests, json, re, sys, subprocess, tempfile, shutil, time
from pathlib import Path
from dotenv import load_dotenv

load_dotenv()
sys.stdout.reconfigure(encoding="utf-8")

R2_ENDPOINT = os.getenv("R2_ENDPOINT")
R2_ACCESS_KEY = os.getenv("R2_ACCESS_KEY_ID")
R2_SECRET_KEY = os.getenv("R2_SECRET_ACCESS_KEY")
R2_BUCKET = os.getenv("R2_BUCKET_NAME") or "shortlovers"
R2_PUBLIC = "https://stream.shortlovers.id"
API_URL = "https://vidrama.asia/api/melolo"
BACKEND_URL = "https://api.shortlovers.id/api"

s3 = boto3.client("s3",
    endpoint_url=R2_ENDPOINT,
    aws_access_key_id=R2_ACCESS_KEY,
    aws_secret_access_key=R2_SECRET_KEY,
    region_name="auto",
)
paginator = s3.get_paginator("list_objects_v2")

def slugify(text):
    text = text.lower().strip()
    text = re.sub(r"[^\w\s-]", "", text)
    text = re.sub(r"[\s_]+", "-", text)
    return re.sub(r"-+", "-", text).strip("-")


# ============================================================
# TASK 1: Delete 5 failed dramas from R2
# ============================================================
DELETE_SLUGS = [
    "setelah-cerai-makin-baik",
    "siaran-langsung-bedah-mahadewa",
    "sistem-ajaib-dan-puncak-hidupku",
    "suara-hati-anak-angkat",
    "tabel-perkalian-sembilan",
]

print("=" * 60)
print("  TASK 1: Deleting 5 failed dramas from R2")
print("=" * 60)

for slug in DELETE_SLUGS:
    # Check both prefixes
    for prefix in [f"melolo/{slug}/", f"dramas/melolo/{slug}/"]:
        objects_to_delete = []
        for page in paginator.paginate(Bucket=R2_BUCKET, Prefix=prefix):
            for obj in page.get("Contents", []):
                objects_to_delete.append({"Key": obj["Key"]})

        if objects_to_delete:
            # Delete in batches of 1000
            for i in range(0, len(objects_to_delete), 1000):
                batch = objects_to_delete[i:i+1000]
                s3.delete_objects(Bucket=R2_BUCKET, Delete={"Objects": batch})
            print(f"  DELETED {slug} ({len(objects_to_delete)} files from {prefix})")
        else:
            pass  # Not found in this prefix

print(f"\n  Task 1 complete: {len(DELETE_SLUGS)} dramas cleaned up")


# ============================================================
# TASK 2: Scrape 5 specific dramas
# ============================================================
TARGET_DRAMAS = [
    "Naga Terjatuh, Kini Bangkit",
    "Sang Dokter Jenius",
    "Takdir Ditukar di Istana",
    "Cinta yang Bunuh Anak Kami",
    "Tak Suka Wanita, Kecuali Dia",
]

print(f"\n{'=' * 60}")
print(f"  TASK 2: Scraping 5 specific dramas")
print(f"{'=' * 60}")

# Step 1: Search for each drama on Vidrama
print(f"\n[1] Searching dramas on Vidrama API...")
found_dramas = {}
for title in TARGET_DRAMAS:
    # Search using first few words
    keywords = title.split()[:3]
    for kw in keywords:
        kw_clean = re.sub(r"[^\w]", "", kw)
        if len(kw_clean) < 2:
            continue
        try:
            r = requests.get(
                f"{API_URL}?action=search&keyword={kw_clean}&limit=50&offset=0",
                timeout=30
            )
            if r.status_code == 200:
                items = r.json().get("data", [])
                for item in items:
                    if item["title"].strip().lower() == title.strip().lower():
                        found_dramas[title] = item
                        break
                    # Fuzzy match
                    if title.lower() in item["title"].lower() or item["title"].lower() in title.lower():
                        found_dramas[title] = item
                        break
        except Exception as e:
            print(f"    Search error for '{kw_clean}': {e}")
        if title in found_dramas:
            break
        time.sleep(0.3)

    if title in found_dramas:
        print(f"  FOUND: {title} -> id={found_dramas[title]['id']}")
    else:
        print(f"  NOT FOUND: {title}")

print(f"\n  Found {len(found_dramas)}/{len(TARGET_DRAMAS)} dramas")

if not found_dramas:
    print("  No dramas found to scrape!")
    sys.exit(0)

# Step 2: Check which ones are already in R2
print(f"\n[2] Checking R2 for existing dramas...")
r2_existing = set()
for page in paginator.paginate(Bucket=R2_BUCKET, Prefix="melolo/", Delimiter="/"):
    for p in page.get("CommonPrefixes", []):
        r2_existing.add(p["Prefix"].split("/")[1])
for page in paginator.paginate(Bucket=R2_BUCKET, Prefix="dramas/melolo/", Delimiter="/"):
    for p in page.get("CommonPrefixes", []):
        r2_existing.add(p["Prefix"].split("/")[2])

# Step 3: Check which ones are already in D1
print(f"[3] Checking D1 for existing dramas...")
d1_titles = set()
try:
    r = requests.get(f"{BACKEND_URL}/dramas?limit=1000", timeout=15)
    data = r.json()
    d1_list = data if isinstance(data, list) else data.get("dramas", [])
    d1_titles = {d["title"] for d in d1_list}
except Exception as e:
    print(f"  D1 fetch error: {e}")

# Step 4: Process each found drama
TEMP_DIR = Path(tempfile.gettempdir()) / "vidrama_scrape_new"
TEMP_DIR.mkdir(exist_ok=True)

def transcode_video(input_path, output_path):
    cmd = [
        "ffmpeg", "-y", "-i", str(input_path),
        "-c:v", "libx264", "-preset", "fast", "-crf", "28",
        "-pix_fmt", "yuv420p",
        "-c:a", "aac", "-b:a", "128k", "-ac", "2",
        "-movflags", "+faststart",
        str(output_path)
    ]
    try:
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=300)
        return result.returncode == 0 and output_path.exists() and output_path.stat().st_size > 1000
    except:
        return False

stats = {"ok": 0, "skip": 0, "fail": 0, "eps": 0}

print(f"\n[4] Processing dramas...")
for title, drama in found_dramas.items():
    slug = slugify(title)
    drama_id = drama["id"]

    print(f"\n{'_' * 60}")
    print(f"  {title}")
    print(f"  Slug: {slug}")

    # Check if already in R2
    if slug in r2_existing:
        # Also check if in D1
        if title in d1_titles:
            print(f"  SKIP: Already in R2 and D1")
            stats["skip"] += 1
            continue
        else:
            print(f"  INFO: In R2 but NOT in D1 - will register only")

    # Get detail + episodes
    try:
        r = requests.get(f"{API_URL}?action=detail&id={drama_id}", timeout=30)
        if r.status_code != 200:
            print(f"  FAIL: Detail API returned {r.status_code}")
            stats["fail"] += 1
            continue
        detail = r.json().get("data", {})
    except Exception as e:
        print(f"  FAIL: Detail error: {e}")
        stats["fail"] += 1
        continue

    episodes = detail.get("episodes", [])
    genres = detail.get("genres", [])
    description = drama.get("description", "") or detail.get("description", "")

    if not episodes:
        print(f"  FAIL: No episodes found")
        stats["fail"] += 1
        continue

    total_eps = len(episodes)
    print(f"  Description: {description[:80]}...")
    print(f"  Genres: {', '.join(genres) if genres else 'none'}")
    print(f"  Episodes: {total_eps}")

    # Use dramas/melolo/ prefix for new dramas
    r2_prefix = f"dramas/melolo/{slug}"

    # Upload cover
    cover_url = drama.get("image") or drama.get("poster", "")
    cover_ok = False
    if cover_url:
        try:
            resp = requests.get(cover_url, timeout=15)
            resp.raise_for_status()
            if len(resp.content) > 100:
                s3.put_object(
                    Bucket=R2_BUCKET, Key=f"{r2_prefix}/cover.webp",
                    Body=resp.content,
                    ContentType=resp.headers.get("content-type", "image/webp")
                )
                cover_ok = True
        except:
            pass
    print(f"  Cover: {'OK' if cover_ok else 'FAIL'}")

    # Process episodes
    uploaded_eps = []
    drama_temp = TEMP_DIR / slug
    drama_temp.mkdir(exist_ok=True)

    for ep in episodes:
        ep_num = ep.get("episodeNumber", 0)
        if ep_num == 0:
            continue

        r2_key = f"{r2_prefix}/ep{ep_num:03d}.mp4"
        print(f"    Ep {ep_num:3}/{total_eps}:", end="", flush=True)

        # Get stream URL
        try:
            sr = requests.get(
                f"{API_URL}?action=stream&id={drama_id}&episode={ep_num}",
                timeout=30
            )
            if sr.status_code != 200:
                print(f" FAIL Stream API {sr.status_code}")
                time.sleep(0.5)
                continue
            stream_data = sr.json().get("data", {})
        except Exception as e:
            print(f" FAIL Stream error: {str(e)[:40]}")
            time.sleep(0.5)
            continue

        proxy_url = stream_data.get("proxyUrl", "")
        if not proxy_url:
            print(f" FAIL No proxy URL")
            time.sleep(0.5)
            continue

        # Download
        full_url = f"https://vidrama.asia{proxy_url}" if proxy_url.startswith("/") else proxy_url
        raw_path = drama_temp / f"raw_ep{ep_num:03d}.mp4"
        transcoded_path = drama_temp / f"ep{ep_num:03d}.mp4"

        try:
            resp = requests.get(full_url, timeout=120, stream=True)
            resp.raise_for_status()
            total_bytes = 0
            with open(raw_path, "wb") as f:
                for chunk in resp.iter_content(chunk_size=1024 * 1024):
                    f.write(chunk)
                    total_bytes += len(chunk)
            if total_bytes < 1000:
                print(f" FAIL tiny file")
                continue
        except Exception as e:
            print(f" FAIL DL: {str(e)[:40]}")
            time.sleep(0.5)
            continue

        raw_mb = raw_path.stat().st_size / 1024 / 1024
        print(f" DL({raw_mb:.1f}MB)", end="", flush=True)

        # Transcode
        if transcode_video(raw_path, transcoded_path):
            upload_path = transcoded_path
        else:
            upload_path = raw_path  # fallback: upload raw

        # Upload to R2
        try:
            s3.upload_file(str(upload_path), R2_BUCKET, r2_key,
                ExtraArgs={"ContentType": "video/mp4"})
            print(f" R2 OK")
            uploaded_eps.append({
                "number": ep_num,
                "videoUrl": f"{R2_PUBLIC}/{r2_key}",
                "duration": ep.get("duration", 0),
            })
        except Exception as e:
            print(f" R2 FAIL: {str(e)[:40]}")

        # Cleanup
        raw_path.unlink(missing_ok=True)
        transcoded_path.unlink(missing_ok=True)
        time.sleep(0.5)

    # Cleanup temp dir
    shutil.rmtree(drama_temp, ignore_errors=True)

    if not uploaded_eps:
        print(f"  FAIL: No episodes uploaded")
        stats["fail"] += 1
        continue

    # Register in D1
    print(f"  Registering {len(uploaded_eps)} episodes to D1...")
    try:
        payload = {
            "title": title,
            "description": description,
            "cover": f"{R2_PUBLIC}/{r2_prefix}/cover.webp",
            "provider": "melolo",
            "totalEpisodes": len(uploaded_eps),
            "isActive": True,
        }
        resp = requests.post(f"{BACKEND_URL}/dramas", json=payload, timeout=15)
        if resp.status_code not in [200, 201]:
            print(f"  Drama API error: {resp.status_code} {resp.text[:80]}")
            stats["fail"] += 1
            continue

        new_drama_id = resp.json().get("id")
        ep_ok = 0
        for ep in uploaded_eps:
            try:
                er = requests.post(f"{BACKEND_URL}/episodes", json={
                    "dramaId": new_drama_id,
                    "episodeNumber": ep["number"],
                    "videoUrl": ep["videoUrl"],
                    "duration": ep.get("duration", 0),
                }, timeout=10)
                if er.status_code in [200, 201]:
                    ep_ok += 1
            except:
                pass

        print(f"  REGISTERED: {title} (id={new_drama_id}, {ep_ok}/{len(uploaded_eps)} eps)")
        stats["ok"] += 1
        stats["eps"] += ep_ok

    except Exception as e:
        print(f"  Registration error: {e}")
        stats["fail"] += 1

# Cleanup
shutil.rmtree(TEMP_DIR, ignore_errors=True)

print(f"\n{'=' * 60}")
print(f"  DONE")
print(f"  Scraped: {stats['ok']} dramas, {stats['eps']} episodes")
print(f"  Skipped: {stats['skip']}")
print(f"  Failed: {stats['fail']}")
print(f"{'=' * 60}")
