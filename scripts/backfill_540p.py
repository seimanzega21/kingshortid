import os
import time
import subprocess
import psycopg2
import boto3
from pathlib import Path
from dotenv import load_dotenv
import threading
from concurrent.futures import ThreadPoolExecutor, as_completed
import json

# Load env variables from admin panel
load_dotenv('d:/kingshortid/admin/.env')

DATABASE_URL = os.environ.get("DATABASE_URL")
R2_ENDPOINT = os.environ.get("R2_ENDPOINT")
R2_ACCESS_KEY = os.environ.get("R2_ACCESS_KEY_ID")
R2_SECRET_KEY = os.environ.get("R2_SECRET_ACCESS_KEY")
R2_BUCKET = os.environ.get("R2_BUCKET_NAME")
R2_PUBLIC = os.environ.get("R2_PUBLIC_URL", "https://stream.shortlovers.id")

print("Checking environment variables...")
if not all([DATABASE_URL, R2_ENDPOINT, R2_ACCESS_KEY, R2_SECRET_KEY, R2_BUCKET]):
    print("[!] Missing required environment variables. Check d:/kingshortid/admin/.env")
    exit(1)

TEMP_DIR = Path("d:/kingshortid/scripts/temp_540p")
TEMP_DIR.mkdir(exist_ok=True)

# Thread-local S3 client to avoid conflicts in ThreadPoolExecutor
_local = threading.local()
_print_lock = threading.Lock()
stats_lock = threading.Lock()
stats = {"ok": 0, "fail": 0, "skipped": 0}

def tprint(msg):
    with _print_lock:
        print(msg, flush=True)

def get_s3():
    if not hasattr(_local, "s3"):
        _local.s3 = boto3.client(
            "s3",
            endpoint_url=R2_ENDPOINT,
            aws_access_key_id=R2_ACCESS_KEY,
            aws_secret_access_key=R2_SECRET_KEY,
        )
    return _local.s3

def get_db_connection():
    clean_url = DATABASE_URL.split("?")[0]
    return psycopg2.connect(clean_url)

def get_episodes_to_backfill(limit=1000):
    try:
        conn = get_db_connection()
        cur = conn.cursor()
        
        # We want to process newer dramas first
        query = """
            SELECT e.id, e."videoUrl", d.title, e."episodeNumber" 
            FROM "Episode" e
            JOIN "Drama" d ON e."dramaId" = d.id
            WHERE e."videoUrl540p" IS NULL 
            AND e."videoUrl" IS NOT NULL
            AND e."videoUrl" LIKE %s
            ORDER BY d."createdAt" DESC, e."episodeNumber" ASC
            LIMIT %s;
        """
        cur.execute(query, (f"{R2_PUBLIC}%", limit))
        results = cur.fetchall()
        cur.close()
        conn.close()
        
        # Convert to dict
        episodes = []
        for r in results:
            episodes.append({
                "id": r[0],
                "video_url": r[1],
                "drama_title": r[2],
                "episode_number": r[3]
            })
        return episodes
    except Exception as e:
        print(f"[!] DB Error: {e}")
        return []

def update_episode_540p(episode_id, url_540p):
    try:
        conn = get_db_connection()
        cur = conn.cursor()
        cur.execute('UPDATE "Episode" SET "videoUrl540p" = %s, "updatedAt" = NOW() WHERE id = %s', (url_540p, episode_id))
        conn.commit()
        cur.close()
        conn.close()
        return True
    except Exception as e:
        tprint(f"[!] DB Update Error for {episode_id}: {e}")
        return False

def check_r2_exists(key):
    try:
        get_s3().head_object(Bucket=R2_BUCKET, Key=key)
        return True
    except:
        return False

def transcode_to_540p(input_url, output_path):
    cmd = [
        "ffmpeg", "-y",
        "-i", input_url,
        "-vf", "scale=-2:540",
        "-c:v", "libx264",
        "-crf", "26",
        "-preset", "superfast",  # Using superfast for backfill speed
        "-movflags", "+faststart",
        "-c:a", "aac",
        "-b:a", "128k",
        str(output_path)
    ]
    try:
        process = subprocess.run(cmd, stdout=subprocess.DEVNULL, stderr=subprocess.PIPE, text=True, timeout=300)
        if process.returncode == 0:
            return True
        else:
            tprint(f"      FFmpeg Error:\n{process.stderr[-200:]}")
            return False
    except subprocess.TimeoutExpired:
        tprint("      ⏳ FFmpeg timeout")
        return False
    except Exception as e:
        tprint(f"      [!] FFmpeg exec error: {e}")
        return False

def process_episode(ep, index, total):
    ep_id = ep["id"]
    orig_url = ep["video_url"]
    title = ep["drama_title"]
    ep_num = ep["episode_number"]
    tag = f"[{index}/{total}]"
    
    # Example orig_url: https://stream.shortlovers.id/melolo/aku-cinta-pertama/ep001.mp4
    # We want: melolo/aku-cinta-pertama/ep001_540p.mp4
    r2_key_orig = orig_url.replace(R2_PUBLIC + "/", "")
    if not r2_key_orig.endswith(".mp4"):
        tprint(f"{tag} [>] Skipping {title} Ep {ep_num}: Not an MP4 file.")
        with stats_lock: stats["skipped"] += 1
        return
        
    r2_key_540p = r2_key_orig.replace(".mp4", "_540p.mp4")
    url_540p = f"{R2_PUBLIC}/{r2_key_540p}"
    
    tprint(f"{tag} [+] {title} Ep {ep_num} -> 540p")
    
    # 1. Check if 540p already exists in R2 (maybe DB update failed previously)
    if check_r2_exists(r2_key_540p):
        tprint(f"    [+] File already in R2. Updating DB...")
        if update_episode_540p(ep_id, url_540p):
            with stats_lock: stats["ok"] += 1
        else:
            with stats_lock: stats["fail"] += 1
        return

    # 2. Transcode
    temp_file = TEMP_DIR / f"temp_{ep_id}_540p.mp4"
    tprint(f"    [*] Transcoding...")
    start_time = time.time()
    
    if not transcode_to_540p(orig_url, temp_file):
        temp_file.unlink(missing_ok=True)
        tprint(f"    [!] Transcode failed.")
        with stats_lock: stats["fail"] += 1
        return
        
    duration = time.time() - start_time
    file_mb = temp_file.stat().st_size / (1024 * 1024)
    tprint(f"    [+] Transcoded in {duration:.1f}s ({file_mb:.1f}MB). Uploading...")

    # 3. Upload to R2
    try:
        get_s3().upload_file(
            str(temp_file), 
            R2_BUCKET, 
            r2_key_540p,
            ExtraArgs={"ContentType": "video/mp4"}
        )
    except Exception as e:
        tprint(f"    [!] Upload failed: {e}")
        temp_file.unlink(missing_ok=True)
        with stats_lock: stats["fail"] += 1
        return

    # 4. Update DB
    if update_episode_540p(ep_id, url_540p):
        tprint(f"    [+] Success! DB Updated.")
        with stats_lock: stats["ok"] += 1
    else:
        tprint(f"    [!] DB Update failed after upload.")
        with stats_lock: stats["fail"] += 1

    # Cleanup
    temp_file.unlink(missing_ok=True)


if __name__ == "__main__":
    import sys
    limit = 1000
    workers = 3
    
    if "--limit" in sys.argv:
        idx = sys.argv.index("--limit")
        limit = int(sys.argv[idx + 1])
        
    if "--workers" in sys.argv:
        idx = sys.argv.index("--workers")
        workers = int(sys.argv[idx + 1])

    print("="*60)
    print(" [+] KINGSHORT 540P BACKFILL SCRIPT")
    print(f" Target: {limit} episodes | Workers: {workers}")
    print("="*60)
    
    episodes = get_episodes_to_backfill(limit=limit)
    total_eps = len(episodes)
    
    if total_eps == 0:
        print("[+] No episodes need 540p backfill.")
        exit(0)
        
    print(f"Found {total_eps} episodes to process. Starting pool...\n")
    
    with ThreadPoolExecutor(max_workers=workers) as executor:
        futures = []
        for i, ep in enumerate(episodes, 1):
            f = executor.submit(process_episode, ep, i, total_eps)
            futures.append(f)
            
        for f in as_completed(futures):
            try:
                f.result()
            except Exception as e:
                tprint(f"Worker exception: {e}")
                
    print("\n" + "="*60)
    print(" DONE!")
    print(f" [+] Success: {stats['ok']}")
    print(f" [!] Failed:  {stats['fail']}")
    print(f" [>] Skipped: {stats['skipped']}")
    print("="*60)
