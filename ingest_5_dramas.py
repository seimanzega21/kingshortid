# -*- coding: utf-8 -*-
"""
Ingestion script for 5 requested Dotdrama titles:
1. Pulau Kiamat: Pewaris Darah Purba (51 eps)
2. Pangeran Dingin Kini Memanjakanku (66 eps)
3. Legenda Sang Raja Perang (56 eps)
4. Jatuh ke Pelukan Ayah Alpha Mantanku (50 eps)
5. Ratu Terjatuh, Permainan Dimulai (45 eps)
"""
import requests
import boto3
import sys
import json
import time
import os
import subprocess
import urllib3
import re
import urllib.parse
from botocore.config import Config

urllib3.disable_warnings()

# ─── CONFIG ────────────────────────────────────────────────────────────────
API_BASE     = 'http://141.11.160.187:3000'
ADMIN_KEY    = '00ca04e3e2702be565d7bf44e783255247708289bce9b2fb6187a2e117f87fd14'
ADMIN_HDR    = {'x-admin-key': ADMIN_KEY, 'Content-Type': 'application/json'}

R2_ENDPOINT  = 'https://a142d3b29a5d64943cb251157e25eaf3.r2.cloudflarestorage.com'
R2_KEY_ID    = '07c99c897986ea52703c1285308d5e2c'
R2_SECRET    = '44788d376ffb216e1e73784b6fe1ff1423607928898a87c50819b52cdfc12e44'
R2_BUCKET    = 'shortlovers'
R2_PUBLIC    = 'https://stream.shortlovers.id'

TEMP_DIR     = 'd:/kingshortid/temp_dotdrama_5batch'
os.makedirs(TEMP_DIR, exist_ok=True)

DRAMAS = [
    {
        "slug": "pulau-kiamat-pewaris-darah-purba",
        "id": "2072916449407352834",
        "lang": "id",
        "genres": ["Aksi", "Fantasi"]
    },
    {
        "slug": "pangeran-dingin-kini-memanjakanku",
        "id": "2071481268519649281",
        "lang": "id",
        "genres": ["Romantis", "Drama"]
    },
    {
        "slug": "legenda-sang-raja-perang",
        "id": "2084571179372765186",
        "lang": "id",
        "genres": ["Aksi", "Drama"]
    },
    {
        "slug": "jatuh-ke-pelukan-ayah-alpha-mantanku",
        "id": "2090371829822881794",
        "lang": "id",
        "genres": ["Romantis", "Drama"]
    },
    {
        "slug": "ratu-terjatuh-permainan-dimulai",
        "id": "2090260826665746433",
        "lang": "id",
        "genres": ["Drama", "Romantis"]
    }
]

# ─── HELPERS ───────────────────────────────────────────────────────────────
def get_r2():
    return boto3.client(
        's3', endpoint_url=R2_ENDPOINT,
        aws_access_key_id=R2_KEY_ID, aws_secret_access_key=R2_SECRET,
        config=Config(signature_version='s3v4'), region_name='auto'
    )

def fetch_drama_data(mid):
    url = f"https://vidrama.asia/api/dotdrama?action=detail&id={mid}&lang=id"
    print(f"   🌐 Fetching details for drama ID {mid} (dotdrama REST)...", flush=True)
    hdrs = {'User-Agent': 'Mozilla/5.0'}
    for attempt in range(1, 6):
        try:
            r = requests.get(url, headers=hdrs, timeout=20)
            if r.ok:
                return r.json()
        except Exception as e:
            print(f"      ⚠ Detail Connection error: {e}", flush=True)
        time.sleep(3)
    return None

def download_and_transcode(video_url, ep_no, slug):
    local_source = os.path.join(TEMP_DIR, f"{slug}_source_ep{ep_no:03d}.mp4")
    local_720 = os.path.join(TEMP_DIR, f"{slug}_ep{ep_no:03d}_720p.mp4")
    local_540 = os.path.join(TEMP_DIR, f"{slug}_ep{ep_no:03d}_540p.mp4")

    for f in [local_source, local_720, local_540]:
        if os.path.exists(f):
            try: os.remove(f)
            except: pass

    success_dl = False
    for attempt in range(1, 4):
        try:
            cmd_dl = [
                'ffmpeg', '-y',
                '-headers', 'User-Agent: Mozilla/5.0\r\n',
                '-i', video_url,
                '-c', 'copy',
                '-loglevel', 'warning',
                local_source
            ]
            res = subprocess.run(cmd_dl, capture_output=True, text=True, errors='ignore', timeout=300)
            if res.returncode == 0 and os.path.exists(local_source) and os.path.getsize(local_source) > 500*1024:
                success_dl = True
                break
            else:
                print(f"      ⚠ Source DL Attempt {attempt} failed: {res.stderr.strip()[-200:]}", flush=True)
        except Exception as e:
            print(f"      ⚠ Source DL Connection error (attempt {attempt}/3): {e}", flush=True)
        time.sleep(3)

    if not success_dl:
        return None, None

    success_720 = False
    for attempt in range(1, 4):
        cmd = [
            'ffmpeg', '-y',
            '-i', local_source,
            '-vf', 'scale=720:-2', '-c:v', 'libx264', '-crf', '23', '-preset', 'fast', '-fps_mode', 'cfr', '-af', 'aresample=async=1',
            '-maxrate', '1500k', '-bufsize', '3000k', '-c:a', 'aac', '-b:a', '128k',
            '-movflags', '+faststart',
            '-loglevel', 'warning',
            local_720
        ]
        res = subprocess.run(cmd, capture_output=True, text=True, errors='ignore', timeout=180)
        if res.returncode == 0 and os.path.exists(local_720) and os.path.getsize(local_720) > 500*1024:
            success_720 = True
            break
        else:
            print(f"      ⚠ 720p Attempt {attempt} failed: {res.stderr.strip()[-200:]}", flush=True)
            if attempt < 3: time.sleep(3)

    if not success_720:
        if os.path.exists(local_source):
            try: os.remove(local_source)
            except: pass
        return None, None

    success_540 = False
    for attempt in range(1, 4):
        cmd = [
            'ffmpeg', '-y',
            '-i', local_source,
            '-vf', 'scale=540:-2', '-c:v', 'libx264', '-crf', '26', '-preset', 'fast', '-fps_mode', 'cfr', '-af', 'aresample=async=1',
            '-maxrate', '1000k', '-bufsize', '2000k', '-c:a', 'aac', '-b:a', '96k',
            '-movflags', '+faststart',
            '-loglevel', 'warning',
            local_540
        ]
        res = subprocess.run(cmd, capture_output=True, text=True, errors='ignore', timeout=180)
        if res.returncode == 0 and os.path.exists(local_540) and os.path.getsize(local_540) > 300*1024:
            success_540 = True
            break
        else:
            print(f"      ⚠ 540p Attempt {attempt} failed: {res.stderr.strip()[-200:]}", flush=True)
            if attempt < 3: time.sleep(3)

    if os.path.exists(local_source):
        try: os.remove(local_source)
        except: pass

    if not success_540:
        return local_720, None

    return local_720, local_540

def upload_to_r2(r2, local_path, r2_key):
    try:
        size_mb = os.path.getsize(local_path) / (1024*1024)
        with open(local_path, 'rb') as f:
            r2.upload_fileobj(
                f, R2_BUCKET, r2_key,
                ExtraArgs={'ContentType': 'video/mp4', 'CacheControl': 'public, max-age=31536000'}
            )
        print(f"      ✓ Uploaded {os.path.basename(r2_key)} ({size_mb:.1f} MB)", flush=True)
        return f"{R2_PUBLIC}/{r2_key}"
    except Exception as e:
        print(f"      ✗ Upload failed: {e}", flush=True)
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
        r = requests.get(cover_url, headers={'User-Agent': 'Mozilla/5.0'}, timeout=30, verify=False)
        if r.ok:
            raw_path = f"{TEMP_DIR}/raw_cover_{slug}.tmp"
            jpg_path = f"{TEMP_DIR}/cover_{slug}.jpg"
            with open(raw_path, 'wb') as out:
                out.write(r.content)

            subprocess.run(['ffmpeg', '-y', '-i', raw_path, '-update', '1', jpg_path], capture_output=True)

            if os.path.exists(jpg_path):
                with open(jpg_path, 'rb') as out:
                    r2.upload_fileobj(
                        out, R2_BUCKET, key,
                        ExtraArgs={'ContentType': 'image/jpeg', 'CacheControl': 'public, max-age=31536000'}
                    )
                for f in [raw_path, jpg_path]:
                    if os.path.exists(f):
                        try: os.remove(f)
                        except: pass
                return f"{R2_PUBLIC}/{key}"
    except Exception as e:
        print(f"      Cover upload failed: {e}", flush=True)
    return cover_url

def get_or_register_drama(title, metadata, total_eps, slug, genres):
    r = requests.get(f"{API_BASE}/api/dramas?limit=5000", timeout=15)
    if r.ok:
        data = r.json()
        dramas = data if isinstance(data, list) else data.get('dramas', [])
        for d in dramas:
            if title.lower() == d.get('title', '').lower():
                print(f"   ✓ Drama already registered in DB: {d['id']}", flush=True)
                return d['id']

    print(f"   🖼 Uploading cover image...", flush=True)
    r2 = get_r2()
    cover_url = metadata.get('cover') or metadata.get('image') or ''
    cover_r2 = upload_cover(r2, cover_url, slug)

    payload = {
        'title': title,
        'description': metadata.get('description') or '',
        'cover': cover_r2,
        'genres': genres,
        'totalEpisodes': total_eps,
        'country': 'Indonesia',
        'language': 'Indonesia',
        'isActive': False,
        'status': 'pending',
        'isVip': False,
    }
    r = requests.post(f"{API_BASE}/api/admin/dramas", headers=ADMIN_HDR, json=payload, timeout=30)
    if r.ok:
        resp = r.json()
        drama_id = resp.get('id') or resp.get('drama', {}).get('id')
        print(f"   ✓ New drama registered! ID: {drama_id}", flush=True)
        return drama_id
    else:
        print(f"   ✗ Drama registration failed: {r.status_code} {r.text[:200]}", flush=True)
        return None

def register_episode(drama_id, ep_no, url_720, url_540):
    payload = {
        'episodeNumber': ep_no,
        'title': f'Episode {ep_no}',
        'videoUrl': url_720 or url_540 or '',
        'videoUrl540p': url_540 or '',
        'isVip': False,
        'coinPrice': 0,
        'isActive': False,
    }
    r = requests.post(
        f"{API_BASE}/api/admin/dramas/{drama_id}/episodes",
        headers=ADMIN_HDR, json=payload, timeout=20
    )
    if r.ok:
        return r.json().get('id')
    else:
        r2 = requests.put(
            f"{API_BASE}/api/admin/dramas/{drama_id}/episodes/{ep_no}",
            headers=ADMIN_HDR, json=payload, timeout=20
        )
        if r2.ok:
            return r2.json().get('id') or 'updated'
    return None

def process_drama(r2, d):
    print("\n" + "=" * 65, flush=True)
    print(f"🎬 STARTING INGESTION: {d['slug']} (ID: {d['id']})", flush=True)
    print("=" * 65, flush=True)

    meta = fetch_drama_data(d['id'])
    if not meta:
        print(f"❌ Failed to fetch drama details for {d['slug']}! Skipping.", flush=True)
        return False

    title = meta.get('title') or d['slug'].replace('-', ' ').title()
    eps_list = meta.get('episodes', [])
    total_eps = len(eps_list) or meta.get('totalEpisodes', 50)
    print(f"   Drama Title: {title}", flush=True)
    print(f"   Total Episodes: {total_eps}", flush=True)

    drama_id = get_or_register_drama(title, meta, total_eps, d['slug'], d.get('genres', ['Drama']))
    if not drama_id:
        print(f"❌ Failed to register drama {d['slug']}! Skipping.", flush=True)
        return False

    done_eps = {}
    er = requests.get(f"{API_BASE}/api/dramas/{drama_id}/episodes?includeInactive=true", timeout=15)
    if er.ok:
        for ep in er.json():
            done_eps[int(ep.get('episodeNumber', 0))] = ep.get('id')
    print(f"   Already done in DB: {len(done_eps)} episodes", flush=True)

    success_count = 0
    fail_count = 0

    for ep in eps_list:
        ep_no = int(ep.get('index', 0))
        if not ep_no: continue

        print(f"\n   📺 Episode {ep_no}/{total_eps}:", flush=True)

        if ep_no in done_eps:
            print("      ✓ Video already registered", flush=True)
            success_count += 1
            continue

        qualities = ep.get('qualities', [])
        video_url = None
        for q in qualities:
            if '720' in q.get('quality', '') and q.get('originalUrl'):
                video_url = q.get('originalUrl')
                break

        if not video_url:
            for q in qualities:
                if q.get('originalUrl'):
                    video_url = q.get('originalUrl')
                    break
        if not video_url:
            video_url = ep.get('originalUrl') or ep.get('videoUrl')

        if video_url and video_url.startswith('/api/video-proxy'):
            parsed = urllib.parse.urlparse(video_url)
            qs = urllib.parse.parse_qs(parsed.query)
            if 'url' in qs:
                video_url = qs['url'][0]

        if not video_url:
            print(f"      ❌ Failed to fetch stream URL for EP {ep_no}", flush=True)
            fail_count += 1
            continue

        r2_key_720 = f"dramas/{d['slug']}/ep{ep_no:03d}_720p.mp4"
        r2_key_540 = f"dramas/{d['slug']}/ep{ep_no:03d}_540p.mp4"

        url_720 = None
        url_540 = None

        try:
            r2.head_object(Bucket=R2_BUCKET, Key=r2_key_720)
            url_720 = f"{R2_PUBLIC}/{r2_key_720}"
        except Exception:
            pass

        try:
            r2.head_object(Bucket=R2_BUCKET, Key=r2_key_540)
            url_540 = f"{R2_PUBLIC}/{r2_key_540}"
        except Exception:
            pass

        if not url_720:
            local_720, local_540 = download_and_transcode(video_url, ep_no, d['slug'])
            if not local_720:
                print(f"      ❌ Download/transcode failed for EP {ep_no}", flush=True)
                fail_count += 1
                continue

            url_720 = upload_to_r2(r2, local_720, r2_key_720)
            if local_540:
                url_540 = upload_to_r2(r2, local_540, r2_key_540)

            for f in [local_720, local_540]:
                if f and os.path.exists(f):
                    try: os.remove(f)
                    except: pass

            if not url_720:
                print(f"      ❌ R2 upload failed for EP {ep_no}", flush=True)
                fail_count += 1
                continue
        else:
            print("      ✓ Already in R2", flush=True)

        ep_id = register_episode(drama_id, ep_no, url_720, url_540)
        if ep_id:
            print(f"      ✅ Video Done! ID: {ep_id}", flush=True)
            success_count += 1
            done_eps[ep_no] = ep_id
        else:
            print(f"      ❌ DB Registration failed for EP {ep_no}", flush=True)
            fail_count += 1

    print("\n" + "=" * 65, flush=True)
    print(f"🏁 INGESTION COMPLETE FOR {title}!", flush=True)
    print(f"   Success: {success_count}/{total_eps}", flush=True)
    print(f"   Failed:  {fail_count}/{total_eps}", flush=True)
    print("=" * 65, flush=True)
    return True

def main():
    print("=" * 65, flush=True)
    print(f"STARTING BATCH INGESTION FOR {len(DRAMAS)} DOTDRAMA DRAMAS", flush=True)
    print("=" * 65, flush=True)
    r2 = get_r2()
    for idx, d in enumerate(DRAMAS, 1):
        print(f"\n[{idx}/{len(DRAMAS)}] Processing drama: {d['slug']}...", flush=True)
        try:
            process_drama(r2, d)
        except Exception as e:
            print(f"❌ Error processing drama {d['slug']}: {e}", flush=True)
    print("\n🎉 ALL 5 DRAMAS HAVE BEEN PROCESSED!", flush=True)

if __name__ == '__main__':
    main()
