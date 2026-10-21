#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Fix Subtitles for Drama: Jodoh Kita Telah Berakhir (Drama ID: qaw689g77h7ybo64y4jubp6n)
1. Download official Indonesian subtitles from Dramabox (hwztakavideoto.dramaboxdb.com).
2. Convert SRT to clean, valid WebVTT format with double newlines.
3. Upload to Cloudflare R2: dramas/jodoh-kita-telah-berakhir/subtitles/epXXX.vtt.
4. Save local copy to: D:\\Video Drama\\Facebook\\Jodoh Kita Telah Berakhir\\epXXX.vtt.
5. Clean old broken vidrama proxy records in PostgreSQL via SSH.
6. Register new clean subtitles into KingShort DB.
"""

import sys
if sys.platform == 'win32':
    sys.stdout.reconfigure(encoding='utf-8', errors='replace')
    sys.stderr.reconfigure(encoding='utf-8', errors='replace')

import os
import re
import json
import urllib.parse
import requests
import paramiko
import boto3
from pathlib import Path
from botocore.config import Config

# ── CONFIGURATION ─────────────────────────────────────────────────────────────
API_BASE    = 'https://api.shortlovers.id/api'
ADMIN_KEY   = '00ca04e3e2702be565d7bf44e783255247708289bce9b2fb6187a2e117f87fd14'
ADMIN_HDR   = {'x-admin-key': ADMIN_KEY, 'Content-Type': 'application/json'}

R2_ENDPOINT = 'https://a142d3b29a5d64943cb251157e25eaf3.r2.cloudflarestorage.com'
R2_KEY_ID   = '07c99c897986ea52703c1285308d5e2c'
R2_SECRET   = '44788d376ffb216e1e73784b6fe1ff1423607928898a87c50819b52cdfc12e44'
R2_BUCKET   = 'shortlovers'
R2_PUBLIC   = 'https://stream.shortlovers.id'

DRAMA_ID    = 'qaw689g77h7ybo64y4jubp6n'
TITLE       = 'Jodoh Kita Telah Berakhir'
PREFIX      = 'dramas/jodoh-kita-telah-berakhir/subtitles'

LOCAL_DIR   = Path("D:/Video Drama/Facebook") / TITLE
LOCAL_DIR.mkdir(parents=True, exist_ok=True)

SSH_HOST    = '141.11.160.187'
SSH_USER    = 'root'
SSH_PASS    = 'Surya123!'

# ── R2 CLIENT ─────────────────────────────────────────────────────────────────
s3 = boto3.client('s3', endpoint_url=R2_ENDPOINT,
                  aws_access_key_id=R2_KEY_ID, aws_secret_access_key=R2_SECRET,
                  config=Config(signature_version='s3v4'), region_name='auto')

# ── SRT TO CLEAN WEBVTT ───────────────────────────────────────────────────────
time_re = re.compile(r'(\d{2}:)?(\d{2}:\d{2}[.,]\d{3})\s*-->\s*(\d{2}:)?(\d{2}:\d{2}[.,]\d{3})')

def srt_to_clean_vtt(srt_text):
    lines = srt_text.replace('\r\n', '\n').replace('\r', '\n').split('\n')
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

# ── DELETE OLD BROKEN SUBTITLES IN DATABASE ───────────────────────────────────
def delete_old_subtitles_in_db():
    print(f"\n[DB] Menghapus subtitle lama yang rusak untuk drama {TITLE} ({DRAMA_ID})...")
    try:
        ssh = paramiko.SSHClient()
        ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
        ssh.connect(SSH_HOST, username=SSH_USER, password=SSH_PASS, timeout=10)
        query = f"DELETE FROM subtitles WHERE episode_id IN (SELECT id FROM episodes WHERE drama_id = '{DRAMA_ID}');"
        cmd = f'docker exec -i supabase-db-og8gwooogk480gcws0o84ssc psql -U postgres -d postgres -c "{query}"'
        stdin, stdout, stderr = ssh.exec_command(cmd)
        res = stdout.read().decode('utf-8').strip()
        print(f"  -> Hasil SQL: {res}")
        ssh.close()
        return True
    except Exception as e:
        print(f"  [WARN] Gagal hapus subtitle via SSH: {e}")
        return False

# ── MAIN PIPELINE ────────────────────────────────────────────────────────────
def main():
    print("=" * 60)
    print(f"PERBAIKAN SUBTITLE: {TITLE} (Drama ID: {DRAMA_ID})")
    print("=" * 60)

    # 1. Ambil data episode dari KingShort API
    print("\n[1/4] Mengambil daftar episode dari KingShort API...")
    r = requests.get(f"{API_BASE}/dramas/{DRAMA_ID}", headers=ADMIN_HDR, timeout=15)
    if not r.ok:
        print(f"[ERROR] Gagal ambil drama: {r.status_code}")
        return

    episodes = sorted(r.json().get('episodes', []), key=lambda x: x['episodeNumber'])
    total = len(episodes)
    print(f"  -> Ditemukan {total} episode di database.")

    # 2. Hapus subtitle lama yang rusak (proxy vidrama.asia mati)
    delete_old_subtitles_in_db()

    # 3. Download, konversi ke VTT, upload R2, dan daftarkan ke DB
    print(f"\n[2/4] Mengunduh subtitle Dramabox & Upload ke Cloudflare R2...")
    headers = {'User-Agent': 'Mozilla/5.0'}
    success_count = 0

    for ep in episodes:
        num = ep['episodeNumber']
        ep_id = ep['id']
        subs = ep.get('subtitles', [])
        old_url = subs[0]['url'] if subs else ''

        # Ekstrak URL asli Dramabox dari proxy vidrama lama
        parsed = urllib.parse.urlparse(old_url)
        params = urllib.parse.parse_qs(parsed.query)
        target = params.get('url', [None])[0]

        if not target:
            # Fallback jika tidak ada query params: tebak pattern atau cari dari source
            print(f"  -> Ep {num:02d}: [GAGAL - URL asal tidak ditemukan]")
            continue

        # Ganti domain mati hwztakavideo -> hwztakavideoto
        direct_url = target.replace('hwztakavideo.dramaboxdb.com', 'hwztakavideoto.dramaboxdb.com')

        try:
            r_srt = requests.get(direct_url, headers=headers, timeout=10)
            if not r_srt.ok or len(r_srt.text) < 50:
                print(f"  -> Ep {num:02d}: [GAGAL DOWNLOAD: {r_srt.status_code}]")
                continue

            # Konversi SRT ke WebVTT
            vtt_content = srt_to_clean_vtt(r_srt.text)

            # Simpan lokal
            local_vtt = LOCAL_DIR / f"ep{num:03d}.vtt"
            local_vtt.write_text(vtt_content, encoding='utf-8')

            # Upload ke Cloudflare R2
            r2_key = f"{PREFIX}/ep{num:03d}.vtt"
            s3.upload_file(str(local_vtt), R2_BUCKET, r2_key, ExtraArgs={'ContentType': 'text/vtt'})
            r2_url = f"{R2_PUBLIC}/{r2_key}"

            # Daftarkan ke KingShort DB
            sub_payload = {
                'language': 'indonesia',
                'label': 'Indonesia',
                'url': r2_url,
                'isDefault': True
            }
            r_link = requests.post(f"{API_BASE}/episodes/{ep_id}/subtitles", headers=ADMIN_HDR, json=sub_payload, timeout=10)

            if r_link.ok:
                print(f"  -> Ep {num:02d}: OK! ({len(vtt_content.splitlines())} baris VTT -> R2 & DB)")
                success_count += 1
            else:
                print(f"  -> Ep {num:02d}: Upload R2 OK, tapi gagal link DB ({r_link.status_code})")

        except Exception as e:
            print(f"  -> Ep {num:02d}: Exception {e}")

    print("\n" + "=" * 60)
    print(f"[HASIL AKHIR] Berhasil memperbaiki subtitle: {success_count}/{total} episode!")
    print(f"  - Cloudflare R2: {R2_PUBLIC}/{PREFIX}/")
    print(f"  - Local Storage: {LOCAL_DIR}")
    print("=" * 60)

if __name__ == "__main__":
    main()
