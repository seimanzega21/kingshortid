#!/usr/bin/env python3
"""
FIXED RESCRAPE - Download full + faststart yang benar untuk ep 16 & 17
Masalah sebelumnya: moov atom not found (faststart tidak diterapkan dengan benar)
"""
import requests, subprocess, os, sys, time, json
from pathlib import Path
from dotenv import load_dotenv
import boto3

load_dotenv()
sys.stdout.reconfigure(encoding="utf-8")

DRAMA_ID   = "2010948201357684738"
DRAMA_SLUG = "legenda-naga-kembali"
TARGET_EPS = [34, 35]
R2_BUCKET  = os.getenv("R2_BUCKET_NAME", "shortlovers")
R2_PUBLIC  = "https://stream.shortlovers.id"
R2_PREFIX  = "dramas/microdrama"
BACKEND    = "https://api.shortlovers.id/api"
TEMP       = Path("C:/tmp/legenda_naga_fix2")
TEMP.mkdir(parents=True, exist_ok=True)

def get_s3():
    return boto3.client("s3",
        endpoint_url=os.getenv("R2_ENDPOINT"),
        aws_access_key_id=os.getenv("R2_ACCESS_KEY_ID"),
        aws_secret_access_key=os.getenv("R2_SECRET_ACCESS_KEY"),
        region_name="auto",
    )

def fetch_episode_urls():
    """Ambil URL video dari API."""
    print("[1] Fetching episode URLs...")
    url = f"https://vidrama.asia/api/microdrama?action=detail&id={DRAMA_ID}&lang=id"
    resp = requests.get(url, timeout=20)
    episodes = resp.json().get("episodes", [])
    result = {}
    for ep in episodes:
        idx = ep.get("index", 0)
        if idx not in TARGET_EPS:
            continue
        videos = ep.get("videos", [])
        # Prefer 720P
        url_720 = next((v["url"] for v in videos if v.get("quality") == "720P"), None)
        url_any = next((v["url"] for v in videos if v.get("url")), None)
        video_url = url_720 or url_any
        if video_url:
            quality = "720P" if url_720 else "other"
            result[idx] = {"url": video_url, "quality": quality}
            print(f"    Ep {idx}: {quality} → {video_url[:70]}...")
    return result

def download_full(url, dest):
    """Download file lengkap (tidak partial)."""
    print(f"    Downloading full file...")
    resp = requests.get(url, timeout=300, stream=True)
    resp.raise_for_status()
    total = 0
    with open(dest, "wb") as f:
        for chunk in resp.iter_content(chunk_size=2 * 1024 * 1024):
            f.write(chunk)
            total += len(chunk)
    size_mb = total / 1024 / 1024
    print(f"    Downloaded: {size_mb:.2f} MB ({total:,} bytes)")
    return total

def apply_faststart(raw, output):
    """Apply faststart - wajib copy saja, jangan encode ulang."""
    print(f"    Applying faststart (copy mode)...")
    result = subprocess.run(
        ["ffmpeg", "-y", "-i", str(raw),
         "-c", "copy",           # NO re-encode, hanya copy stream
         "-movflags", "+faststart",  # pindah moov ke depan
         str(output)],
        capture_output=True, timeout=180
    )
    if result.returncode != 0:
        stderr = result.stderr.decode("utf-8", errors="replace")
        print(f"    ffmpeg stderr: {stderr[-300:]}")
        return False
    if not output.exists() or output.stat().st_size < 1000:
        print(f"    ffmpeg output invalid!")
        return False
    
    out_mb = output.stat().st_size / 1024 / 1024
    print(f"    Faststart OK: {out_mb:.2f} MB")
    return True

def verify_moov(filepath):
    """Cek apakah moov atom ada di awal file (faststart berhasil)."""
    result = subprocess.run(
        ["ffprobe", "-v", "error", "-print_format", "json",
         "-show_format", "-show_streams", str(filepath)],
        capture_output=True, text=True, timeout=20
    )
    if result.returncode != 0:
        print(f"    VERIFY FAIL: {result.stderr[:150]}")
        return False
    data = json.loads(result.stdout)
    dur = float(data.get("format", {}).get("duration", 0))
    print(f"    VERIFY OK: duration={dur:.1f}s")
    return dur > 0

def upload_to_r2(s3, src, r2_key):
    """Upload ke R2."""
    print(f"    Uploading to R2: {r2_key}")
    s3.upload_file(
        str(src), R2_BUCKET, r2_key,
        ExtraArgs={
            "ContentType": "video/mp4",
            "CacheControl": "public, max-age=31536000, immutable",
            "ContentDisposition": "inline",
        }
    )
    url = f"{R2_PUBLIC}/{r2_key}"
    print(f"    Upload OK: {url}")
    return url

def update_db(ep_num, video_url):
    """Update episode di database."""
    print(f"    Updating DB ep {ep_num}...")
    # Cari drama ID di DB
    resp = requests.get(f"{BACKEND}/dramas?limit=500", timeout=15)
    items = resp.json() if isinstance(resp.json(), list) else resp.json().get("dramas", [])
    drama_db_id = None
    for d in items:
        title = d.get("title", "").lower()
        if "legenda" in title and "naga" in title:
            drama_db_id = d["id"]
            print(f"    Drama DB ID: {drama_db_id}")
            break

    if not drama_db_id:
        print(f"    Drama not found in DB!")
        return False

    payload = {
        "dramaId": drama_db_id,
        "episodeNumber": ep_num,
        "title": f"Episode {ep_num}",
        "videoUrl": video_url,
        "duration": 0,
    }
    # POST (insert/update)
    r = requests.post(f"{BACKEND}/episodes", json=payload, timeout=10)
    if r.status_code in [200, 201]:
        print(f"    DB OK: ep {ep_num} updated")
        return True
    # Try PATCH
    r = requests.patch(f"{BACKEND}/episodes/{drama_db_id}/{ep_num}", json=payload, timeout=10)
    if r.status_code in [200, 201, 204]:
        print(f"    DB PATCH OK: ep {ep_num}")
        return True
    print(f"    DB fail: {r.status_code} {r.text[:100]}")
    return False

def main():
    print("=" * 60)
    print("  FIXED RESCRAPE: Legenda Naga Kembali Ep 16 & 17")
    print("  Strategy: Full download + ffmpeg copy faststart + verify")
    print("=" * 60)

    s3 = get_s3()

    # Fetch URLs
    ep_urls = fetch_episode_urls()
    if not ep_urls:
        print("ERROR: No episode URLs found!")
        return

    for ep_num in TARGET_EPS:
        if ep_num not in ep_urls:
            print(f"\nEp {ep_num}: No URL, skip!")
            continue

        info = ep_urls[ep_num]
        print(f"\n{'─'*55}")
        print(f"  Episode {ep_num} ({info['quality']})")

        raw_file  = TEMP / f"ep{ep_num:03d}_raw.mp4"
        fast_file = TEMP / f"ep{ep_num:03d}_fast.mp4"

        # Step A: Download full
        size = download_full(info["url"], raw_file)
        if size < 1000:
            print(f"  FAIL: Download failed or too small!")
            continue
        print(f"  Raw: {raw_file.stat().st_size / 1024 / 1024:.2f} MB")

        # Step B: Apply faststart
        ok = apply_faststart(raw_file, fast_file)
        raw_file.unlink(missing_ok=True)

        if not ok:
            print(f"  faststart FAILED, using raw file...")
            # Just rename raw → fast (no faststart)
            if raw_file.exists():
                raw_file.rename(fast_file)
            else:
                print(f"  No file to upload!")
                continue

        # Step C: Verify with ffprobe
        valid = verify_moov(fast_file)
        if not valid:
            print(f"  WARNING: ffprobe verification failed, upload anyway...")

        # Step D: Upload to R2
        r2_key = f"{R2_PREFIX}/{DRAMA_SLUG}/ep{ep_num:03d}/video.mp4"
        try:
            video_url = upload_to_r2(s3, fast_file, r2_key)
        except Exception as e:
            print(f"  R2 UPLOAD ERROR: {e}")
            fast_file.unlink(missing_ok=True)
            continue
        fast_file.unlink(missing_ok=True)

        # Step E: Update DB
        update_db(ep_num, video_url)

        print(f"  Ep {ep_num}: DONE → {video_url}")

    # Cleanup
    import shutil
    shutil.rmtree(TEMP, ignore_errors=True)

    print(f"\n{'='*60}")
    print("  SELESAI! Coba play ulang di browser.")
    print(f"{'='*60}")

if __name__ == "__main__":
    main()
