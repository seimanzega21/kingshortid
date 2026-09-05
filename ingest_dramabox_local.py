# -*- coding: utf-8 -*-
"""
VPS-BASED PIPELINE: Ingestion script for dramabox provider
- Fetches fresh video URL per-episode via action=stream (avoids token expiry)
- No subtitles (empty for this provider)
- Direct MP4 download (no HLS)
"""
import requests
import boto3
import json
import time
import os
import subprocess
import urllib3
import urllib.parse
from botocore.config import Config

urllib3.disable_warnings()

# ─── CONFIG ────────────────────────────────────────────────────────────────
API_BASE  = 'http://141.11.160.187:3000'
ADMIN_KEY = '00ca04e3e2702be565d7bf44e783255247708289bce9b2fb6187a2e117f87fd14'
ADMIN_HDR = {'x-admin-key': ADMIN_KEY, 'Content-Type': 'application/json'}

R2_ENDPOINT = 'https://a142d3b29a5d64943cb251157e25eaf3.r2.cloudflarestorage.com'
R2_KEY_ID   = '07c99c897986ea52703c1285308d5e2c'
R2_SECRET   = '44788d376ffb216e1e73784b6fe1ff1423607928898a87c50819b52cdfc12e44'
R2_BUCKET   = 'shortlovers'
R2_PUBLIC   = 'https://stream.shortlovers.id'

TEMP_DIR = 'd:/kingshortid/temp_dramabox'
os.makedirs(TEMP_DIR, exist_ok=True)

DRAMAS = [
    {
        "slug": "hati-yang-dihancurkan",
        "id": "42000025364",
        "lang": "in",
        "genres": ["Drama", "Romantis"]
    }
]

HDR = {'User-Agent': 'Mozilla/5.0'}


# ─── HELPERS ───────────────────────────────────────────────────────────────
def get_r2():
    return boto3.client(
        's3', endpoint_url=R2_ENDPOINT,
        aws_access_key_id=R2_KEY_ID, aws_secret_access_key=R2_SECRET,
        config=Config(signature_version='s3v4'), region_name='auto'
    )


def fetch_drama_details(mid, lang):
    url = f"https://vidrama.asia/api/dramabox?action=detail&id={mid}&lang={lang}"
    print(f"   🌐 Fetching drama details for {mid}...")
    for _ in range(5):
        try:
            r = requests.get(url, headers=HDR, timeout=20)
            if r.ok:
                res = r.json()
                if res.get('success'):
                    return res.get('data', {})
        except Exception as e:
            print(f"      ⚠ {e}")
        time.sleep(3)
    return None


def fetch_episode_url(mid, ep_no, lang):
    """Fetch a FRESH video URL per episode to avoid token expiry."""
    url = f"https://vidrama.asia/api/dramabox?action=stream&id={mid}&episode={ep_no}&lang={lang}"
    for attempt in range(1, 5):
        try:
            r = requests.get(url, headers=HDR, timeout=20)
            if r.ok:
                res = r.json()
                if res.get('success'):
                    data = res.get('data', {})
                    video_url = data.get('videoUrl') or data.get('rawVideoUrl', '')
                    subs = data.get('subtitles', [])
                    return video_url, subs
        except Exception as e:
            print(f"      ⚠ Stream fetch attempt {attempt}: {e}")
        time.sleep(3)
    return None, []


def download_and_transcode(video_url, ep_no):
    src  = os.path.join(TEMP_DIR, f"src_ep{ep_no:03d}.mp4")
    p720 = os.path.join(TEMP_DIR, f"ep{ep_no:03d}_720p.mp4")
    p540 = os.path.join(TEMP_DIR, f"ep{ep_no:03d}_540p.mp4")
    for f in [src, p720, p540]:
        if os.path.exists(f): os.remove(f)

    # Download source
    for attempt in range(1, 4):
        try:
            res = subprocess.run(
                ['ffmpeg', '-y', '-i', video_url, '-c', 'copy', '-loglevel', 'warning', src],
                capture_output=True, text=True, errors='ignore', timeout=300
            )
            if res.returncode == 0 and os.path.exists(src) and os.path.getsize(src) > 500*1024:
                break
            print(f"      ⚠ DL attempt {attempt}: {res.stderr.strip()[-150:]}")
        except Exception as e:
            print(f"      ⚠ DL error attempt {attempt}: {e}")
        time.sleep(3)
    else:
        return None, None

    # Encode 720p
    for attempt in range(1, 4):
        res = subprocess.run(
            ['ffmpeg', '-y', '-i', src,
             '-vf', 'scale=720:-2', '-c:v', 'libx264', '-crf', '23', '-preset', 'fast',
             '-fps_mode', 'cfr', '-af', 'aresample=async=1',
             '-maxrate', '1500k', '-bufsize', '3000k',
             '-c:a', 'aac', '-b:a', '128k', '-movflags', '+faststart',
             '-loglevel', 'warning', p720],
            capture_output=True, text=True, errors='ignore', timeout=180
        )
        if res.returncode == 0 and os.path.exists(p720) and os.path.getsize(p720) > 500*1024:
            break
        print(f"      ⚠ 720p attempt {attempt}: {res.stderr.strip()[-150:]}")
        if attempt < 3: time.sleep(3)
    else:
        if os.path.exists(src): os.remove(src)
        return None, None

    # Encode 540p
    for attempt in range(1, 4):
        res = subprocess.run(
            ['ffmpeg', '-y', '-i', src,
             '-vf', 'scale=540:-2', '-c:v', 'libx264', '-crf', '26', '-preset', 'fast',
             '-fps_mode', 'cfr', '-af', 'aresample=async=1',
             '-maxrate', '1000k', '-bufsize', '2000k',
             '-c:a', 'aac', '-b:a', '96k', '-movflags', '+faststart',
             '-loglevel', 'warning', p540],
            capture_output=True, text=True, errors='ignore', timeout=180
        )
        if res.returncode == 0 and os.path.exists(p540) and os.path.getsize(p540) > 200*1024:
            break
        if attempt < 3: time.sleep(3)

    if os.path.exists(src): os.remove(src)
    return p720, (p540 if os.path.exists(p540) else None)


def upload_to_r2(r2, local_path, r2_key):
    try:
        size_mb = os.path.getsize(local_path) / (1024*1024)
        with open(local_path, 'rb') as f:
            r2.upload_fileobj(f, R2_BUCKET, r2_key,
                ExtraArgs={'ContentType': 'video/mp4', 'CacheControl': 'public, max-age=31536000'})
        print(f"      ✓ Uploaded {os.path.basename(r2_key)} ({size_mb:.1f} MB)")
        return f"{R2_PUBLIC}/{r2_key}"
    except Exception as e:
        print(f"      ✗ Upload failed: {e}")
        return None


def upload_cover(r2, cover_url, slug):
    if not cover_url: return ''
    key = f"dramas/covers/{slug}_cover_hq.jpg"
    try:
        r2.head_object(Bucket=R2_BUCKET, Key=key)
        return f"{R2_PUBLIC}/{key}"
    except Exception:
        pass
    try:
        raw = os.path.join(TEMP_DIR, f"raw_{slug}.tmp")
        jpg = os.path.join(TEMP_DIR, f"cov_{slug}.jpg")
        resp = requests.get(cover_url, headers=HDR, timeout=30, verify=False)
        if resp.ok:
            with open(raw, 'wb') as f: f.write(resp.content)
            subprocess.run(['ffmpeg', '-y', '-i', raw, '-update', '1', jpg], capture_output=True)
            if os.path.exists(jpg):
                with open(jpg, 'rb') as f:
                    r2.upload_fileobj(f, R2_BUCKET, key,
                        ExtraArgs={'ContentType': 'image/jpeg', 'CacheControl': 'public, max-age=31536000'})
                return f"{R2_PUBLIC}/{key}"
    except Exception as e:
        print(f"      Cover upload failed: {e}")
    return cover_url


def get_or_register_drama(r2, title, meta, total_eps, slug, genres):
    r = requests.get(f"{API_BASE}/api/dramas?limit=5000", timeout=30)
    if r.ok:
        data = r.json()
        dramas = data if isinstance(data, list) else data.get('dramas', [])
        for d in dramas:
            if title.lower() == d.get('title', '').lower():
                print(f"   ✓ Already in DB: {d['id']}")
                return d['id']

    print(f"   🖼 Uploading cover...")
    cover_url = meta.get('cover') or meta.get('image') or ''
    cover_r2  = upload_cover(r2, cover_url, slug)

    payload = {
        'title': title,
        'description': meta.get('description') or meta.get('introduction') or '',
        'cover': cover_r2,
        'genres': genres,
        'totalEpisodes': total_eps,
        'country': 'China',
        'language': 'Indonesia',
        'isActive': False,
        'status': 'pending',
        'isVip': False,
    }
    r = requests.post(f"{API_BASE}/api/admin/dramas", headers=ADMIN_HDR, json=payload, timeout=30)
    if r.ok:
        resp = r.json()
        drama_id = resp.get('id') or resp.get('drama', {}).get('id')
        print(f"   ✓ Drama registered! ID: {drama_id}")
        return drama_id
    print(f"   ✗ Registration failed: {r.status_code} {r.text[:200]}")
    return None


def register_episode(drama_id, ep_no, url_720, url_540):
    payload = {
        'episodeNumber': ep_no,
        'title': f'Episode {ep_no}',
        'videoUrl': url_720 or url_540 or '',
        'videoUrl540p': url_540 or '',
        'isVip': False, 'coinPrice': 0, 'isActive': False,
    }
    r = requests.post(f"{API_BASE}/api/admin/dramas/{drama_id}/episodes",
                      headers=ADMIN_HDR, json=payload, timeout=20)
    if r.ok: return r.json().get('id')
    r2 = requests.put(f"{API_BASE}/api/admin/dramas/{drama_id}/episodes/{ep_no}",
                      headers=ADMIN_HDR, json=payload, timeout=20)
    if r2.ok: return r2.json().get('id') or 'updated'
    return None


def process_drama(r2_client, d):
    print("\n" + "=" * 65)
    print(f"🎬 STARTING INGESTION: {d['slug']} (dramabox ID: {d['id']})")
    print("=" * 65)

    meta = fetch_drama_details(d['id'], d['lang'])
    if not meta:
        print("❌ Failed to fetch drama data!")
        return False

    title     = meta.get('title') or meta.get('name') or d['slug']
    total_eps = meta.get('chapterCount') or meta.get('totalEpisodes', 0)
    print(f"   Title: {title} | Total Episodes: {total_eps}")

    drama_id = get_or_register_drama(r2_client, title, meta, total_eps, d['slug'], d.get('genres', ['Drama']))
    if not drama_id:
        return False

    # Get already done episodes
    done_eps = {}
    er = requests.get(f"{API_BASE}/api/dramas/{drama_id}/episodes", timeout=15)
    if er.ok:
        for ep in er.json():
            done_eps[int(ep.get('episodeNumber', 0))] = ep.get('id')
    print(f"   Already in DB: {len(done_eps)} episodes\n")

    success_count = 0
    fail_count    = 0

    for ep_no in range(1, total_eps + 1):
        print(f"   📺 Episode {ep_no}/{total_eps}:")

        if ep_no in done_eps:
            print("      ✓ Already registered")
            success_count += 1
            continue

        # Fetch FRESH URL right before download
        video_url, subs = fetch_episode_url(d['id'], ep_no, d['lang'])
        if not video_url:
            print(f"      ❌ No stream URL for EP {ep_no}")
            fail_count += 1
            continue

        r2_key_720 = f"dramas/{d['slug']}/ep{ep_no:03d}_720p.mp4"
        r2_key_540 = f"dramas/{d['slug']}/ep{ep_no:03d}_540p.mp4"

        url_720 = url_540 = None
        try:
            r2_client.head_object(Bucket=R2_BUCKET, Key=r2_key_720)
            url_720 = f"{R2_PUBLIC}/{r2_key_720}"
        except Exception: pass
        try:
            r2_client.head_object(Bucket=R2_BUCKET, Key=r2_key_540)
            url_540 = f"{R2_PUBLIC}/{r2_key_540}"
        except Exception: pass

        if not url_720:
            local_720, local_540 = download_and_transcode(video_url, ep_no)
            if not local_720:
                print(f"      ❌ Transcode failed for EP {ep_no}")
                fail_count += 1
                continue
            url_720 = upload_to_r2(r2_client, local_720, r2_key_720)
            if local_540:
                url_540 = upload_to_r2(r2_client, local_540, r2_key_540)
            for f in [local_720, local_540]:
                if f and os.path.exists(f): os.remove(f)
            if not url_720:
                print(f"      ❌ R2 upload failed EP {ep_no}")
                fail_count += 1
                continue
        else:
            print("      ✓ Already in R2")

        ep_id = register_episode(drama_id, ep_no, url_720, url_540)
        if ep_id:
            print(f"      ✅ Done! ID: {ep_id}")
            success_count += 1
            done_eps[ep_no] = ep_id
        else:
            print(f"      ❌ DB register failed EP {ep_no}")
            fail_count += 1

    print("\n" + "=" * 65)
    print(f"🏁 INGESTION COMPLETE FOR {title}!")
    print(f"   Success: {success_count}/{total_eps} | Failed: {fail_count}/{total_eps}")
    print("=" * 65)
    return True


def main():
    print("=" * 65)
    print("STARTING DRAMABOX PIPELINE")
    print("=" * 65)
    r2 = get_r2()
    for d in DRAMAS:
        try:
            process_drama(r2, d)
        except Exception as e:
            print(f"❌ Error: {e}")
    print("\nDRAMABOX PIPELINE FINISHED!")


if __name__ == '__main__':
    main()
