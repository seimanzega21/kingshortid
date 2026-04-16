import os, sys, threading, subprocess, shutil, requests, tempfile
from pathlib import Path
from concurrent.futures import ThreadPoolExecutor, as_completed
from dotenv import load_dotenv
import boto3
from botocore.config import Config

load_dotenv('d:\\kingshortid\\scripts\\melolo-scraper\\.env')  # reads .env from current directory

R2_ENDPOINT   = os.getenv("R2_ENDPOINT", "")
R2_ACCESS_KEY = os.getenv("R2_ACCESS_KEY_ID", "")
R2_SECRET_KEY = os.getenv("R2_SECRET_ACCESS_KEY", "")
R2_BUCKET     = os.getenv("R2_BUCKET_NAME", "shortlovers")
R2_PUBLIC     = "https://stream.shortlovers.id"
BACKEND_URL   = "https://api.shortlovers.id/api"
ADMIN_KEY     = os.getenv("ADMIN_API_KEY", "00ca04e3e2702be565d7bf44e783255247708289bce9b2fb6187a2e117f87fd14")

TEMP_DIR = Path(tempfile.gettempdir()) / "backfill540p"
TEMP_DIR.mkdir(exist_ok=True)

WORKERS = 4

_lock = threading.Lock()

def tprint(*args, **kwargs):
    with _lock:
        print(*args, flush=True, **kwargs)

def get_s3():
    return boto3.client(
        "s3",
        endpoint_url=R2_ENDPOINT,
        aws_access_key_id=R2_ACCESS_KEY,
        aws_secret_access_key=R2_SECRET_KEY,
        config=Config(signature_version="s3v4"),
        region_name="auto",
    )

def list_r2_keys(s3, prefix):
    keys = []
    kwargs = {"Bucket": R2_BUCKET, "Prefix": prefix}
    while True:
        resp = s3.list_objects_v2(**kwargs)
        for obj in resp.get("Contents", []):
            keys.append(obj["Key"])
        if not resp.get("IsTruncated"):
            break
        kwargs["ContinuationToken"] = resp["NextContinuationToken"]
    return keys

def r2_key_exists(s3, key):
    try:
        s3.head_object(Bucket=R2_BUCKET, Key=key)
        return True
    except:
        return False

def process_episode(key_720p, s3, idx, total):
    # key_720p example: dramas/netshort/sulih-suara-kebangkitan-raja-balap/1.mp4
    parts = key_720p.split("/")
    if len(parts) < 4:
        return
    slug = parts[2]
    ep_file = parts[3]  # 1.mp4

    try:
        ep_num = int(ep_file.replace("ep", "").replace(".mp4", "").replace("_540p", ""))
    except:
        return

    key_540p = key_720p.replace(".mp4", "_540p.mp4")

    if r2_key_exists(s3, key_540p):
        tprint(f"  [{idx}/{total}] {slug}/ep{ep_num:03d}: 540P exists")
        url_540p = f"{R2_PUBLIC}/{key_540p}"
        url_720p = f"{R2_PUBLIC}/{key_720p}"
        update_db(url_720p, url_540p, slug, ep_num)
        return

    work_dir = TEMP_DIR / f"{slug}_ep{ep_num}_{threading.current_thread().ident}"
    work_dir.mkdir(exist_ok=True)
    path_720p = work_dir / "in_720p.mp4"
    path_540p = work_dir / "out_540p.mp4"

    try:
        tprint(f"  [{idx}/{total}] {slug}/ep{ep_num:03d}: Downloading 720P...")
        s3.download_file(R2_BUCKET, key_720p, str(path_720p))

        res = subprocess.run([
            "ffmpeg", "-y", "-i", str(path_720p),
            "-vf", "scale=w=-2:h=540",
            "-c:v", "libx264", "-preset", "fast", "-crf", "26",
            "-movflags", "+faststart",
            "-c:a", "copy",
            str(path_540p)
        ], capture_output=True, timeout=300)

        if res.returncode != 0 or not path_540p.exists():
            tprint(f"  [{idx}/{total}] {slug}/ep{ep_num:03d}: FFmpeg FAIL")
            return

        mb_540 = path_540p.stat().st_size / 1024 / 1024
        mb_720 = path_720p.stat().st_size / 1024 / 1024

        s3.upload_file(str(path_540p), R2_BUCKET, key_540p,
                       ExtraArgs={"ContentType": "video/mp4"})

        url_540p = f"{R2_PUBLIC}/{key_540p}"
        url_720p = f"{R2_PUBLIC}/{key_720p}"

        tprint(f"  [{idx}/{total}] {slug}/ep{ep_num:03d}: OK {mb_720:.1f}MB->{mb_540:.1f}MB | {url_540p}")

        update_db(url_720p, url_540p, slug, ep_num)

    except Exception as e:
        tprint(f"  [{idx}/{total}] {slug}/ep{ep_num:03d}: ERROR {str(e)[:60]}")
    finally:
        shutil.rmtree(work_dir, ignore_errors=True)

def update_db(url_720p, url_540p, slug, ep_num):
    headers = {
        "Authorization": f"Bearer {ADMIN_KEY}",
        "X-Admin-Key": ADMIN_KEY,
        "Content-Type": "application/json"
    }
    try:
        r = requests.get(f"{BACKEND_URL}/dramas/hfdppzzwmfh63hhhcxv5ff87?includeInactive=true", timeout=10)
        if r.status_code == 200:
            drama_data = r.json()
            episodes = drama_data.get("episodes", [])
            for ep in episodes:
                if ep["episodeNumber"] == ep_num:
                    res = requests.patch(f"{BACKEND_URL}/episodes/{ep['id']}",
                                   json={"videoUrl540p": url_540p},
                                   headers=headers, timeout=10)
                    if res.status_code == 200:
                        tprint(f"  -> Linked DB 540P ep {ep_num}")
                    else:
                        tprint(f"  -> DB PATCH failed for ep {ep_num}: {res.text}")
                    break
    except Exception as e:
        tprint(f"  -> DB update failed: {e}")

def main():
    print("=" * 60)
    print("  NETSHORT 540P BACKFILL")
    print(f"  Workers: {WORKERS}")
    print("=" * 60)

    s3 = get_s3()

    print("\n  Listing R2 objects ...")
    all_keys = list_r2_keys(s3, "dramas/netshort/sulih-suara-kebangkitan-raja-balap/")
    ep_720p_keys = [
        k for k in all_keys
        if k.endswith(".mp4") and "_540p" not in k
    ]
    print(f"  Found {len(ep_720p_keys)} episodes to check\n")

    with ThreadPoolExecutor(max_workers=WORKERS) as executor:
        futures = {
            executor.submit(process_episode, key, s3, idx + 1, len(ep_720p_keys)): key
            for idx, key in enumerate(ep_720p_keys)
        }
        for future in as_completed(futures):
            try:
                future.result()
            except Exception as e:
                tprint(f"  WORKER ERROR: {e}")

    print("\n" + "=" * 60)
    print("  BACKFILL DONE")
    print("=" * 60)

if __name__ == "__main__":
    main()
