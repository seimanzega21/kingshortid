#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Sedot Drama: Kelahiran Kembali Pemandian (69 Episode)
Provider: Dracinema (DramaNova / cdnt.yfeitrade.com)
Features:
- Tanpa blur pada video (kualitas video original & tajam).
- Subtitle Bahasa Indonesia (WebVTT) diletakkan di bawah tulisan Mandarin (line:88% position:50% align:center).
- Subtitle diekstrak dari Dracinema (Ep 1-2) atau digenerate otomatis menggunakan AI (ag/gemini-3.8-flash-high).
- Upload 720p, 540p faststart, dan VTT ke Cloudflare R2.
- Daftarkan ke database KingShort (api.shortlovers.id).
- Simpan file lokal di satu lokasi saja: D:\\Video Drama\\Facebook\\Kelahiran Kembali Pemandian\\
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
import base64
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

TITLE       = 'Kelahiran Kembali Pemandian'
SLUG        = 'kelahiran-kembali-pemandian'
MOVIE_KEY   = 'kelahiran-kembali-pemandian-dn_2102231938793574401'
TOTAL_EPS   = 69
COVER_URL   = 'https://img.mebilu.com/mQf6EpOKP3EmieV_mie-0XcxjzcWrOnCsTkXjrj8HOZQMw8CYwcE80mjsC_R5G01g8Mft42L256Iow.webp'
GENRES      = ['Perjalanan Waktu', 'Pemeran Utama Pria', 'Kelahiran Kembali', 'Drama', 'Romantis']
DESC        = 'Terlahir kembali ke tahun 1995, seorang mantan pemilik laundry berusaha menyelamatkan rumah pemandian umum bobrok keluarganya dari kebangkrutan, membalas perlakuan kejam, dan bangkit membangun kekaisaran bisnis pemandian modern!'
PREFIX      = f"dracinema/{SLUG}"

LOCAL_DIR   = Path("D:/Video Drama/Facebook") / TITLE
LOCAL_DIR.mkdir(parents=True, exist_ok=True)

TEMP_DIR    = Path("D:/temp_scraper") / SLUG
TEMP_DIR.mkdir(parents=True, exist_ok=True)

DUMP_FILE   = Path("D:/temp_scraper/kelahiran_dump.json")

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

# ── SUBTITLE POSITIONING & PROCESSING ─────────────────────────────────────────
LINE_SETTING = "line:88% position:50% align:center"

def format_vtt_with_positioning(raw_text):
    """
    Format WebVTT subtitle and ensure each cue has line:88% position:50% align:center
    so it renders cleanly beneath the Chinese hardsub.
    """
    if not raw_text or not raw_text.strip():
        return ""

    raw_text = raw_text.replace('\r\n', '\n').replace('\r', '\n')
    lines = raw_text.split('\n')
    out_lines = ["WEBVTT\n"]

    time_re = re.compile(r'(\d{2}:)?(\d{2}:\d{2}[.,]\d{3})\s*-->\s*(\d{2}:)?(\d{2}:\d{2}[.,]\d{3})(.*)')

    for line in lines:
        stripped = line.strip()
        if not stripped or stripped.startswith("WEBVTT") or stripped.startswith("NOTE"):
            continue

        match = time_re.search(stripped)
        if match:
            # Reconstruct start and end time
            start_prefix = match.group(1) or "00:"
            start_rest = match.group(2).replace(',', '.')
            start_time = f"{start_prefix}{start_rest}"

            end_prefix = match.group(3) or "00:"
            end_rest = match.group(4).replace(',', '.')
            end_time = f"{end_prefix}{end_rest}"

            out_lines.append(f"{start_time} --> {end_time} {LINE_SETTING}")
        else:
            out_lines.append(line)

    return "\n".join(out_lines).strip() + "\n"

def generate_subtitles_ai(audio_path):
    """
    Extract audio dialogue and translate to Indonesian WebVTT using Gemini 3.8 Flash via 9router.
    """
    try:
        with open(audio_path, 'rb') as fp:
            audio_b64 = base64.b64encode(fp.read()).decode('utf-8')

        prompt = (
            "Transcribe the dialogue in this Chinese audio clip and translate it into natural, fluent Indonesian in WebVTT subtitle format.\n"
            "Requirements:\n"
            "1. Output MUST start with 'WEBVTT'.\n"
            f"2. Every cue timing line MUST include: '--> <end_time> {LINE_SETTING}'.\n"
            "3. Translate accurately into everyday natural Indonesian suitable for short drama dubbing/subtitles.\n"
            "4. Output ONLY the Indonesian translation text (do NOT include any Chinese characters).\n"
            "5. Output pure WebVTT text directly, no markdown formatting (no ```vtt blocks)."
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
            return format_vtt_with_positioning(content)
        else:
            print(f" [AI Sub Error {r.status_code}]", end="", flush=True)
    except Exception as e:
        print(f" [AI Sub Exc: {e}]", end="", flush=True)
    return None

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

def download_hls_video(url, out_mp4):
    headers_list = [
        "User-Agent: Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36",
        "Referer: https://www.dracinema.com/"
    ]
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

# ── LOAD METADATA DUMP ────────────────────────────────────────────────────────
def load_dump_items():
    if DUMP_FILE.exists():
        try:
            with open(DUMP_FILE, 'r', encoding='utf-8') as f:
                data = json.load(f)
                return {item['ep']: item for item in data.get('items', []) if item.get('url')}
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

    # 1. Cek apakah video & sub sudah ada di R2
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

    print(f"  -> Ep {ep_num:02d}: Mengunduh video HLS...", end="", flush=True)

    raw_mp4 = TEMP_DIR / f"raw_{ep_num:03d}.mp4"
    out_540 = TEMP_DIR / f"out540_{ep_num:03d}.mp4"
    audio_mp3 = TEMP_DIR / f"audio_{ep_num:03d}.mp3"

    if not download_hls_video(video_url, raw_mp4):
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

    # Subtitle Processing
    print(" Sub...", end="", flush=True)
    vtt_content = None

    # Opsi A: Subtitle bawaan dari Dracinema (Ep 1 & 2)
    if ep_meta.get('inlineSub'):
        vtt_content = format_vtt_with_positioning(ep_meta['inlineSub'])
    elif ep_meta.get('sub'):
        try:
            r_sub = requests.get(ep_meta['sub'], headers={'User-Agent': 'Mozilla/5.0', 'Referer': 'https://www.dracinema.com/'}, timeout=15)
            if r_sub.ok and len(r_sub.text) > 30:
                vtt_content = format_vtt_with_positioning(r_sub.text)
        except Exception:
            pass

    # Opsi B: Generate via AI jika subtitle bawaan tidak ada
    if not vtt_content or len(vtt_content) < 30:
        # Ekstrak audio mp3 64k
        cmd_aud = ['ffmpeg', '-y', '-i', str(raw_mp4), '-vn', '-c:a', 'mp3', '-b:a', '64k', '-ar', '16000', '-loglevel', 'error', str(audio_mp3)]
        if subprocess.run(cmd_aud).returncode == 0 and audio_mp3.exists():
            vtt_content = generate_subtitles_ai(audio_mp3)
            audio_mp3.unlink(missing_ok=True)

    if vtt_content and len(vtt_content) > 30:
        with open(local_vtt, 'w', encoding='utf-8') as fp:
            fp.write(vtt_content)
        s3.upload_file(str(local_vtt), R2_BUCKET, kvtt, ExtraArgs={'ContentType': 'text/vtt'})
        print(" [VTT AI OK]", end="", flush=True)
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
    print(f"[INFO] Terbaca {len(dump_items)} episode awal dari metadata dump.")

    success = 0
    for ep in range(1, TOTAL_EPS + 1):
        dump_items = load_dump_items()
        retry_count = 0
        while ep not in dump_items:
            print(f"  [WAIT] Menunggu metadata Ep {ep:02d} dari browser...", flush=True)
            time.sleep(3)
            dump_items = load_dump_items()
            retry_count += 1
            if retry_count > 60:
                print(f"  [ERROR] Timeout menunggu metadata Ep {ep:02d}!")
                break

        ep_meta = dump_items.get(ep, {})
        if ep_meta and process_episode(drama_id, ep, ep_meta):
            success += 1
        time.sleep(0.5)

    print("\n" + "=" * 60)
    print(f"[HASIL] Selesai {TITLE}: {success}/{TOTAL_EPS} episode.")
    print(f"  - Cloudflare R2: {R2_PUBLIC}/{PREFIX}/")
    print(f"  - Local Storage (Single Location): {LOCAL_DIR}")
    print("=" * 60)

if __name__ == "__main__":
    main()
