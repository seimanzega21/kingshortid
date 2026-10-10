# -*- coding: utf-8 -*-
"""
Ingestion script for Mendidik Makhluk Buas (Sulih Suara)
Provider: dmboxx
ID: 42000029602
Total: 50 Episodes
"""
import requests
import boto3
import json
import time
import os
import subprocess
import urllib3
from botocore.config import Config

urllib3.disable_warnings()

# CONFIG
API_BASE  = 'http://141.11.160.187:3000'
ADMIN_KEY = '00ca04e3e2702be565d7bf44e783255247708289bce9b2fb6187a2e117f87fd14'
ADMIN_HDR = {'x-admin-key': ADMIN_KEY, 'Content-Type': 'application/json'}

R2_ENDPOINT = 'https://a142d3b29a5d64943cb251157e25eaf3.r2.cloudflarestorage.com'
R2_KEY_ID   = '07c99c897986ea52703c1285308d5e2c'
R2_SECRET   = '44788d376ffb216e1e73784b6fe1ff1423607928898a87c50819b52cdfc12e44'
R2_BUCKET   = 'shortlovers'
R2_PUBLIC   = 'https://stream.shortlovers.id'

TEMP_DIR = 'd:/kingshortid/temp_dmboxx'
os.makedirs(TEMP_DIR, exist_ok=True)

DRAMA_CONFIG = {
    "slug": "mendidik-makhluk-buas",
    "id": "42000029602",
    "lang": "id",
    "genres": ["Fantasi", "Sulih Suara", "Keluarga", "Wanita Mandiri"]
}

HDR = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64)'}

def get_r2():
    return boto3.client(
        's3', endpoint_url=R2_ENDPOINT,
        aws_access_key_id=R2_KEY_ID, aws_secret_access_key=R2_SECRET,
        config=Config(signature_version='s3v4'), region_name='auto'
    )

def fetch_drama_metadata(drama_id, lang):
    url = f"https://vidrama.asia/api/dmboxx?action=detail&id={drama_id}&lang={lang}"
    print(f"   🌐 Fetching drama metadata for {drama_id}...")
    for _ in range(5):
        try:
            r = requests.get(url, headers=HDR, timeout=20)
            if r.ok:
                res = r.json()
                if res.get('success'):
                    return res.get('data', {})
        except Exception as e:
            print(f"      ⚠ Metadata error: {e}")
        time.sleep(3)
    return None

def fetch_all_episodes(drama_id, lang):
    url = f"https://vidrama.asia/api/dmboxx?action=alleps&id={drama_id}&lang={lang}"
    print(f"   🌐 Fetching all episodes list for {drama_id}...")
    for _ in range(5):
        try:
            r = requests.get(url, headers=HDR, timeout=30)
            if r.ok:
                res = r.json()
                if res.get('success'):
                    return res.get('data', {}).get('episodes', [])
        except Exception as e:
            print(f"      ⚠ Alleps error: {e}")
        time.sleep(3)
    return []

def upload_cover(r2, cover_url, slug):
    if not cover_url: return ''
    key = f"dramas/covers/{slug}_cover_hq.jpg"
    try:
        r2.head_object(Bucket=R2_BUCKET, Key=key)
        print(f"   ✓ Cover already exists in R2: {key}")
        return f"{R2_PUBLIC}/{key}"
    except Exception:
        pass

    try:
        raw_cov = os.path.join(TEMP_DIR, f"cov_raw_{slug}.jpg")
        final_cov = os.path.join(TEMP_DIR, f"cov_{slug}.jpg")
        
        base_cover = cover_url.split('?')[0]
        resp = requests.get(base_cover, headers=HDR, timeout=30)
        if not resp.ok:
            resp = requests.get(cover_url, headers=HDR, timeout=30)
            
        if resp.ok:
            with open(raw_cov, 'wb') as f:
                f.write(resp.content)
                
            subprocess.run(['ffmpeg', '-y', '-i', raw_cov, '-update', '1', final_cov], capture_output=True)
            if os.path.exists(final_cov):
                with open(final_cov, 'rb') as f:
                    r2.upload_fileobj(f, R2_BUCKET, key,
                        ExtraArgs={'ContentType': 'image/jpeg', 'CacheControl': 'public, max-age=31536000'})
                for f in [raw_cov, final_cov]:
                    if os.path.exists(f): os.remove(f)
                print(f"   ✓ Cover uploaded to R2: {key}")
                return f"{R2_PUBLIC}/{key}"
    except Exception as e:
        print(f"   ⚠ Cover upload failed: {e}")
    return cover_url

def get_or_register_drama(r2, title, meta, total_eps, slug, genres):
    r = requests.get(f"{API_BASE}/api/dramas?limit=5000", timeout=30)
    if r.ok:
        data = r.json()
        dramas = data if isinstance(data, list) else data.get('dramas', [])
        for d in dramas:
            if title.lower() == d.get('title', '').lower():
                print(f"   ✓ Drama already in DB: {d['id']}")
                return d['id']

    print(f"   🖼 Processing cover...")
    cover_url = meta.get('cover') or ''
    cover_r2  = upload_cover(r2, cover_url, slug)

    payload = {
        'title': title,
        'description': meta.get('description') or 'No description available',
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

def download_file(url, local_path, min_size=200*1024):
    for attempt in range(1, 4):
        try:
            resp = requests.get(url, headers=HDR, stream=True, timeout=60)
            if resp.ok:
                with open(local_path, 'wb') as f:
                    for chunk in resp.iter_content(chunk_size=1024*1024):
                        if chunk:
                            f.write(chunk)
                if os.path.exists(local_path) and os.path.getsize(local_path) >= min_size:
                    return True
            print(f"      ⚠ DL attempt {attempt} failed, status: {resp.status_code}")
        except Exception as e:
            print(f"      ⚠ DL error attempt {attempt}: {e}")
        time.sleep(2)
    return False

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

def finalize_drama(drama_id, total_eps):
    print(f"   🎉 Finalizing drama {drama_id} (isActive=True, status=completed)...")
    payload = {
        'isActive': True,
        'status': 'completed',
        'totalEpisodes': total_eps
    }
    r = requests.patch(f"{API_BASE}/api/dramas/{drama_id}", headers=ADMIN_HDR, json=payload, timeout=20)
    if r.ok:
        print(f"   ✓ Drama activated and marked as completed!")
    else:
        print(f"   ⚠ Failed to finalize drama: {r.status_code} {r.text[:100]}")

def main():
    print("=" * 65)
    print("STARTING DMBOXX INGESTION: Mendidik Makhluk Buas")
    print("=" * 65)
    r2 = get_r2()
    cfg = DRAMA_CONFIG

    meta = fetch_drama_metadata(cfg['id'], cfg['lang'])
    if not meta:
        print("❌ Failed to fetch drama metadata!")
        return

    title = meta.get('title') or 'Mendidik Makhluk Buas (Sulih Suara)'
    all_eps_data = fetch_all_episodes(cfg['id'], cfg['lang'])
    if not all_eps_data:
        print("❌ Failed to fetch episodes list!")
        return

    total_eps = len(all_eps_data)
    print(f"   Title: {title} | Total Episodes: {total_eps}")

    drama_id = get_or_register_drama(r2, title, meta, total_eps, cfg['slug'], cfg['genres'])
    if not drama_id:
        return

    # Check already registered episodes in DB
    done_eps = {}
    er = requests.get(f"{API_BASE}/api/dramas/{drama_id}/episodes", timeout=15)
    if er.ok:
        for ep in er.json():
            done_eps[int(ep.get('episodeNumber', 0))] = ep.get('id')
    print(f"   Already in DB: {len(done_eps)} episodes\n")

    success_count = len(done_eps)
    fail_count = 0

    for item in all_eps_data:
        ep_no = item.get('episode')
        print(f"   📺 Episode {ep_no}/{total_eps}:")
        if ep_no in done_eps:
            print("      ✓ Already registered in DB")
            continue

        url_720_src = None
        url_540_src = None
        for q in item.get('qualities', []):
            label = str(q.get('label', '')).lower()
            if '720' in label:
                url_720_src = q.get('url')
            elif '540' in label:
                url_540_src = q.get('url')

        if not url_720_src:
            url_720_src = item.get('videoUrl')

        r2_key_720 = f"dramas/{cfg['slug']}/ep{ep_no:03d}_720p.mp4"
        r2_key_540 = f"dramas/{cfg['slug']}/ep{ep_no:03d}_540p.mp4"

        url_720 = url_540 = None
        try:
            r2.head_object(Bucket=R2_BUCKET, Key=r2_key_720)
            url_720 = f"{R2_PUBLIC}/{r2_key_720}"
        except Exception: pass
        try:
            r2.head_object(Bucket=R2_BUCKET, Key=r2_key_540)
            url_540 = f"{R2_PUBLIC}/{r2_key_540}"
        except Exception: pass

        if not url_720 and url_720_src:
            local_720 = os.path.join(TEMP_DIR, f"{cfg['slug']}_ep{ep_no:03d}_720p.mp4")
            if download_file(url_720_src, local_720, min_size=500*1024):
                url_720 = upload_to_r2(r2, local_720, r2_key_720)
            if os.path.exists(local_720):
                os.remove(local_720)

        if not url_540 and url_540_src:
            local_540 = os.path.join(TEMP_DIR, f"{cfg['slug']}_ep{ep_no:03d}_540p.mp4")
            if download_file(url_540_src, local_540, min_size=200*1024):
                url_540 = upload_to_r2(r2, local_540, r2_key_540)
            if os.path.exists(local_540):
                os.remove(local_540)

        if not url_720 and not url_540:
            print(f"      ❌ Failed to prepare video for EP {ep_no}")
            fail_count += 1
            continue

        ep_id = register_episode(drama_id, ep_no, url_720, url_540)
        if ep_id:
            print(f"      ✅ Done! ID: {ep_id}")
            success_count += 1
            done_eps[ep_no] = ep_id
        else:
            print(f"      ❌ DB register failed EP {ep_no}")
            fail_count += 1

    print("\n" + "=" * 65)
    print(f"🏁 INGESTION RESULT FOR {title}!")
    print(f"   Success: {success_count}/{total_eps} | Failed: {fail_count}/{total_eps}")
    print("=" * 65)

    if success_count == total_eps:
        finalize_drama(drama_id, total_eps)

if __name__ == '__main__':
    main()
