#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Sedot Drama: Petani Bertemu Naga Suci (45 Episode)
Provider: Dracinema (PandaDrama / TikTok CDN MP4)
Execution (Opsi B):
- Video asli di-blur secara halus (feathered/gradient Gaussian blur) pada area teks Bahasa Inggris agar hilang dengan lembut.
- Transcode 540p faststart untuk performa streaming hemat kuota.
- Subtitle Bahasa Indonesia diekstrak dari audio ucapan Mandarin lalu ditranskripsikan & diterjemahkan oleh AI (Gemini 3.8 Flash via 9router) dalam format WebVTT (.vtt).
- Subtitle diatur posisinya tepat di atas area blur tersebut.
- Upload 720p, 540p, dan VTT ke Cloudflare R2 (stream.shortlovers.id/dracinema/petani-bertemu-naga-suci/).
- Daftarkan ke database KingShort (api.shortlovers.id).
- Simpan file lokal strictly di 1 tempat: D:\\Video Drama\\Facebook\\Petani Bertemu Naga Suci\\
"""

import sys
if sys.platform == 'win32':
    sys.stdout.reconfigure(encoding='utf-8', errors='replace')
    sys.stderr.reconfigure(encoding='utf-8', errors='replace')

import os
import re
import json
import time
import shutil
import base64
import sqlite3
import subprocess
import requests
import urllib3
import boto3
import numpy as np
from PIL import Image
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

TITLE       = 'Petani Bertemu Naga Suci'
SLUG        = 'petani-bertemu-naga-suci'
MOVIE_KEY   = 'petani-bertemu-naga-suci-pd_7693379487056073734'
TOTAL_EPS   = 45
COVER_URL   = 'https://img.mebilu.com/IaqM5sjn4MdRuG7C0j3zCe8m0GntXvTMmFpkmRotFiUAzfF9IcBK2G8ULsFRwhaZfVN61822WTj_fw.webp'
GENRES      = ['Kekuatan Super', 'Fantasi', 'Pemeran Utama Pria', 'Drama']
DESC        = 'Di dunia persilatan, seorang petani miskin tak sengaja menemukan seekor naga suci kuno yang terperangkap rantai di bawah lembah. Pertemuan takdir ini mengubah hidupnya secara drastis saat ia mendapatkan kekuatan dewa naga untuk melawan kezaliman dan bangkit menjadi sosok terkuat!'
PREFIX      = f"dracinema/{SLUG}"

LOCAL_DIR   = Path("D:/Video Drama/Facebook") / TITLE
LOCAL_DIR.mkdir(parents=True, exist_ok=True)

TEMP_DIR    = Path("D:/temp_scraper") / SLUG
TEMP_DIR.mkdir(parents=True, exist_ok=True)

URL_DUMP_FILE = Path("D:/temp_scraper/petani_naga_urls.json")

ROUTER_URL  = 'http://localhost:20128/v1/chat/completions'
ROUTER_KEY  = 'sk-6c5720214189ea51-otb97y-5446d478'
ROUTER_MODEL= 'ag/gemini-3.8-flash-high'

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
                    return d['id']
    except Exception as e:
        print(f"  [WARN] Gagal cek drama di DB: {e}")

    payload = {
        'title': TITLE,
        'description': DESC,
        'cover': cover_r2_url,
        'genres': GENRES,
        'totalEpisodes': TOTAL_EPS,
        'country': 'China',
        'language': 'Indonesia',
        'status': 'completed',
        'isActive': True
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

# ── COOKIES & PLAYBACK URL GETTER ─────────────────────────────────────────────
def get_dracinema_cookies():
    src = r'C:\Users\Seiman\AppData\Roaming\Paseo\Partitions\paseo-browser\Network\Cookies'
    dst = TEMP_DIR / 'temp_cookies.db'
    if not os.path.exists(src):
        return {}
    try:
        shutil.copy2(src, dst)
        conn = sqlite3.connect(dst)
        cur = conn.cursor()
        cur.execute('SELECT name, value FROM cookies WHERE host_key LIKE "%dracinema%"')
        cookies = {name: val for name, val in cur.fetchall()}
        conn.close()
        dst.unlink(missing_ok=True)
        return cookies
    except Exception:
        return {}

def fetch_fresh_video_url(ep_num):
    cookies = get_dracinema_cookies()
    headers = {
        'Content-Type': 'application/json',
        'X-API-Key': 'xb3MdwdLrZrpaDXvrLLwfP==',
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36',
        'Origin': 'https://www.dracinema.com',
        'Referer': f'https://www.dracinema.com/play/{MOVIE_KEY}'
    }
    try:
        r = requests.post(
            'https://www.dracinema.com/api/playback',
            headers=headers,
            cookies=cookies,
            json={'movieKey': MOVIE_KEY, 'episode': ep_num},
            timeout=12
        )
        if r.ok:
            token = r.json().get('token', '')
            s = token.split('.')[1]
            s += '=' * ((4 - len(s) % 4) % 4)
            data = json.loads(base64.b64decode(s.replace('-', '+').replace('_', '/')).decode('utf-8'))
            return data.get('data', {}).get('detail', {}).get('videoUrls', [{}])[0].get('url')
    except Exception:
        pass
    return None

def load_cached_urls():
    if URL_DUMP_FILE.exists():
        try:
            with open(URL_DUMP_FILE, 'r', encoding='utf-8') as f:
                d = json.load(f)
                return {int(k): v for k, v in d.items() if v}
        except Exception:
            pass
    return {}

# ── FEATHERED BLUR MASK ───────────────────────────────────────────────────────
MASK_CACHE = {}

def get_feather_mask(w, h):
    key = (w, h)
    if key in MASK_CACHE and MASK_CACHE[key].exists():
        return MASK_CACHE[key]

    mask_path = TEMP_DIR / f"mask_{w}_{h}.png"
    mask = np.zeros((h, w), dtype=np.float32)
    # Wider mask to generously cover both single-line and multi-line subtitles
    y1 = int(0.58 * h)
    y2 = int(0.63 * h)
    y3 = int(0.76 * h)
    y4 = int(0.81 * h)

    for y in range(y1, y2):
        mask[y, :] = (y - y1) / (y2 - y1)
    mask[y2:y3, :] = 1.0
    for y in range(y3, y4):
        mask[y, :] = (y4 - y) / (y4 - y3)

    Image.fromarray((mask * 255).astype(np.uint8), mode='L').save(mask_path)
    MASK_CACHE[key] = mask_path
    return mask_path

# ── VIDEO PROCESSING (FEATHERED BLUR & 540P) ──────────────────────────────────
def get_video_dimensions(file_path):
    cmd = [
        'ffprobe', '-v', 'error', '-select_streams', 'v:0',
        '-show_entries', 'stream=width,height', '-of', 'csv=s=x:p=0',
        str(file_path)
    ]
    try:
        res = subprocess.check_output(cmd).decode('utf-8').strip()
        parts = res.split('x')
        return int(parts[0]), int(parts[1])
    except Exception:
        return 576, 1026

def apply_feathered_blur(raw_file, out_file):
    w, h = get_video_dimensions(raw_file)
    mask_file = get_feather_mask(w, h)

    cmd = [
        'ffmpeg', '-y',
        '-i', str(raw_file),
        '-loop', '1', '-i', str(mask_file),
        '-filter_complex', '[0:v]boxblur=luma_radius=45:luma_power=4:chroma_radius=45:chroma_power=4[b];[b][1:v]alphamerge[bm];[0:v][bm]overlay=0:0[v]',
        '-map', '[v]', '-map', '0:a?',
        '-c:v', 'libx264', '-crf', '23', '-preset', 'fast',
        '-c:a', 'copy',
        '-shortest',
        '-movflags', '+faststart',
        '-loglevel', 'error',
        str(out_file)
    ]
    res = subprocess.run(cmd)
    return res.returncode == 0 and out_file.exists() and out_file.stat().st_size > 100 * 1024

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

# ── SUBTITLE GENERATOR VIA AI (GEMINI 3.8 FLASH) ──────────────────────────────
def format_vtt_with_double_newlines(raw_text):
    if not raw_text or not raw_text.strip():
        return ""
    lines = raw_text.replace('\r\n', '\n').replace('\r', '\n').split('\n')
    cues = []
    cur_time = None
    cur_text = []
    time_re = re.compile(r'(\d{2}:)?(\d{2}:\d{2}[.,]\d{3})\s*-->\s*(\d{2}:)?(\d{2}:\d{2}[.,]\d{3})')

    for line in lines:
        s = line.strip()
        if not s or s.startswith("WEBVTT") or s.startswith("NOTE"):
            continue
        m = time_re.search(s)
        if m:
            if cur_time and cur_text:
                cues.append((cur_time, "\n".join(cur_text)))
            s1 = m.group(1) or "00:"
            s2 = m.group(2).replace(',', '.')
            e1 = m.group(3) or "00:"
            e2 = m.group(4).replace(',', '.')
            cur_time = f"{s1}{s2} --> {e1}{e2}"
            cur_text = []
        elif not s.isdigit():
            clean_s = re.sub(r'line:\d+%.*$', '', s).strip()
            clean_s = re.sub(r'<[^>]+>', '', clean_s)
            if clean_s:
                cur_text.append(clean_s)

    if cur_time and cur_text:
        cues.append((cur_time, "\n".join(cur_text)))

    out = ["WEBVTT\n"]
    for i, (ctime, ctext) in enumerate(cues, 1):
        out.append(f"{i}\n{ctime}\n{ctext}\n")
    return "\n".join(out).strip() + "\n"

def generate_subtitles_ai(audio_path):
    try:
        with open(audio_path, 'rb') as fp:
            audio_b64 = base64.b64encode(fp.read()).decode('utf-8')

        prompt = (
            "Transcribe the dialogue in this Chinese audio clip and translate it into natural, fluent Indonesian in WebVTT subtitle format.\n"
            "Requirements:\n"
            "1. Output MUST start with 'WEBVTT'.\n"
            "2. Translate accurately into everyday natural Indonesian suitable for short drama dubbing/subtitles.\n"
            "3. Output ONLY the Indonesian translation text (do NOT include any Chinese characters).\n"
            "4. Output pure WebVTT text directly, no markdown formatting (no ```vtt blocks)."
        )
        headers = {
            'Authorization': f'Bearer {ROUTER_KEY}',
            'Content-Type': 'application/json'
        }
        payload = {
            'model': ROUTER_MODEL,
            'stream': False,
            'messages': [
                {
                    'role': 'user',
                    'content': [
                        {'type': 'text', 'text': prompt},
                        {'type': 'input_audio', 'input_audio': {'data': audio_b64, 'format': 'mp3'}}
                    ]
                }
            ]
        }
        r = requests.post(ROUTER_URL, headers=headers, json=payload, timeout=60)
        if r.status_code == 200:
            content = r.json().get('choices', [{}])[0].get('message', {}).get('content', '').strip()
            content = re.sub(r'^```[a-zA-Z]*\n', '', content)
            content = re.sub(r'\n```$', '', content)
            return format_vtt_with_double_newlines(content)
    except Exception as e:
        print(f" [AI Sub Exc: {e}]", end="", flush=True)
    return None

# ── PROCESS EPISODE ───────────────────────────────────────────────────────────
FORCE_REBLUR = True

def process_episode(drama_id, ep_num, cached_urls):
    k720 = f"{PREFIX}/ep{ep_num:03d}.mp4"
    k540 = f"{PREFIX}/ep{ep_num:03d}_540p.mp4"
    kvtt = f"{PREFIX}/ep{ep_num:03d}.vtt"

    local_file = LOCAL_DIR / f"ep{ep_num:03d}.mp4"
    local_vtt = LOCAL_DIR / f"ep{ep_num:03d}.vtt"

    # 1. Cek jika sudah lengkap di R2 dan tidak dipaksa re-blur
    if not FORCE_REBLUR and r2_exists(k720) and r2_exists(k540) and r2_exists(kvtt):
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

    # 2. Ambil URL video
    video_url = cached_urls.get(ep_num)
    if not video_url:
        video_url = fetch_fresh_video_url(ep_num)

    if not video_url:
        print(f"  -> Ep {ep_num:02d}: [GAGAL - Tidak ada URL video]")
        return False

    print(f"  -> Ep {ep_num:02d}: Download raw...", end="", flush=True)
    raw_mp4 = TEMP_DIR / f"raw_{ep_num:03d}.mp4"
    blur_mp4 = TEMP_DIR / f"blur_{ep_num:03d}.mp4"
    out_540 = TEMP_DIR / f"out540_{ep_num:03d}.mp4"
    audio_mp3 = TEMP_DIR / f"audio_{ep_num:03d}.mp3"

    try:
        r_vid = requests.get(video_url, headers={'User-Agent': 'Mozilla/5.0'}, stream=True, timeout=60)
        if not r_vid.ok:
            video_url = fetch_fresh_video_url(ep_num)
            r_vid = requests.get(video_url, headers={'User-Agent': 'Mozilla/5.0'}, stream=True, timeout=60)
            if not r_vid.ok:
                print(f" [GAGAL DOWNLOAD: {r_vid.status_code}]")
                return False

        with open(raw_mp4, 'wb') as f:
            for chunk in r_vid.iter_content(chunk_size=1024*1024):
                if chunk: f.write(chunk)
    except Exception as e:
        print(f" [DOWNLOAD EXC: {e}]")
        raw_mp4.unlink(missing_ok=True)
        return False

    size_mb = raw_mp4.stat().st_size / (1024 * 1024)
    print(f" ({size_mb:.1f} MB) FeatherBlur(Wide)...", end="", flush=True)

    # 3. Feathered Blur (Wide mask + Gaussian Blur)
    if not apply_feathered_blur(raw_mp4, blur_mp4):
        print(" [GAGAL BLUR]")
        raw_mp4.unlink(missing_ok=True)
        blur_mp4.unlink(missing_ok=True)
        return False

    # 4. Transcode 540p faststart
    print(" 540p...", end="", flush=True)
    if not encode_540p(blur_mp4, out_540):
        print(" [GAGAL 540P]")
        raw_mp4.unlink(missing_ok=True)
        blur_mp4.unlink(missing_ok=True)
        out_540.unlink(missing_ok=True)
        return False

    # 5. Extract audio & Generate Subtitle AI if needed
    if local_vtt.exists() and local_vtt.stat().st_size > 30:
        print(" [VTT OK]", end="", flush=True)
    else:
        print(" Sub AI...", end="", flush=True)
        cmd_aud = ['ffmpeg', '-y', '-i', str(raw_mp4), '-vn', '-c:a', 'mp3', '-b:a', '64k', '-ar', '16000', '-loglevel', 'error', str(audio_mp3)]
        vtt_content = None
        if subprocess.run(cmd_aud).returncode == 0 and audio_mp3.exists():
            vtt_content = generate_subtitles_ai(audio_mp3)
            audio_mp3.unlink(missing_ok=True)

        if vtt_content and len(vtt_content) > 30:
            local_vtt.write_text(vtt_content, encoding='utf-8')
            s3.upload_file(str(local_vtt), R2_BUCKET, kvtt, ExtraArgs={'ContentType': 'text/vtt'})
            print(" [VTT Generated]", end="", flush=True)
        else:
            print(" [No Sub]", end="", flush=True)

    # 6. Upload R2
    print(" R2...", end="", flush=True)
    u720 = r2_upload(blur_mp4, k720)
    u540 = r2_upload(out_540, k540)

    # 7. Simpan lokal (Single Location)
    try:
        shutil.copy2(blur_mp4, local_file)
    except Exception as e:
        print(f" [WARN local copy: {e}]", end="")

    # 8. Upsert DB
    ep_id = upsert_episode(drama_id, ep_num, u720, u540)
    if ep_id and local_vtt.exists():
        link_subtitle_to_episode(ep_id, f"{R2_PUBLIC}/{kvtt}")

    # Clean temp
    raw_mp4.unlink(missing_ok=True)
    blur_mp4.unlink(missing_ok=True)
    out_540.unlink(missing_ok=True)
    print(" [SELESAI]")
    return True

    # Clean temp
    raw_mp4.unlink(missing_ok=True)
    blur_mp4.unlink(missing_ok=True)
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

    cached_urls = load_cached_urls()
    print(f"[INFO] Terbaca {len(cached_urls)} URL video dari cache.")

    success = 0
    for ep in range(1, TOTAL_EPS + 1):
        if process_episode(drama_id, ep, cached_urls):
            success += 1
        time.sleep(0.3)

    # Retry jika ada episode terlewat
    missing = [e for e in range(1, TOTAL_EPS + 1) if not (LOCAL_DIR / f"ep{e:03d}.mp4").exists()]
    if missing:
        print(f"\n[RETRY] Memproses episode yang belum lengkap: {missing}...")
        for ep in missing:
            if process_episode(drama_id, ep, cached_urls):
                success += 1

    print("\n" + "=" * 60)
    print(f"[HASIL] Selesai {TITLE}: {success}/{TOTAL_EPS} episode.")
    print(f"  - Cloudflare R2: {R2_PUBLIC}/{PREFIX}/")
    print(f"  - Local Storage (Single Location): {LOCAL_DIR}")
    print("=" * 60)

if __name__ == "__main__":
    main()
