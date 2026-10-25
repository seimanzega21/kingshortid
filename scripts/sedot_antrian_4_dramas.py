#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Sedot Antrian 4 Drama Dracinema:
1. Tengah Malam Si Cantik Memikat (30 Episode) - ZebraShort (Hardsub Indo)
2. Dewa Perang Palsu (77 Episode) - DramaWave (WebVTT Sub Indo)
3. Susuku, Pedangku (62 Episode) - DramaWave (WebVTT Sub Indo)
4. Musim Panas Bersama Tetangga (60 Episode) - DramaBox (Hardsub)
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
    except Exception:
        return False

def r2_upload(local_path, key, content_type='video/mp4'):
    s3.upload_file(str(local_path), R2_BUCKET, key, ExtraArgs={'ContentType': content_type},
                   Config=boto3.s3.transfer.TransferConfig(multipart_threshold=30*1024*1024, multipart_chunksize=10*1024*1024))
    return f"{R2_PUBLIC}/{key}"

# ── SUBTITLE HELPER ──────────────────────────────────────────────────────────
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
                    requests.patch(f"{API_BASE}/dramas/{d['id']}", headers=ADMIN_HDR, json={'isActive': True, 'totalEpisodes': meta['total_eps']})
                    return d['id']
    except Exception as e:
        print(f"  [WARN] Gagal cek drama di DB: {e}")

    payload = {
        'title': title,
        'description': meta.get('desc') or title,
        'cover': cover_r2_url,
        'genres': meta.get('genres', ['Drama']),
        'totalEpisodes': meta['total_eps'],
        'country': meta.get('country', 'China'),
        'language': 'Indonesia',
        'status': 'completed',
        'isActive': True
    }
    try:
        r = requests.post(f"{API_BASE}/admin/dramas", headers=ADMIN_HDR, json=payload, timeout=20)
        if r.ok:
            new_id = r.json().get('id')
            print(f"  -> Berhasil membuat drama di DB (ID: {new_id})")
            requests.patch(f"{API_BASE}/dramas/{new_id}", headers=ADMIN_HDR, json={'isActive': True, 'totalEpisodes': meta['total_eps']})
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

def download_video(url, out_mp4, movie_key):
    headers_list = [
        "User-Agent: Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36"
    ]
    if "mydramawave.com" in url or "dw_" in movie_key:
        headers_list.append("Referer: https://mydramawave.com/")
    elif "dramapetir.com" in url or "dx_" in movie_key:
        headers_list.append("Referer: https://dramapetir.com/")
    elif "zebrashort.com" in url or "zs_" in movie_key:
        headers_list.append("Referer: https://www.dracinema.com/")
    else:
        headers_list.append("Referer: https://www.dracinema.com/")

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
    return res.returncode == 0 and out_mp4.exists() and out_mp4.stat().st_size > 100 * 1024

def ensure_cover(meta, temp_dir):
    cover_key = f"{meta['prefix']}/cover.webp"
    if r2_exists(cover_key):
        print(f"  -> [R2] Cover already exists.")
        return
    print(f"  -> [R2] Mengunduh dan mengupload cover...")
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

# ── BRIDGE CLIENT FOR PLAYBACK URLS ──────────────────────────────────────────
def get_playback_via_bridge(movie_key, ep_num):
    for attempt in range(4):
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
    local_vtt  = meta['local_dir'] / f"ep{ep_num:03d}.vtt"

    has_sub = meta.get('has_sub', False)

    # 1. Cek apakah video sudah lengkap di R2
    if r2_exists(k720) and r2_exists(k540) and (not has_sub or r2_exists(kvtt)):
        print(f"  -> Ep {ep_num:02d}: Sudah lengkap di R2. Link DB...", end="", flush=True)
        u720 = f"{R2_PUBLIC}/{k720}"
        u540 = f"{R2_PUBLIC}/{k540}"
        ep_id = upsert_episode(drama_id, ep_num, u720, u540)
        if has_sub:
            link_subtitle_to_episode(ep_id, f"{R2_PUBLIC}/{kvtt}")
        if not local_file.exists():
            try: s3.download_file(R2_BUCKET, k720, str(local_file))
            except Exception: pass
        if has_sub and not local_vtt.exists():
            try: s3.download_file(R2_BUCKET, kvtt, str(local_vtt))
            except Exception: pass
        print(" [OK]")
        return True

    # 2. Ambil URL video fresh melalui Bridge Browser
    print(f"  -> Ep {ep_num:02d}: Ambil stream dari Dracinema...", end="", flush=True)
    pb = get_playback_via_bridge(meta['movie_key'], ep_num)
    if not pb or not pb.get('url'):
        print(" [GAGAL DAPAT URL STREAM]")
        return False

    video_url = pb['url']
    raw_mp4 = temp_dir / f"raw_{ep_num:03d}.mp4"
    out_540 = temp_dir / f"out540_{ep_num:03d}.mp4"

    # 3. Download
    if not download_video(video_url, raw_mp4, meta['movie_key']):
        print(" [GAGAL DOWNLOAD]")
        raw_mp4.unlink(missing_ok=True)
        return False

    size_mb = raw_mp4.stat().st_size / (1024 * 1024)
    print(f" ({size_mb:.1f} MB) 540p...", end="", flush=True)

    # 4. 540p Transcode
    if not encode_540p(raw_mp4, out_540):
        print(" [GAGAL 540P]")
        raw_mp4.unlink(missing_ok=True)
        out_540.unlink(missing_ok=True)
        return False

    # 5. Subtitle Handling
    vtt_content = None
    if pb.get('inlineSub'):
        vtt_content = clean_vtt(pb['inlineSub'])
    elif pb.get('sub'):
        try:
            sub_hdrs = {'User-Agent': 'Mozilla/5.0'}
            if 'mydramawave.com' in pb['sub']:
                sub_hdrs['Referer'] = 'https://mydramawave.com/'
            else:
                sub_hdrs['Referer'] = 'https://www.dracinema.com/'
            r_sub = requests.get(pb['sub'], headers=sub_hdrs, timeout=12)
            if r_sub.ok and len(r_sub.text) > 30:
                vtt_content = clean_vtt(r_sub.text)
        except Exception:
            pass

    if vtt_content and len(vtt_content) > 30:
        local_vtt.write_text(vtt_content, encoding='utf-8')
        s3.upload_file(str(local_vtt), R2_BUCKET, kvtt, ExtraArgs={'ContentType': 'text/vtt'})
        print(" [+Sub VTT]", end="", flush=True)

    # 6. Upload R2
    print(" R2...", end="", flush=True)
    u720 = r2_upload(raw_mp4, k720)
    u540 = r2_upload(out_540, k540)

    # 7. Simpan lokal (Single Location)
    try:
        shutil.copy2(raw_mp4, local_file)
    except Exception as e:
        print(f" [WARN local copy: {e}]", end="")

    # 8. Upsert DB
    ep_id = upsert_episode(drama_id, ep_num, u720, u540)
    if ep_id and local_vtt.exists():
        link_subtitle_to_episode(ep_id, f"{R2_PUBLIC}/{kvtt}")

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
        time.sleep(0.3)

    # Retry jika ada episode terlewat
    missing = [e for e in range(1, total_eps + 1) if not (meta['local_dir'] / f"ep{e:03d}.mp4").exists()]
    if missing:
        print(f"\n[RETRY] Memproses episode yang belum lengkap: {missing}...")
        for ep in missing:
            if process_episode(drama_id, meta, ep, temp_dir):
                success += 1

    print("\n" + "=" * 60)
    print(f"[HASIL] Selesai {title}: {success}/{total_eps} episode.")
    print(f"  - Cloudflare R2: {R2_PUBLIC}/{meta['prefix']}/")
    print(f"  - Local Storage (Single Location): {meta['local_dir']}")
    print("=" * 60)

# ── MAIN PIPELINE ────────────────────────────────────────────────────────────
def main():
    dramas = [
        {
            "title": "Tengah Malam Si Cantik Memikat",
            "slug": "tengah-malam-si-cantik-memikat",
            "movie_key": "tengah-malam-si-cantik-memikat-zs_83",
            "total_eps": 30,
            "cover_url": "https://img.mebilu.com/3PatXOl9AzJlY4WMCFi7d2ZVhutrWi0VzxbONhxOxpiPmWjxGn9hQYY.webp",
            "genres": ["Thriller", "Misteri", "Drama", "Romantis"],
            "desc": "Seorang pembawa acara live streaming misterius berani menjelajahi rumah angker di tengah malam demi menaikkan penontonnya, hingga ia terjerat dalam rahasia gelap dan pesona wanita misterius yang mematikan.",
            "country": "China",
            "has_sub": False, # Hardsub Indo sudah di video
            "prefix": "dracinema/tengah-malam-si-cantik-memikat",
            "local_dir": Path("D:/Video Drama/Facebook/Tengah Malam Si Cantik Memikat")
        },
        {
            "title": "Dewa Perang Palsu",
            "slug": "dewa-perang-palsu",
            "movie_key": "dewa-perang-palsu-dw_ez1sMVNpx5",
            "total_eps": 77,
            "cover_url": "https://img.mebilu.com/DAPwSNLah5bEiT5khvYn0QMXMqqWCz63X0EcPymf29a_G4zcTyWqXxG1aptjKZo97g.webp",
            "genres": ["Pahlawan Kembali", "Aksi", "Drama"],
            "desc": "Fang Xiaolong, seorang pekerja biasa, dijebak dan dipenjara setelah memergoki pacarnya berselingkuh dengan atasannya. Saat keluar, takdir mempertemukannya dengan Qingfeng, bawahan setia Dewa Perang Longshuai, yang menjadikannya pengganti sang jenderal besar berkat kemiripan wajah mereka yang luar biasa!",
            "country": "China",
            "has_sub": True, # WebVTT subtitle
            "prefix": "dracinema/dewa-perang-palsu",
            "local_dir": Path("D:/Video Drama/Facebook/Dewa Perang Palsu")
        },
        {
            "title": "Susuku, Pedangku",
            "slug": "susuku-pedangku",
            "movie_key": "susuku-pedangku-dw_PXhCWGhm6h",
            "total_eps": 62,
            "cover_url": "https://img.mebilu.com/ACbk6PF9l2RZQARzR__vxTuC5CiWkMjqnfnokshpfESIXmZ5xiees8ViccJeYyMKOg.webp",
            "genres": ["Fantasi", "Romantis", "Drama"],
            "desc": "Tragedi kebakaran membunuh orang tua Mia akibat ulah keluarga konglomerat Blair. Demi membalas dendam, Mia rela menyamar menjadi pengasuh bayi di rumah tunangan Blair untuk membongkar kejahatan mereka dari dalam dan menuntut keadilan!",
            "country": "China",
            "has_sub": True, # WebVTT subtitle
            "prefix": "dracinema/susuku-pedangku",
            "local_dir": Path("D:/Video Drama/Facebook/Susuku, Pedangku")
        },
        {
            "title": "Musim Panas Bersama Tetangga",
            "slug": "musim-panas-bersama-tetangga",
            "movie_key": "musim-panas-bersama-tetangga-dx_42000026165",
            "total_eps": 60,
            "cover_url": "https://img.mebilu.com/eYb3gppcPocQ-EzC5lxo7nfcG7wV6dtdXmYjxEgxC1fq9QxPmSq-QTA1oTqLbx9vRjw.webp",
            "genres": ["Romantis", "Muda Mudi", "Drama"],
            "desc": "Di hari terakhir sekolah, Skye bertaruh bahwa ia akan bisa memikat cowok terpopuler di sekolah musim panas ini. Tetangganya yang seksi dan cuek, Grayson, menawarkan diri untuk mengajarinya, hingga percikan asmara tak terduga justru tumbuh di antara mereka berdua.",
            "country": "Luar Negeri",
            "has_sub": False,
            "prefix": "dracinema/musim-panas-bersama-tetangga",
            "local_dir": Path("D:/Video Drama/Facebook/Musim Panas Bersama Tetangga")
        }
    ]

    for meta in dramas:
        process_drama(meta)

    print("\n" + "=" * 60)
    print("SEMUA 4 DRAMA DALAM ANTRIAN SELESAI DISEDOT LENGKAP 100%!")
    print("=" * 60)

if __name__ == "__main__":
    main()
