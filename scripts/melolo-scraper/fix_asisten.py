#!/usr/bin/env python3
"""
Fix Asisten yang Ternyata Istri Bos — download missing ep3-37
"""
import requests, json, time, os, tempfile
from pathlib import Path
from dotenv import load_dotenv
load_dotenv()

R2_ENDPOINT = os.getenv("R2_ENDPOINT")
R2_ACCESS_KEY = os.getenv("R2_ACCESS_KEY_ID")
R2_SECRET_KEY = os.getenv("R2_SECRET_ACCESS_KEY")
R2_BUCKET = os.getenv("R2_BUCKET_NAME")
R2_PUBLIC = "https://stream.shortlovers.id"
API_URL = "https://vidrama.asia/api/melolo"

SLUG = "asisten-yang-ternyata-istri-bos"
VIDRAMA_ID = "7584301330890492933"
MISSING_EPS = list(range(3, 38))  # ep3 to ep37

TEMP_DIR = Path(tempfile.gettempdir()) / "vidrama_fix"
TEMP_DIR.mkdir(exist_ok=True)

_s3 = None
def get_s3():
    global _s3
    if _s3 is None:
        import boto3
        _s3 = boto3.client("s3",
            endpoint_url=R2_ENDPOINT,
            aws_access_key_id=R2_ACCESS_KEY,
            aws_secret_access_key=R2_SECRET_KEY)
    return _s3

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
    except:
        return False

def upload_to_r2(file_path, r2_key):
    try:
        get_s3().upload_file(str(file_path), R2_BUCKET, r2_key,
            ExtraArgs={"ContentType": "video/mp4"})
        return True
    except Exception as e:
        print(f"    R2 error: {str(e)[:60]}")
        return False

def main():
    print("=" * 60)
    print(f"  FIX: {SLUG}")
    print(f"  Missing episodes: {MISSING_EPS[0]}-{MISSING_EPS[-1]} ({len(MISSING_EPS)} eps)")
    print("=" * 60)

    uploaded = 0
    failed = 0

    for ep_num in MISSING_EPS:
        r2_key = f"melolo/{SLUG}/ep{ep_num:03d}.mp4"
        raw_path = TEMP_DIR / f"ep{ep_num:03d}.mp4"

        print(f"  Ep {ep_num:3}/{MISSING_EPS[-1]}:", end="", flush=True)

        success = False
        for attempt in range(3):
            try:
                sr = requests.get(
                    f"{API_URL}?action=stream&id={VIDRAMA_ID}&episode={ep_num}",
                    timeout=15)
                if sr.status_code != 200:
                    time.sleep(2 * (attempt + 1))
                    continue
                stream_data = sr.json().get("data", {})
            except:
                time.sleep(2 * (attempt + 1))
                continue

            proxy_url = stream_data.get("proxyUrl", "")
            if not proxy_url:
                time.sleep(2 * (attempt + 1))
                continue

            if download_mp4(proxy_url, raw_path):
                success = True
                break

            raw_path.unlink(missing_ok=True)
            if attempt < 2:
                print(" 🔄", end="", flush=True)
            time.sleep(2 * (attempt + 1))

        if not success:
            print(" ❌ Failed")
            raw_path.unlink(missing_ok=True)
            failed += 1
            continue

        file_mb = raw_path.stat().st_size / 1024 / 1024

        if upload_to_r2(raw_path, r2_key):
            print(f" ✅ {file_mb:.1f}MB")
            uploaded += 1
        else:
            print(" ❌ Upload failed")
            failed += 1

        raw_path.unlink(missing_ok=True)
        time.sleep(0.3)

    print(f"\n{'=' * 60}")
    print(f"  DONE: {uploaded} uploaded, {failed} failed")
    print(f"{'=' * 60}")

    if uploaded > 0:
        print(f"\n  Now register in DB:")
        print(f"    cd admin && node audit_episodes.js --fix")

if __name__ == "__main__":
    main()
