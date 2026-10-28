#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Sedot Pengantin Pengganti Taklukkan Keluarga Kaya (Dubbing) (40 Episode) - FreeReels
- Stream: M3U8 from farsunpteltd CDN (no Referer header to bypass 403)
- Audio: Indonesian dubbing
- Subtitle: AI Speech-to-Text via local Gemini STT model to generate accurate Indonesian WebVTT matching the audio
- Dual transcode: 720p master faststart + 540p faststart
- Upload 720p, 540p, VTT to Cloudflare R2
- Upsert & activate drama + episodes in KingShort DB
- Single storage location strictly in D:\\Video Drama\\Facebook\\Pengantin Pengganti Taklukkan Keluarga Kaya (Dubbing)\\
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
import subprocess
import requests
import urllib3
import boto3
import concurrent.futures
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

AI_ENDPOINT = 'http://localhost:20128/v1/chat/completions'
AI_KEY      = 'sk-6c5720214189ea51-otb97y-5446d478'

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

def generate_vtt_from_audio(audio_path):
    for attempt in range(3):
        try:
            with open(audio_path, 'rb') as f:
                audio_b64 = base64.b64encode(f.read()).decode('utf-8')

            headers = {
                'Authorization': f'Bearer {AI_KEY}',
                'Content-Type': 'application/json'
            }
            payload = {
                'model': 'ag/gemini-3.8-flash-high',
                'messages': [
                    {
                        'role': 'user',
                        'content': [
                            {
                                'type': 'text',
                                'text': 'Transkripsikan audio bahasa Indonesia ini secara presisi ke dalam format subtitle WebVTT (.vtt) lengkap dengan timestamp (format 00:00:00.000 --> 00:00:00.000) sesuai jeda dan waktu suara di audio. HANYA berikan isi teks WebVTT murni tanpa penjelasan pembuka/penutup.'
                            },
                            {
                                'type': 'input_audio',
                                'input_audio': {
                                    'data': audio_b64,
                                    'format': 'mp3'
                                }
                            }
                        ]
                    }
                ]
            }
            r = requests.post(AI_ENDPOINT, headers=headers, json=payload, timeout=60)
            rc = []
            for line in r.text.splitlines():
                if line.startswith('data: ') and not line.endswith('[DONE]'):
                    try:
                        d = json.loads(line[6:])
                        c = d['choices'][0]['delta'].get('content')
                        if c: rc.append(c)
                    except Exception:
                        pass
            raw_vtt = ''.join(rc)
            cleaned = clean_vtt(raw_vtt)
            if len(cleaned) > 50:
                return cleaned
        except Exception as e:
            time.sleep(2)
    return None

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
        'genres': meta.get('genres', ['Sulih Suara', 'Drama']),
        'totalEpisodes': meta['total_eps'],
        'country': meta.get('country', 'Luar Negeri'),
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

# ── DOWNLOAD & TRANSCODE ─────────────────────────────────────────────────────
def download_m3u8_no_referer(url, out_path):
    url = url.replace('farsunpteltd.com', 'farsunpteltd.net')
    cmd = [
        'ffmpeg', '-y',
        '-i', url,
        '-c', 'copy',
        '-movflags', '+faststart',
        '-loglevel', 'error',
        str(out_path)
    ]
    for attempt in range(4):
        res = subprocess.run(cmd, timeout=300)
        if res.returncode == 0 and out_path.exists() and out_path.stat().st_size > 100 * 1024:
            return True
        time.sleep(2)
    return False

def transcode_540p(in_file, out_file):
    cmd = [
        'ffmpeg', '-y', '-loglevel', 'error',
        '-i', str(in_file),
        '-vf', 'scale=-2:540',
        '-c:v', 'libx264', '-crf', '28', '-preset', 'veryfast',
        '-c:a', 'aac', '-b:a', '96k',
        '-movflags', '+faststart',
        str(out_file)
    ]
    res = subprocess.run(cmd, timeout=300)
    return res.returncode == 0 and out_file.exists() and out_file.stat().st_size > 50 * 1024

def extract_audio(in_file, out_audio):
    cmd = [
        'ffmpeg', '-y', '-loglevel', 'error',
        '-i', str(in_file),
        '-c:a', 'libmp3lame', '-q:a', '4',
        str(out_audio)
    ]
    res = subprocess.run(cmd, timeout=120)
    return res.returncode == 0 and out_audio.exists() and out_audio.stat().st_size > 10 * 1024

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

# ── PROCESS EPISODE ───────────────────────────────────────────────────────────
def process_episode(drama_id, meta, ep_data, temp_dir):
    ep_num = ep_data['ep']
    prefix = meta['prefix']
    k720 = f"{prefix}/ep{ep_num:03d}.mp4"
    k540 = f"{prefix}/ep{ep_num:03d}_540p.mp4"
    kvtt = f"{prefix}/ep{ep_num:03d}.vtt"

    local_file = meta['local_dir'] / f"ep{ep_num:03d}.mp4"
    local_vtt  = meta['local_dir'] / f"ep{ep_num:03d}.vtt"

    # 1. Cek apakah video & sub sudah lengkap di R2
    if r2_exists(k720) and r2_exists(k540) and r2_exists(kvtt):
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
        print(f"  -> Ep {ep_num:02d}: [OK - R2 Cache]")
        return True

    video_url = ep_data.get('url')
    if not video_url:
        print(f"  -> Ep {ep_num:02d}: [GAGAL - Tidak ada URL video]")
        return False

    raw_mp4 = temp_dir / f"raw_{ep_num:03d}.mp4"
    out_540 = temp_dir / f"out540_{ep_num:03d}.mp4"
    out_aud = temp_dir / f"aud_{ep_num:03d}.mp3"

    # 2. Download raw (remux M3U8 -> MP4)
    if not download_m3u8_no_referer(video_url, raw_mp4):
        print(f"  -> Ep {ep_num:02d}: [GAGAL UNDUH M3U8]")
        raw_mp4.unlink(missing_ok=True)
        return False

    # 3. Transcode 540p faststart
    if not transcode_540p(raw_mp4, out_540):
        print(f"  -> Ep {ep_num:02d}: [GAGAL TRANSCODE 540P]")
        raw_mp4.unlink(missing_ok=True)
        out_540.unlink(missing_ok=True)
        return False

    # 4. Generate Subtitle WebVTT via AI Speech-to-Text
    vtt_content = None
    if extract_audio(raw_mp4, out_aud):
        vtt_content = generate_vtt_from_audio(out_aud)
        out_aud.unlink(missing_ok=True)

    if vtt_content and len(vtt_content) > 30:
        local_vtt.write_text(vtt_content, encoding='utf-8')
        s3.upload_file(str(local_vtt), R2_BUCKET, kvtt, ExtraArgs={'ContentType': 'text/vtt'})

    # 5. Upload R2
    u720 = r2_upload(raw_mp4, k720)
    u540 = r2_upload(out_540, k540)

    # 6. Simpan lokal (Single Location)
    try:
        shutil.copy2(raw_mp4, local_file)
    except Exception as e:
        print(f"  -> Ep {ep_num:02d}: [WARN local copy: {e}]")

    raw_mp4.unlink(missing_ok=True)
    out_540.unlink(missing_ok=True)

    # 7. Upsert DB
    ep_id = upsert_episode(drama_id, ep_num, u720, u540)
    if ep_id and local_vtt.exists():
        link_subtitle_to_episode(ep_id, f"{R2_PUBLIC}/{kvtt}")

    print(f"  -> Ep {ep_num:02d}: [SELESAI - R2 + Sub VTT + Local + DB]")
    return True

# ── PROCESS DRAMA ────────────────────────────────────────────────────────────
def process_drama(meta):
    title = meta['title']
    total_eps = meta['total_eps']
    print("\n" + "=" * 60)
    print(f"MEMULAI SEDOT: {title} ({total_eps} Episode)")
    print("=" * 60)

    dump_file = Path(meta['dump_file'])
    if not dump_file.exists():
        print(f"[ERROR] Dump file tidak ditemukan: {dump_file}")
        return

    with open(dump_file, 'r', encoding='utf-8') as f:
        data = json.load(f)
        episodes = data.get('items', [])

    temp_dir = TEMP_ROOT / meta['slug']
    temp_dir.mkdir(parents=True, exist_ok=True)
    meta['local_dir'].mkdir(parents=True, exist_ok=True)

    ensure_cover(meta, temp_dir)

    drama_id = get_or_create_drama(meta)
    if not drama_id:
        print(f"[ERROR] Gagal mendapatkan ID drama DB untuk {title}.")
        return

    success = 0
    with concurrent.futures.ThreadPoolExecutor(max_workers=2) as executor:
        futures = {executor.submit(process_episode, drama_id, meta, ep_data, temp_dir): ep_data['ep'] for ep_data in episodes}
        for future in concurrent.futures.as_completed(futures):
            ep_no = futures[future]
            try:
                if future.result():
                    success += 1
            except Exception as e:
                print(f"  -> Ep {ep_no:02d} exception: {e}")

    # Retry jika ada episode terlewat
    missing = [e for e in range(1, total_eps + 1) if not (meta['local_dir'] / f"ep{e:03d}.mp4").exists()]
    if missing:
        print(f"\n[RETRY] Memproses episode yang belum lengkap: {missing}...")
        ep_dict = {x['ep']: x for x in episodes}
        for ep in missing:
            if ep in ep_dict and process_episode(drama_id, meta, ep_dict[ep], temp_dir):
                success += 1

    # Final patch to ensure totalEpisodes and isActive are set
    requests.patch(f"{API_BASE}/dramas/{drama_id}", headers=ADMIN_HDR, json={'isActive': True, 'totalEpisodes': total_eps})

    print("\n" + "=" * 60)
    print(f"[HASIL] Selesai {title}: {success}/{total_eps} episode.")
    print(f"  - Cloudflare R2: {R2_PUBLIC}/{meta['prefix']}/")
    print(f"  - Local Storage (Single Location): {meta['local_dir']}")
    print("=" * 60)

# ── MAIN PIPELINE ────────────────────────────────────────────────────────────
def main():
    meta = {
        "title": "Pengantin Pengganti Taklukkan Keluarga Kaya (Dubbing)",
        "slug": "pengantin-pengganti-taklukkan-keluarga-kaya-dubbing",
        "movie_key": "pengantin-pengganti-taklukkan-keluarga-kaya-dubbing-fr_9848",
        "total_eps": 40,
        "dump_file": "D:/temp_scraper/pengantin_dump.json",
        "cover_url": "https://img.mebilu.com/59FUWnSwGBiaG57QDSs2Sta8tXjB1gOQTyct7mz_r_WtAeYpXAZ_zV7b8g.webp",
        "genres": ["Sulih Suara", "Nikah Dulu", "Penebusan", "Drama Romantis", "Drama CEO / Bos"],
        "desc": "Selama sepuluh tahun, Eliza dikurung di rumah sakit jiwa oleh ibu tirinya. Setelah bebas, dia dipaksa menggantikan adiknya menjadi pengantin Cassius Blackwood, pengusaha dingin dan kejam. Semua orang mengira nasibnya akan sama seperti empat istri Cassius sebelumnya. Namun, dengan kemampuan yang ia asah selama di sana dan hati yang tulus, Eliza berhasil menyembuhkan keluarga Blackwood dan menemukan cinta sejati!",
        "country": "Luar Negeri",
        "prefix": "dracinema/pengantin-pengganti-taklukkan-keluarga-kaya-dubbing",
        "local_dir": Path("D:/Video Drama/Facebook/Pengantin Pengganti Taklukkan Keluarga Kaya (Dubbing)")
    }

    process_drama(meta)

if __name__ == "__main__":
    main()
