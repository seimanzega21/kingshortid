#!/usr/bin/env python3
"""
Resume scraping Dimanja Habis-habisan Oleh Bos from episode 39 to 102.
Downloads MP4 → FFmpeg transcode → R2 upload → Register episode in DB.
"""
import requests, json, time, os, subprocess, tempfile, shutil
from pathlib import Path
from dotenv import load_dotenv
import boto3
load_dotenv()

# Config
R2_ENDPOINT = os.getenv("R2_ENDPOINT")
R2_ACCESS_KEY = os.getenv("R2_ACCESS_KEY_ID")
R2_SECRET_KEY = os.getenv("R2_SECRET_ACCESS_KEY")
R2_BUCKET = os.getenv("R2_BUCKET_NAME")
R2_PUBLIC = "https://stream.shortlovers.id"
API_URL = "https://vidrama.asia/api/melolo"
TEMP_DIR = Path(tempfile.gettempdir()) / "vidrama_scrape"
TEMP_DIR.mkdir(exist_ok=True)

s3 = boto3.client("s3", endpoint_url=R2_ENDPOINT,
    aws_access_key_id=R2_ACCESS_KEY, aws_secret_access_key=R2_SECRET_KEY)

# Drama info
SLUG = "dimanja-habis-habisan-oleh-bos"
START_EP = 39
END_EP = 102

# First, find the drama ID on Vidrama
print("Finding drama on Vidrama...")
r = requests.get(f"{API_URL}?action=search&keyword=Dimanja Habis&limit=10", timeout=15)
drama_id = None
for d in r.json().get("data", []):
    if "dimanja" in d["title"].lower():
        drama_id = d["id"]
        print(f"  Found: {d['title']} (id={drama_id})")
        break

if not drama_id:
    print("Drama not found on Vidrama!")
    exit(1)

# Get the DB drama ID for episode registration
import subprocess as sp
result = sp.run(["node", "-e", f"""
const {{PrismaClient}} = require('@prisma/client');
const p = new PrismaClient();
p.drama.findFirst({{where:{{title:{{contains:'Dimanja'}}}}}}).then(d=>{{
    process.stdout.write(d ? d.id : 'NULL');
    p.$disconnect();
}});
"""], capture_output=True, text=True, cwd=r"D:\kingshortid\admin")
DB_DRAMA_ID = result.stdout.strip()
print(f"  DB Drama ID: {DB_DRAMA_ID}")

if not DB_DRAMA_ID or DB_DRAMA_ID == "NULL":
    print("Drama not found in DB!")
    exit(1)

def transcode(input_path, output_path):
    cmd = ["ffmpeg", "-y", "-i", str(input_path),
           "-c:v", "libx264", "-preset", "fast", "-crf", "28",
           "-pix_fmt", "yuv420p",
           "-c:a", "aac", "-b:a", "128k", "-ac", "2",
           "-movflags", "+faststart", str(output_path)]
    try:
        r = subprocess.run(cmd, capture_output=True, text=True, timeout=300)
        return r.returncode == 0 and output_path.exists() and output_path.stat().st_size > 1000
    except:
        return False

def download_mp4(proxy_url, output_path):
    full_url = f"https://vidrama.asia{proxy_url}" if proxy_url.startswith("/") else proxy_url
    try:
        resp = requests.get(full_url, timeout=120, stream=True)
        resp.raise_for_status()
        total = 0
        with open(output_path, 'wb') as f:
            for chunk in resp.iter_content(chunk_size=1024*1024):
                f.write(chunk)
                total += len(chunk)
        return total > 1000
    except Exception as e:
        print(f"        DL error: {str(e)[:50]}")
        return False

def register_episode(ep_num, video_url):
    """Register episode in DB via node script."""
    script = f"""
const {{PrismaClient}} = require('@prisma/client');
const p = new PrismaClient();
p.episode.upsert({{
    where: {{ dramaId_episodeNumber: {{ dramaId: '{DB_DRAMA_ID}', episodeNumber: {ep_num} }} }},
    create: {{
        dramaId: '{DB_DRAMA_ID}',
        episodeNumber: {ep_num},
        title: 'Episode {ep_num}',
        videoUrl: '{video_url}',
        duration: 0,
        isActive: true,
    }},
    update: {{ videoUrl: '{video_url}', isActive: true }},
}}).then(() => {{ process.stdout.write('OK'); p.$disconnect(); }}).catch(e => {{ process.stdout.write('ERR:'+e.message); p.$disconnect(); }});
"""
    r = sp.run(["node", "-e", script], capture_output=True, text=True, cwd=r"D:\kingshortid\admin")
    return r.stdout.strip() == "OK"

# Process episodes
drama_temp = TEMP_DIR / SLUG
drama_temp.mkdir(exist_ok=True)

stats = {"ok": 0, "fail": 0}

for ep_num in range(START_EP, END_EP + 1):
    r2_key = f"melolo/{SLUG}/ep{ep_num:03d}.mp4"
    print(f"  Ep {ep_num:3}/{END_EP}:", end="", flush=True)

    # Check if already on R2
    try:
        s3.head_object(Bucket=R2_BUCKET, Key=r2_key)
        print(f" already on R2, skipping")
        # Still register in DB
        video_url = f"{R2_PUBLIC}/{r2_key}"
        register_episode(ep_num, video_url)
        stats["ok"] += 1
        continue
    except:
        pass

    # Get stream URL
    try:
        sr = requests.get(
            f"{API_URL}?action=stream&id={drama_id}&episode={ep_num}",
            timeout=15
        )
        if sr.status_code != 200:
            print(f" ❌ Stream {sr.status_code}")
            stats["fail"] += 1
            time.sleep(0.5)
            continue
        stream_data = sr.json().get("data", {})
    except Exception as e:
        print(f" ❌ Stream: {str(e)[:40]}")
        stats["fail"] += 1
        time.sleep(0.5)
        continue

    proxy_url = stream_data.get("proxyUrl", "")
    if not proxy_url:
        print(f" ❌ No proxy")
        stats["fail"] += 1
        time.sleep(0.5)
        continue

    # Download
    raw_path = drama_temp / f"raw_ep{ep_num:03d}.mp4"
    out_path = drama_temp / f"ep{ep_num:03d}.mp4"

    print(f" DL", end="", flush=True)
    if not download_mp4(proxy_url, raw_path):
        print(f" ❌ DL fail")
        stats["fail"] += 1
        time.sleep(0.5)
        continue

    raw_mb = raw_path.stat().st_size / 1024 / 1024
    print(f"({raw_mb:.1f}MB)", end="", flush=True)

    # Transcode
    print(f" → FFmpeg", end="", flush=True)
    if not transcode(raw_path, out_path):
        print(f" (raw)", end="", flush=True)
        out_path = raw_path

    out_mb = out_path.stat().st_size / 1024 / 1024
    savings = (1 - out_mb / raw_mb) * 100 if raw_mb > 0 else 0
    print(f"({out_mb:.1f}MB, {savings:+.0f}%)", end="", flush=True)

    # Upload to R2
    print(f" → R2", end="", flush=True)
    try:
        s3.upload_file(str(out_path), R2_BUCKET, r2_key, ExtraArgs={"ContentType": "video/mp4"})
        video_url = f"{R2_PUBLIC}/{r2_key}"
        
        # Register in DB
        if register_episode(ep_num, video_url):
            print(f" ✅")
            stats["ok"] += 1
        else:
            print(f" ✅ (R2 ok, DB failed)")
            stats["ok"] += 1
    except Exception as e:
        print(f" ❌ Upload: {str(e)[:40]}")
        stats["fail"] += 1

    # Cleanup
    raw_path.unlink(missing_ok=True)
    if out_path != raw_path:
        out_path.unlink(missing_ok=True)

    time.sleep(0.5)

shutil.rmtree(drama_temp, ignore_errors=True)

print(f"\n{'='*60}")
print(f"  DONE: {stats['ok']} episodes uploaded, {stats['fail']} failed")
print(f"{'='*60}")
