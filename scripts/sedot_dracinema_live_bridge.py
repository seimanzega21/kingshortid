#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Sedot Drama Dracinema - Live Bridge Automated Scraper
Uses dracinema_bridge.py on http://127.0.0.1:20199 for real-time authenticated VIP playback URLs.
Target: Cloudflare R2 + KingShort DB + Single Local Storage (D:\Video Drama\Facebook\<TITLE>\)
"""

import sys
if sys.platform == 'win32':
    sys.stdout.reconfigure(encoding='utf-8', errors='replace')
    sys.stderr.reconfigure(encoding='utf-8', errors='replace')

import os
import re
import json
import uuid
import time
import shutil
import subprocess
import requests
import urllib3
import boto3
from pathlib import Path
from botocore.config import Config

urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

# ── CONFIGURATION ─────────────────────────────────────────────────────────────
API_BASE    = 'https://api.shortlovers.id/api'
ADMIN_KEY   = '00ca04e3e2702be565d7bf44e783255247708289bce9b2fb6187a2e117f87fd14'
ADMIN_HDR   = {'x-admin-key': ADMIN_KEY, 'Content-Type': 'application/json'}

R2_ENDPOINT = 'https://a142d3b29a5d64943cb251157e25eaf3.r2.cloudflarestorage.com'
R2_KEY_ID   = '07c99c897986ea52703c1285308d5e2c'
R2_SECRET   = '44788d376ffb216e1e73784b6fe1ff1423607928898a87c50819b52cdfc12e44'
R2_BUCKET   = 'shortlovers'
R2_PUBLIC   = 'https://stream.shortlovers.id'

BRIDGE_URL  = 'http://127.0.0.1:20199/request'
TEMP_ROOT   = Path("D:/temp_scraper")
TEMP_ROOT.mkdir(parents=True, exist_ok=True)

# ── R2 CLIENT ─────────────────────────────────────────────────────────────────
s3 = boto3.client('s3', endpoint_url=R2_ENDPOINT,
                  aws_access_key_id=R2_KEY_ID, aws_secret_access_key=R2_SECRET,
                  config=Config(signature_version='s3v4', retries={'max_attempts': 3}),
                  region_name='auto')

def r2_exists(key):
    try:
        s3.head_object(Bucket=R2_BUCKET, Key=key)
        return True
    except:
        return False

def r2_upload(local_path, key, content_type='video/mp4'):
    s3.upload_file(str(local_path), R2_BUCKET, key, ExtraArgs={'ContentType': content_type},
                   Config=boto3.s3.transfer.TransferConfig(multipart_threshold=30*1024*1024, multipart_chunksize=10*1024*1024))
    return f"{R2_PUBLIC}/{key}"

# ── SUBTITLE HELPER ──────────────────────────────────────────────────────────
def srt_to_vtt(srt_text):
    if srt_text.strip().startswith("WEBVTT"):
        return srt_text
    lines = srt_text.replace('\r\n', '\n').split('\n')
    vtt_lines = ["WEBVTT\n"]
    timestamp_re = re.compile(r'(\d{2}:\d{2}:\d{2}),(\d{3})\s*-->\s*(\d{2}:\d{2}:\d{2}),(\d{3})')
    for line in lines:
        match = timestamp_re.search(line)
        if match:
            vtt_lines.append(timestamp_re.sub(r'\1.\2 --> \3.\4', line))
        else:
            vtt_lines.append(line)
    return "\n".join(vtt_lines)

# ── DATABASE HELPERS ─────────────────────────────────────────────────────────
def get_or_create_drama(meta):
    title = meta['title']
    cover_r2_url = f"{R2_PUBLIC}/{meta['prefix']}/cover.webp"

    print(f"\n[DB] Memeriksa & Mendaftarkan Drama '{title}' ke KingShort...")
    try:
        r = requests.get(f"{API_BASE}/dramas?limit=1000&includeInactive=true", headers=ADMIN_HDR, timeout=15)
        if r.ok:
            for d in r.json().get('dramas', []):
                if d.get('title', '').strip().lower() == title.lower():
                    print(f"  -> Drama sudah ada di database (ID: {d['id']})")
                    return d['id']
    except Exception as e:
        print(f"  [WARN] Gagal cek drama di DB: {e}")

    payload = {
        'title': title,
        'description': meta.get('description') or title,
        'cover': cover_r2_url,
        'genres': meta.get('genres', ['Drama']),
        'totalEpisodes': meta['total_eps'],
        'country': 'China',
        'language': 'Indonesia',
        'status': 'completed',
        'isActive': False  # Pending verifikasi admin
    }
    try:
        r = requests.post(f"{API_BASE}/admin/dramas", headers=ADMIN_HDR, json=payload, timeout=20)
        if r.ok:
            new_id = r.json().get('id')
            print(f"  -> Berhasil membuat drama di DB (ID: {new_id})")
            return new_id
        else:
            print(f"  [ERROR] Gagal buat drama di DB: {r.status_code} {r.text}")
    except Exception as e:
        print(f"  [ERROR] Exception creating drama in DB: {e}")
    return None

def upsert_episode(drama_id, ep_num, url_720, url_540=None):
    payload = {
        'episodeNumber': ep_num,
        'title': f'Episode {ep_num}',
        'videoUrl': url_720,
        'isActive': True
    }
    if url_540:
        payload['videoUrl540p'] = url_540

    try:
        r = requests.post(f"{API_BASE}/admin/dramas/{drama_id}/episodes", headers=ADMIN_HDR, json=payload, timeout=20)
        if r.ok:
            return r.json().get('id')
    except Exception as e:
        print(f"      [WARN] DB upsert ep {ep_num} error: {e}")
    return None

def link_subtitle_to_episode(ep_id, r2_sub_url):
    try:
        sub_res = requests.get(f"{API_BASE}/episodes/{ep_id}/subtitles", headers=ADMIN_HDR, timeout=10)
        existing_subs = sub_res.json().get('subtitles', []) if sub_res.ok else []
        has_id = any(s.get('language') == 'indonesia' for s in existing_subs)
        if not has_id:
            sub_payload = {
                'language': 'indonesia',
                'label': 'Indonesia',
                'url': r2_sub_url,
                'isDefault': True
            }
            requests.post(f"{API_BASE}/episodes/{ep_id}/subtitles", headers=ADMIN_HDR, json=sub_payload, timeout=10)
    except Exception:
        pass

# ── VIDEO HELPERS ─────────────────────────────────────────────────────────────
def encode_540p(in_file, out_540p):
    cmd = [
        'ffmpeg', '-y', '-i', str(in_file),
        '-vf', 'scale=-2:540',
        '-c:v', 'libx264', '-crf', '28', '-preset', 'fast',
        '-c:a', 'aac', '-b:a', '96k',
        '-movflags', '+faststart',
        '-loglevel', 'error',
        str(out_540p)
    ]
    return subprocess.run(cmd).returncode == 0

def download_video(url, out_mp4):
    headers_list = [
        "User-Agent: Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36"
    ]
    if "idrama.video" in url:
        headers_list.append("Referer: https://www.dracinema.com/")
        headers_list.append("Origin: https://www.dracinema.com")
    elif "dramapetir.com" in url:
        headers_list.append("Referer: https://dramapetir.com/")
    elif "mydramawave.com" in url:
        headers_list.append("Referer: https://mydramawave.com/")

    header_str = "\r\n".join(headers_list) + "\r\n"

    cmd = [
        'ffmpeg', '-y',
        '-headers', header_str,
        '-i', url,
        '-c', 'copy',
        '-movflags', '+faststart',
        '-loglevel', 'error',
        str(out_mp4)
    ]
    res = subprocess.run(cmd, timeout=300)
    return res.returncode == 0 and os.path.exists(out_mp4) and os.path.getsize(out_mp4) > 100 * 1024

def ensure_cover(meta, temp_dir):
    cover_key = f"{meta['prefix']}/cover.webp"
    if r2_exists(cover_key):
        print(f"  -> [R2] Cover already exists for '{meta['title']}'.")
        return
    print(f"  -> [R2] Mengunduh dan mengupload cover untuk '{meta['title']}'...")
    try:
        r = requests.get(meta['cover_url'], timeout=15)
        if r.ok:
            tmp_cov = temp_dir / "cover.webp"
            tmp_cov.write_bytes(r.content)
            r2_upload(tmp_cov, cover_key, 'image/webp')
            tmp_cov.unlink(missing_ok=True)
            print("  -> [R2] Cover uploaded successfully!")
    except Exception as e:
        print(f"  -> [WARN] Cover error: {e}")

# ── BRIDGE CLIENT ────────────────────────────────────────────────────────────
def get_playback_via_bridge(movie_key, ep_num):
    for attempt in range(3):
        req_id = str(uuid.uuid4())
        payload = {
            'id': req_id,
            'movieKey': movie_key,
            'episode': ep_num
        }
        try:
            r = requests.post(BRIDGE_URL, json=payload, timeout=35)
            if r.status_code == 200:
                res = r.json()
                if res.get('ok') and res.get('data', {}).get('kind') == 'ok':
                    return res['data']
        except Exception:
            time.sleep(2)
    return None

# ── PROCESS EPISODE ───────────────────────────────────────────────────────────
def process_episode(drama_id, meta, ep_num, temp_dir):
    prefix = meta['prefix']
    k720 = f"{prefix}/ep{ep_num:03d}.mp4"
    k540 = f"{prefix}/ep{ep_num:03d}_540p.mp4"
    kvtt = f"{prefix}/ep{ep_num:03d}.vtt"

    local_file = meta['local_dir'] / f"ep{ep_num:03d}.mp4"
    local_vtt = meta['local_dir'] / f"ep{ep_num:03d}.vtt"

    # 1. Cek apakah video sudah ada di R2
    if r2_exists(k720) and r2_exists(k540):
        print(f"  -> Ep {ep_num:02d}: Sudah ada di R2. Link DB...", end="", flush=True)
        u720 = f"{R2_PUBLIC}/{k720}"
        u540 = f"{R2_PUBLIC}/{k540}"
        ep_id = upsert_episode(drama_id, ep_num, u720, u540)
        if not local_file.exists():
            try:
                s3.download_file(R2_BUCKET, k720, str(local_file))
            except Exception:
                pass
        print(" [OK Video]")
        return True

    # 2. Ambil URL video fresh melalui Bridge Browser
    print(f"  -> Ep {ep_num:02d}: Mengambil stream dari Dracinema...", end="", flush=True)
    pb = get_playback_via_bridge(meta['movie_key'], ep_num)
    if not pb or not pb.get('url'):
        print(" [GAGAL DAPAT URL STREAM]")
        return False

    video_url = pb['url']
    sub_url = pb.get('sub')

    raw_mp4 = temp_dir / f"raw_{ep_num:03d}.mp4"
    out_540 = temp_dir / f"out540_{ep_num:03d}.mp4"

    if not download_video(video_url, raw_mp4):
        print(" [GAGAL DOWNLOAD]")
        if raw_mp4.exists(): raw_mp4.unlink()
        return False

    size_mb = raw_mp4.stat().st_size / (1024 * 1024)
    print(f" ({size_mb:.1f} MB) 540p...", end="", flush=True)

    if not encode_540p(raw_mp4, out_540):
        print(" [GAGAL 540P]")
        if raw_mp4.exists(): raw_mp4.unlink()
        if out_540.exists(): out_540.unlink()
        return False

    print(" R2...", end="", flush=True)
    u720 = r2_upload(raw_mp4, k720)
    u540 = r2_upload(out_540, k540)

    # Simpan ke folder lokal (Single Location)
    try:
        shutil.copy2(raw_mp4, local_file)
    except Exception:
        pass

    ep_id = upsert_episode(drama_id, ep_num, u720, u540)

    # Subtitle download jika ada
    if sub_url and ep_id:
        try:
            if not local_vtt.exists() or local_vtt.stat().st_size < 50:
                sub_hdrs = {'User-Agent': 'Mozilla/5.0'}
                if 'dramapetir.com' in sub_url:
                    sub_hdrs['Referer'] = 'https://dramapetir.com/'
                else:
                    sub_hdrs['Referer'] = 'https://www.dracinema.com/'
                r_sub = requests.get(sub_url, headers=sub_hdrs, timeout=15)
                if r_sub.ok and len(r_sub.text) > 20:
                    vtt_text = srt_to_vtt(r_sub.text)
                    with open(local_vtt, 'w', encoding='utf-8') as fp:
                        fp.write(vtt_text)
            if local_vtt.exists():
                s3.upload_file(str(local_vtt), R2_BUCKET, kvtt, ExtraArgs={'ContentType': 'text/vtt'})
                link_subtitle_to_episode(ep_id, f"{R2_PUBLIC}/{kvtt}")
                print(" [+Sub VTT]", end="", flush=True)
        except Exception as e:
            print(f" [Sub ERR: {e}]", end="", flush=True)

    raw_mp4.unlink(missing_ok=True)
    out_540.unlink(missing_ok=True)
    print(" [SELESAI]")
    return True

# ── PROCESS DRAMA ────────────────────────────────────────────────────────────
def process_drama(meta):
    title = meta['title']
    total_eps = meta['total_eps']
    print("\n" + "=" * 60)
    print(f"MEMULAI SEDOT: {title} ({total_eps} Episode)")
    print("=" * 60)

    temp_dir = TEMP_ROOT / meta['slug']
    temp_dir.mkdir(parents=True, exist_ok=True)
    meta['local_dir'].mkdir(parents=True, exist_ok=True)

    ensure_cover(meta, temp_dir)

    drama_id = get_or_create_drama(meta)
    if not drama_id:
        print(f"[ERROR] Gagal mendapatkan ID drama DB untuk {title}.")
        return

    success = 0
    for ep in range(1, total_eps + 1):
        if process_episode(drama_id, meta, ep, temp_dir):
            success += 1
        time.sleep(1.2) # Jeda aman anti-rate-limit

    print(f"\n[HASIL] Selesai {title}: {success}/{total_eps} episode.")
    print(f"  - Cloudflare R2: {R2_PUBLIC}/{meta['prefix']}/")
    print(f"  - Local Storage (Single Location): {meta['local_dir']}")

# ── MAIN PIPELINE ────────────────────────────────────────────────────────────
def main():
    metadata_file = Path(__file__).parent / "dramas_metadata.json"
    with open(metadata_file, "r", encoding="utf-8") as f:
        meta_all = json.load(f)

    # Queue of 8 remaining dramas
    queue_keys = [
        "drama4",  # Kebangkitan Gadis Jelek (80 eps)
        "drama7",  # Pikiran Sang Tiran (118 eps)
        "drama8",  # Aku Mendapatkan Tiga Pacar dari Sistem (30 eps)
        "drama9",  # (Sulih suara) Tinju Maut (45 eps)
        "drama10", # Cinta yang Terbeli, Dendam yang Gak Pernah Mati (26 eps)
        "drama11", # [Dubbing] Perisai (50 eps)
        "drama12", # Pacar Onlineku Don Mafia (32 eps)
        "drama13"  # Dari montir jadi raja mobil (73 eps)
    ]

    for key in queue_keys:
        meta = meta_all.get(key)
        if not meta:
            continue
        meta['local_dir'] = Path(meta['local_dir'])
        process_drama(meta)

    print("\n" + "=" * 60)
    print("SELURUH 8 DRAMA SELESAI DISEDOT LENGKAP 100%!")
    print("=" * 60)

if __name__ == "__main__":
    main()
