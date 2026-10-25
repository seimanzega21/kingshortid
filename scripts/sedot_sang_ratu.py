#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Sedot Drama: Sang Ratu Mengasingkanku (Sulih Suara) - 54 Episode
Provider: Dracinema (DramaWave / video-v6.mydramawave.com)
Features:
- Video Full HD 1080x1920 dengan Audio Sulih Suara (Dubbing Bahasa Indonesia).
- Subtitle Bahasa Indonesia (WebVTT) resmi dari Dracinema.
- Transcode 540p faststart untuk hemat kuota & streaming cepat.
- Upload 720p/1080p, 540p faststart, dan VTT ke Cloudflare R2 (stream.shortlovers.id/dracinema/sang-ratu-mengasingkanku-sulih-suara/).
- Daftarkan ke database KingShort (api.shortlovers.id) & activate drama.
- Simpan file lokal strictly di 1 tempat: D:\\Video Drama\\Facebook\\Sang Ratu Mengasingkanku (Sulih Suara)\\
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

TITLE       = 'Sang Ratu Mengasingkanku (Sulih Suara)'
SLUG        = 'sang-ratu-mengasingkanku-sulih-suara'
MOVIE_KEY   = 'sang-ratu-mengasingkanku-sulih-suara-dw_fp0TLauey9'
TOTAL_EPS   = 54
COVER_URL   = 'https://img.mebilu.com/xt3sfmxGlqIK-KnG_MS1r951sZ-_i7Gm27xTmlQZyCGiPQRprK7aCBGlulEDKhKTeg.webp'
GENRES      = ['Sulih Suara', 'Fantasi', 'Pahlawan Kembali', 'Drama', 'Aksi']
DESC        = 'Setelah dikhianati dan diasingkan ratu yang pernah dilindunginya, Rayne Ashford, seorang pria yang dianggap tak berguna membangkitkan kekuatan legendaris sebagai Penjaga Avalon. Saat kerajaannya terancam kehancuran, mereka baru menyadari bahwa sosok yang mereka buang adalah satu-satunya penyelamat kerajaan!'
PREFIX      = f"dracinema/{SLUG}"

LOCAL_DIR   = Path("D:/Video Drama/Facebook") / TITLE
LOCAL_DIR.mkdir(parents=True, exist_ok=True)

TEMP_DIR    = Path("D:/temp_scraper") / SLUG
TEMP_DIR.mkdir(parents=True, exist_ok=True)

DUMP_FILE   = Path("D:/temp_scraper/sang_ratu_dump.json")
BRIDGE_URL  = 'http://127.0.0.1:20199/request'

HEADERS_STR = "Referer: https://mydramawave.com/\r\nUser-Agent: Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36\r\n"

# ── R2 CLIENT ─────────────────────────────────────────────────────────────────
s3 = boto3.client('s3', endpoint_url=R2_ENDPOINT,
                  aws_access_key_id=R2_KEY_ID, aws_secret_access_key=R2_SECRET,
                  config=Config(signature_version='s3v4', retries={'max_attempts': 3}),
                  region_name='auto')

def r2_exists(key):
    try:
        s3.head_object(Bucket=R2_BUCKET, Key=key)
        return True
    except Exception:
        return False

def r2_upload(local_path, key, content_type='video/mp4'):
    s3.upload_file(str(local_path), R2_BUCKET, key, ExtraArgs={'ContentType': content_type},
                   Config=boto3.s3.transfer.TransferConfig(multipart_threshold=30*1024*1024, multipart_chunksize=10*1024*1024))
    return f"{R2_PUBLIC}/{key}"

def ensure_cover():
    cover_key = f"{PREFIX}/cover.webp"
    if r2_exists(cover_key):
        print(f"  -> [R2] Cover already exists.")
        return
    print(f"  -> [R2] Mengunduh dan mengupload cover...")
    try:
        r = requests.get(COVER_URL, timeout=15)
        if r.ok:
            tmp_cov = TEMP_DIR / "cover.webp"
            tmp_cov.write_bytes(r.content)
            r2_upload(tmp_cov, cover_key, 'image/webp')
            tmp_cov.unlink(missing_ok=True)
            print("  -> [R2] Cover uploaded successfully!")
    except Exception as e:
        print(f"  -> [WARN] Cover error: {e}")

# ── DATABASE HELPERS ─────────────────────────────────────────────────────────
def get_or_create_drama():
    cover_r2_url = f"{R2_PUBLIC}/{PREFIX}/cover.webp"
    print(f"\n[DB] Memeriksa & Mendaftarkan Drama '{TITLE}' ke KingShort...")
    try:
        r = requests.get(f"{API_BASE}/dramas?limit=1000&includeInactive=true", headers=ADMIN_HDR, timeout=15)
        if r.ok:
            for d in r.json().get('dramas', []):
                if d.get('title', '').strip().lower() == TITLE.lower():
                    print(f"  -> Drama sudah ada di database (ID: {d['id']})")
                    # Pastikan active
                    requests.patch(f"{API_BASE}/dramas/{d['id']}", headers=ADMIN_HDR, json={'isActive': True, 'totalEpisodes': TOTAL_EPS})
                    return d['id']
    except Exception as e:
        print(f"  [WARN] Gagal cek drama di DB: {e}")

    payload = {
        'title': TITLE,
        'description': DESC,
        'cover': cover_r2_url,
        'genres': GENRES,
        'totalEpisodes': TOTAL_EPS,
        'country': 'Luar Negeri',
        'language': 'Indonesia',
        'status': 'completed',
        'isActive': True
    }
    try:
        r = requests.post(f"{API_BASE}/admin/dramas", headers=ADMIN_HDR, json=payload, timeout=20)
        if r.ok:
            new_id = r.json().get('id')
            print(f"  -> Berhasil membuat drama di DB (ID: {new_id})")
            requests.patch(f"{API_BASE}/dramas/{new_id}", headers=ADMIN_HDR, json={'isActive': True, 'totalEpisodes': TOTAL_EPS})
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

# ── SUBTITLE FORMATTER ────────────────────────────────────────────────────────
time_re = re.compile(r'(\d{2}:)?(\d{2}:\d{2}[.,]\d{3})\s*-->\s*(\d{2}:)?(\d{2}:\d{2}[.,]\d{3})')

def clean_vtt(text):
    if not text or not text.strip():
        return ""
    lines = text.replace('\r\n', '\n').replace('\r', '\n').split('\n')
    cues = []
    cur_time = None
    cur_text = []
    for line in lines:
        s = line.strip()
        if not s or s.startswith('WEBVTT') or s.startswith('NOTE') or s.startswith('Kind:') or s.startswith('Language:'):
            continue
        m = time_re.search(s)
        if m:
            if cur_time and cur_text:
                cues.append((cur_time, '\n'.join(cur_text)))
            s1 = m.group(1) or '00:'
            s2 = m.group(2).replace(',', '.')
            e1 = m.group(3) or '00:'
            e2 = m.group(4).replace(',', '.')
            cur_time = f"{s1}{s2} --> {e1}{e2}"
            cur_text = []
        elif not s.isdigit():
            clean_s = re.sub(r'line:\d+%.*$', '', s).strip()
            clean_s = re.sub(r'<[^>]+>', '', clean_s)
            if clean_s:
                cur_text.append(clean_s)
    if cur_time and cur_text:
        cues.append((cur_time, '\n'.join(cur_text)))

    out = ['WEBVTT\n']
    for i, (ctime, ctext) in enumerate(cues, 1):
        out.append(f"{i}\n{ctime}\n{ctext}\n")
    return '\n'.join(out).strip() + '\n'

# ── VIDEO HELPERS ─────────────────────────────────────────────────────────────
def download_dramawave_video(m3u8_url, out_mp4):
    cmd = [
        'ffmpeg', '-y',
        '-headers', HEADERS_STR,
        '-i', m3u8_url,
        '-map', '0:a:0',
        '-map', '0:v:0',
        '-c', 'copy',
        '-movflags', '+faststart',
        '-loglevel', 'error',
        str(out_mp4)
    ]
    res = subprocess.run(cmd, timeout=300)
    return res.returncode == 0 and out_mp4.exists() and out_mp4.stat().st_size > 100 * 1024

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

# ── LOAD METADATA DUMP ────────────────────────────────────────────────────────
def load_dump_items():
    if DUMP_FILE.exists():
        try:
            with open(DUMP_FILE, 'r', encoding='utf-8') as f:
                d = json.load(f)
                return {item['ep']: item for item in d.get('items', []) if item.get('url')}
        except Exception:
            pass
    return {}

# ── PROCESS EPISODE ───────────────────────────────────────────────────────────
def process_episode(drama_id, ep_num, ep_meta):
    k720 = f"{PREFIX}/ep{ep_num:03d}.mp4"
    k540 = f"{PREFIX}/ep{ep_num:03d}_540p.mp4"
    kvtt = f"{PREFIX}/ep{ep_num:03d}.vtt"

    local_file = LOCAL_DIR / f"ep{ep_num:03d}.mp4"
    local_vtt = LOCAL_DIR / f"ep{ep_num:03d}.vtt"

    # 1. Cek jika sudah ada di R2
    has_720 = r2_exists(k720)
    has_540 = r2_exists(k540)
    has_vtt = r2_exists(kvtt)

    if has_720 and has_540 and has_vtt:
        print(f"  -> Ep {ep_num:02d}: Sudah lengkap di R2. Link DB...", end="", flush=True)
        u720 = f"{R2_PUBLIC}/{k720}"
        u540 = f"{R2_PUBLIC}/{k540}"
        ep_id = upsert_episode(drama_id, ep_num, u720, u540)
        link_subtitle_to_episode(ep_id, f"{R2_PUBLIC}/{kvtt}")
        if not local_file.exists():
            try: s3.download_file(R2_BUCKET, k720, str(local_file))
            except Exception: pass
        if not local_vtt.exists():
            try: s3.download_file(R2_BUCKET, kvtt, str(local_vtt))
            except Exception: pass
        print(" [OK]")
        return True

    video_url = ep_meta.get('url')
    if not video_url:
        print(f"  -> Ep {ep_num:02d}: [GAGAL - Tidak ada URL video]")
        return False

    print(f"  -> Ep {ep_num:02d}: Download...", end="", flush=True)

    raw_mp4 = TEMP_DIR / f"raw_{ep_num:03d}.mp4"
    out_540 = TEMP_DIR / f"out540_{ep_num:03d}.mp4"

    if not download_dramawave_video(video_url, raw_mp4):
        print(" [GAGAL DOWNLOAD]")
        raw_mp4.unlink(missing_ok=True)
        return False

    size_mb = raw_mp4.stat().st_size / (1024 * 1024)
    print(f" ({size_mb:.1f} MB) 540p...", end="", flush=True)

    if not encode_540p(raw_mp4, out_540):
        print(" [GAGAL 540P]")
        raw_mp4.unlink(missing_ok=True)
        out_540.unlink(missing_ok=True)
        return False

    # Process Subtitle
    print(" Sub...", end="", flush=True)
    vtt_content = None
    if ep_meta.get('inlineSub'):
        vtt_content = clean_vtt(ep_meta['inlineSub'])
    elif ep_meta.get('sub'):
        try:
            r_sub = requests.get(ep_meta['sub'], headers={'User-Agent': 'Mozilla/5.0', 'Referer': 'https://mydramawave.com/'}, timeout=10)
            if r_sub.ok and len(r_sub.text) > 30:
                vtt_content = clean_vtt(r_sub.text)
        except Exception:
            pass

    if vtt_content and len(vtt_content) > 30:
        local_vtt.write_text(vtt_content, encoding='utf-8')
        s3.upload_file(str(local_vtt), R2_BUCKET, kvtt, ExtraArgs={'ContentType': 'text/vtt'})
        print(" [VTT OK]", end="", flush=True)
    else:
        print(" [No Sub]", end="", flush=True)

    print(" R2...", end="", flush=True)
    u720 = r2_upload(raw_mp4, k720)
    u540 = r2_upload(out_540, k540)

    # Simpan ke folder lokal (Single Location)
    try:
        shutil.copy2(raw_mp4, local_file)
    except Exception as e:
        print(f" [WARN local copy: {e}]", end="")

    # Upsert DB
    ep_id = upsert_episode(drama_id, ep_num, u720, u540)
    if ep_id and local_vtt.exists():
        link_subtitle_to_episode(ep_id, f"{R2_PUBLIC}/{kvtt}")

    raw_mp4.unlink(missing_ok=True)
    out_540.unlink(missing_ok=True)
    print(" [SELESAI]")
    return True

# ── MAIN PIPELINE ────────────────────────────────────────────────────────────
def main():
    print("=" * 60)
    print(f"MEMULAI SEDOT: {TITLE} ({TOTAL_EPS} Episode)")
    print("=" * 60)

    ensure_cover()

    drama_id = get_or_create_drama()
    if not drama_id:
        print(f"[ERROR] Gagal mendapatkan ID drama DB untuk {TITLE}.")
        return

    dump_items = load_dump_items()
    print(f"[INFO] Terbaca {len(dump_items)} episode dari metadata dump.")

    success = 0
    for ep in range(1, TOTAL_EPS + 1):
        ep_meta = dump_items.get(ep, {})
        if process_episode(drama_id, ep, ep_meta):
            success += 1
        time.sleep(0.3)

    # Retry jika ada episode terlewat
    missing = [e for e in range(1, TOTAL_EPS + 1) if not (LOCAL_DIR / f"ep{e:03d}.mp4").exists()]
    if missing:
        print(f"\n[RETRY] Memproses episode yang belum lengkap: {missing}...")
        for ep in missing:
            ep_meta = dump_items.get(ep, {})
            if process_episode(drama_id, ep, ep_meta):
                success += 1

    print("\n" + "=" * 60)
    print(f"[HASIL] Selesai {TITLE}: {success}/{TOTAL_EPS} episode.")
    print(f"  - Cloudflare R2: {R2_PUBLIC}/{PREFIX}/")
    print(f"  - Local Storage (Single Location): {LOCAL_DIR}")
    print("=" * 60)

if __name__ == "__main__":
    main()
