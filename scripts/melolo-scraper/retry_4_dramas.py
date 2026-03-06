#!/usr/bin/env python3
"""
Retry 4 dramas with no episodes in R2.
Searches Vidrama API by title, downloads episodes, uploads to R2, registers in DB.
"""
import requests, json, time, os, re, sys, tempfile, shutil
from pathlib import Path
from dotenv import load_dotenv
load_dotenv()

R2_ENDPOINT = os.getenv("R2_ENDPOINT")
R2_ACCESS_KEY = os.getenv("R2_ACCESS_KEY_ID")
R2_SECRET_KEY = os.getenv("R2_SECRET_ACCESS_KEY")
R2_BUCKET = os.getenv("R2_BUCKET_NAME")
R2_PUBLIC = "https://stream.shortlovers.id"
API_URL = "https://vidrama.asia/api/melolo"
BACKEND_URL = "http://localhost:3001/api"

TEMP_DIR = Path(tempfile.gettempdir()) / "vidrama_retry"
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

def slugify(text):
    text = text.lower().strip()
    text = re.sub(r'[^\w\s-]', '', text)
    text = re.sub(r'[\s_]+', '-', text)
    return re.sub(r'-+', '-', text).strip('-')

# Dramas to retry
RETRY_SLUGS = [
    "sadar-akan-realita",
    "takdir-pedang-dan-gadis-kesepian",
    "tangi-penyesalan-bos-cantik",
    "tangkap-harta-karun-di-kampung",
]

def search_vidrama(keyword):
    """Search Vidrama API for a drama."""
    try:
        r = requests.get(
            f"{API_URL}?action=search&keyword={keyword}&limit=20",
            timeout=15)
        if r.status_code == 200:
            return r.json().get("data", [])
    except:
        pass
    return []

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
        print(f"        Download error: {str(e)[:60]}")
        return False

def upload_to_r2(file_path, r2_key):
    try:
        ct = "video/mp4" if r2_key.endswith(".mp4") else "image/webp"
        get_s3().upload_file(str(file_path), R2_BUCKET, r2_key,
            ExtraArgs={"ContentType": ct})
        return True
    except Exception as e:
        print(f"        R2 error: {str(e)[:60]}")
        return False

def main():
    print("=" * 60)
    print("  RETRY 4 DRAMAS WITH NO EPISODES")
    print("=" * 60)

    # Load discovery data
    disco_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "vidrama_all_dramas.json")
    with open(disco_path, "r", encoding="utf-8") as f:
        all_dramas = json.load(f)

    slug_to_drama = {}
    for d in all_dramas:
        sl = slugify(d['title'])
        slug_to_drama[sl] = d

    for slug in RETRY_SLUGS:
        print(f"\n{'─' * 60}")
        print(f"  {slug}")

        # Find in discovery data
        drama = slug_to_drama.get(slug)
        if not drama:
            # Try searching Vidrama API
            kw = slug.replace("-", " ")
            print(f"  Searching API for '{kw}'...")
            results = search_vidrama(kw)
            for r in results:
                if slugify(r['title']) == slug:
                    drama = r
                    break
            if not drama and results:
                # Try partial match
                for r in results:
                    rslug = slugify(r['title'])
                    if slug in rslug or rslug in slug:
                        drama = r
                        break

        if not drama:
            print(f"  ❌ Not found in Vidrama API")
            continue

        drama_id = drama.get('id', '')
        title = drama.get('title', slug)
        print(f"  Title: {title}")
        print(f"  ID: {drama_id}")

        # Get detail
        try:
            r = requests.get(f"{API_URL}?action=detail&id={drama_id}", timeout=15)
            if r.status_code != 200:
                print(f"  ❌ Detail API failed: {r.status_code}")
                continue
            detail = r.json().get("data", {})
        except Exception as e:
            print(f"  ❌ Detail error: {e}")
            continue

        episodes = detail.get("episodes", [])
        if not episodes:
            print(f"  ❌ No episodes in API")
            continue

        total_eps = len(episodes)
        print(f"  Episodes: {total_eps}")

        # Process episodes
        uploaded = []
        drama_temp = TEMP_DIR / slug
        drama_temp.mkdir(exist_ok=True)

        for ep in episodes:
            ep_num = ep.get("episodeNumber", 0)
            if ep_num == 0:
                continue

            r2_key = f"melolo/{slug}/ep{ep_num:03d}.mp4"
            print(f"    Ep {ep_num:3}/{total_eps}:", end="", flush=True)

            # Retry up to 3 times with fresh proxy URL
            raw_path = drama_temp / f"ep{ep_num:03d}.mp4"
            success = False

            for attempt in range(3):
                try:
                    sr = requests.get(
                        f"{API_URL}?action=stream&id={drama_id}&episode={ep_num}",
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
                    print(f" 🔄", end="", flush=True)
                time.sleep(2 * (attempt + 1))

            if not success:
                print(f" ❌ Failed")
                raw_path.unlink(missing_ok=True)
                continue

            file_mb = raw_path.stat().st_size / 1024 / 1024

            if upload_to_r2(raw_path, r2_key):
                print(f" ✅ {file_mb:.1f}MB")
                uploaded.append({
                    "number": ep_num,
                    "videoUrl": f"{R2_PUBLIC}/{r2_key}",
                })
            else:
                print(f" ❌ Upload failed")

            raw_path.unlink(missing_ok=True)
            time.sleep(0.3)

        shutil.rmtree(drama_temp, ignore_errors=True)

        if uploaded:
            print(f"  ✅ Uploaded {len(uploaded)}/{total_eps} episodes")
        else:
            print(f"  ❌ No episodes uploaded")

    print(f"\n{'=' * 60}")
    print("  DONE")
    print(f"{'=' * 60}")

if __name__ == "__main__":
    main()
