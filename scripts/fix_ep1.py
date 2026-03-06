#!/usr/bin/env python3
"""
Fix missing Episode 1 of Ahli Pengobatan Sakti.

Steps:
1. Get EP1 stream URL from Vidrama
2. Download raw MP4
3. Transcode to HLS with FFmpeg (matching existing format)
4. Upload HLS segments + playlist to R2
5. Shift all existing episode numbers +1 in backend
6. Insert new EP1 pointing to R2
"""
import requests, os, sys, shutil, subprocess, tempfile, time
from pathlib import Path
from dotenv import load_dotenv

load_dotenv(os.path.join(os.path.dirname(__file__), "melolo-scraper", ".env"))

R2_ENDPOINT = os.getenv("R2_ENDPOINT")
R2_ACCESS_KEY = os.getenv("R2_ACCESS_KEY_ID")
R2_SECRET_KEY = os.getenv("R2_SECRET_ACCESS_KEY")
R2_BUCKET = os.getenv("R2_BUCKET_NAME")
R2_PUBLIC = "https://stream.shortlovers.id"
BACKEND_API = "https://api.shortlovers.id/api"
VIDRAMA_API = "https://vidrama.asia/api/melolo"

DRAMA_VIDRAMA_ID = "7588815593659173941"
DRAMA_DB_ID = "cmleexll8004hhx5e4qx99qtv"
SLUG = "ahli-pengobatan-sakti"

TEMP_DIR = Path(tempfile.gettempdir()) / "fix_ep1"
TEMP_DIR.mkdir(exist_ok=True)

import boto3
s3 = boto3.client("s3",
    endpoint_url=R2_ENDPOINT,
    aws_access_key_id=R2_ACCESS_KEY,
    aws_secret_access_key=R2_SECRET_KEY,
)


def step1_get_stream_url():
    """Get EP1 stream/proxy URL from Vidrama."""
    print("[1/6] Getting EP1 stream URL from Vidrama...", end="", flush=True)
    try:
        r = requests.get(
            f"{VIDRAMA_API}?action=stream&id={DRAMA_VIDRAMA_ID}&episode=1",
            timeout=15
        )
        if r.status_code != 200:
            print(f" ❌ HTTP {r.status_code}: {r.text[:100]}")
            return None
        data = r.json().get("data", {})
        proxy_url = data.get("proxyUrl", "")
        duration = data.get("duration", 0)
        print(f" ✅ (duration={duration}s)")
        print(f"  Proxy URL: {proxy_url[:80]}...")
        return proxy_url, duration
    except Exception as e:
        print(f" ❌ {e}")
        return None


def step2_download_mp4(proxy_url):
    """Download raw MP4 from Vidrama proxy."""
    print("[2/6] Downloading raw MP4...", end="", flush=True)
    full_url = f"https://vidrama.asia{proxy_url}" if proxy_url.startswith("/") else proxy_url
    raw_path = TEMP_DIR / "raw_ep001.mp4"
    try:
        resp = requests.get(full_url, timeout=120, stream=True)
        resp.raise_for_status()
        total = 0
        with open(raw_path, "wb") as f:
            for chunk in resp.iter_content(chunk_size=1024 * 1024):
                f.write(chunk)
                total += len(chunk)
        size_mb = total / 1024 / 1024
        print(f" ✅ ({size_mb:.1f}MB)")
        return raw_path
    except Exception as e:
        print(f" ❌ {e}")
        return None


def step3_transcode_to_hls(raw_path):
    """Transcode MP4 to HLS (m3u8 + .ts segments) using FFmpeg."""
    print("[3/6] Transcoding to HLS with FFmpeg...", end="", flush=True)
    hls_dir = TEMP_DIR / "hls"
    hls_dir.mkdir(exist_ok=True)
    playlist = hls_dir / "playlist.m3u8"
    
    cmd = [
        "ffmpeg", "-y",
        "-i", str(raw_path),
        "-c:v", "libx264", "-crf", "28", "-preset", "fast",
        "-c:a", "aac", "-b:a", "128k",
        "-hls_time", "10",
        "-hls_list_size", "0",
        "-hls_segment_filename", str(hls_dir / "seg_%03d.ts"),
        "-f", "hls",
        str(playlist),
    ]
    
    try:
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=120)
        if result.returncode != 0:
            print(f" ❌ FFmpeg error: {result.stderr[:200]}")
            return None
        
        segments = list(hls_dir.glob("seg_*.ts"))
        total_size = sum(s.stat().st_size for s in segments) / 1024 / 1024
        print(f" ✅ ({len(segments)} segments, {total_size:.1f}MB)")
        return hls_dir
    except Exception as e:
        print(f" ❌ {e}")
        return None


def step4_upload_hls_to_r2(hls_dir):
    """Upload all HLS files to R2 under ep001/."""
    print("[4/6] Uploading HLS to R2...", end="", flush=True)
    r2_prefix = f"melolo/{SLUG}/ep001"
    
    files = list(hls_dir.iterdir())
    uploaded = 0
    for f in files:
        r2_key = f"{r2_prefix}/{f.name}"
        ct = "application/vnd.apple.mpegurl" if f.suffix == ".m3u8" else "video/mp2t"
        try:
            s3.put_object(
                Bucket=R2_BUCKET,
                Key=r2_key,
                Body=f.read_bytes(),
                ContentType=ct,
            )
            uploaded += 1
        except Exception as e:
            print(f"\n  ❌ Upload {f.name}: {e}")
    
    print(f" ✅ ({uploaded}/{len(files)} files)")
    return uploaded == len(files)


def step5_shift_episodes():
    """Shift all existing episode numbers +1 in the database."""
    print("[5/6] Shifting episode numbers +1 in DB...", end="", flush=True)
    
    # Get all existing episodes
    try:
        r = requests.get(f"{BACKEND_API}/dramas/{DRAMA_DB_ID}/episodes", timeout=15)
        eps = r.json()
        eps.sort(key=lambda x: x.get("episodeNumber", 0), reverse=True)  # descending to avoid conflicts
        
        shifted = 0
        for ep in eps:
            old_num = ep["episodeNumber"]
            new_num = old_num + 1
            ep_id = ep["id"]
            
            # Update episode number via API
            # Since we may not have a PATCH endpoint, we'll need to handle this differently
            # Let's check if we can just insert EP1 and update the drama record
            shifted += 1
        
        print(f" ⚠️ Need API support for updating episode numbers")
        print(f"    Total episodes to shift: {len(eps)}")
        return eps
    except Exception as e:
        print(f" ❌ {e}")
        return None


def step6_verify():
    """Verify EP1 is accessible on R2."""
    print("[6/6] Verifying EP1 on R2...", end="", flush=True)
    url = f"{R2_PUBLIC}/melolo/{SLUG}/ep001/playlist.m3u8"
    try:
        r = requests.head(url, timeout=10)
        print(f" {'✅' if r.status_code == 200 else '❌'} HTTP {r.status_code} ({r.headers.get('content-length', '?')} bytes)")
        return r.status_code == 200
    except Exception as e:
        print(f" ❌ {e}")
        return False


def main():
    print("=" * 60)
    print("  FIX MISSING EP1: Ahli Pengobatan Sakti")
    print("=" * 60)
    
    # Step 1: Get stream URL
    result = step1_get_stream_url()
    if not result:
        return
    proxy_url, duration = result
    
    # Step 2: Download
    raw_path = step2_download_mp4(proxy_url)
    if not raw_path:
        return
    
    # Step 3: Transcode to HLS
    hls_dir = step3_transcode_to_hls(raw_path)
    if not hls_dir:
        return
    
    # Step 4: Upload to R2
    if not step4_upload_hls_to_r2(hls_dir):
        return
    
    # Step 5: Check episode situation
    step5_shift_episodes()
    
    # Step 6: Verify
    step6_verify()
    
    # Cleanup
    shutil.rmtree(TEMP_DIR, ignore_errors=True)
    
    print()
    print("=" * 60)
    print("  EP1 uploaded to R2! Episode reordering needs manual DB update.")
    print(f"  EP1 URL: {R2_PUBLIC}/melolo/{SLUG}/ep001/playlist.m3u8")
    print("=" * 60)


if __name__ == "__main__":
    main()
