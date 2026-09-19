#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Backfill ep 27, 28, 29, 30 untuk Pacar Saudariku Menjebakku
"""
import sys
if sys.platform == 'win32':
    sys.stdout.reconfigure(encoding='utf-8', errors='replace')
    sys.stderr.reconfigure(encoding='utf-8', errors='replace')

import requests, boto3, subprocess, time, tempfile, urllib3, re, os, shutil, json
from pathlib import Path
from botocore.config import Config

urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

API_BASE    = 'https://api.shortlovers.id/api'
ADMIN_KEY   = '00ca04e3e2702be565d7bf44e783255247708289bce9b2fb6187a2e117f87fd14'
ADMIN_HDR   = {'x-admin-key': ADMIN_KEY, 'Content-Type': 'application/json'}

R2_ENDPOINT = 'https://a142d3b29a5d64943cb251157e25eaf3.r2.cloudflarestorage.com'
R2_KEY_ID   = '07c99c897986ea52703c1285308d5e2c'
R2_SECRET   = '44788d376ffb216e1e73784b6fe1ff1423607928898a87c50819b52cdfc12e44'
R2_BUCKET   = 'shortlovers'
R2_PUBLIC   = 'https://stream.shortlovers.id'

VIDRAMA_API = 'https://vidrama.asia/api/netshortv2'
WEB_HDRS    = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/147.0.0.0 Safari/537.36',
    'Referer': 'https://vidrama.asia/',
}

TEMP_DIR = Path(tempfile.gettempdir()) / 'ns2_backfill_pacar'
TEMP_DIR.mkdir(exist_ok=True)

FFMPEG_BIN = r'C:\ProgramData\chocolatey\bin\ffmpeg.exe'
if not os.path.exists(FFMPEG_BIN):
    FFMPEG_BIN = shutil.which('ffmpeg') or 'ffmpeg'

r2 = boto3.client('s3', endpoint_url=R2_ENDPOINT,
                  aws_access_key_id=R2_KEY_ID, aws_secret_access_key=R2_SECRET,
                  config=Config(signature_version='s3v4'), region_name='auto')

vid = '2098979214770876418'
slug = 'pacar-saudariku-menjebakku'
db_id = 'n10716h9l7e4y1dkz9vo45g6'
title = 'Pacar Saudariku Menjebakku'
prefix = f'netshortv2/{slug}'

local_save_dir = Path("D:/Video Drama/Facebook") / title
local_save_dir.mkdir(parents=True, exist_ok=True)

for ep_no in [27, 28, 29, 30]:
    k720 = f"{prefix}/ep{ep_no:03d}.mp4"
    k540 = f"{prefix}/ep{ep_no:03d}_540p.mp4"
    ksub = f"{prefix}/ep{ep_no:03d}.vtt"
    local_file = local_save_dir / f"ep{ep_no:03d}.mp4"

    print(f"Mengambil ep{ep_no:03d}...", end="", flush=True)
    vurls = []
    sub_url_raw = None
    for attempt in range(5):
        try:
            r = requests.get(f"{VIDRAMA_API}/episode/{vid}/{ep_no}?lang=id_ID", headers=WEB_HDRS, verify=False, timeout=20)
            if r.ok and r.json().get('code') == 200:
                vurls = [v['url'] for v in r.json().get('data', {}).get('videos', [])]
                subs = r.json().get('data', {}).get('subtitles', [])
                if subs: sub_url_raw = subs[0].get('url')
                if vurls: break
        except: pass
        time.sleep(2)

    if not vurls:
        print(" [GAGAL DAPAT URL]")
        continue

    final_sub_r2 = None
    if sub_url_raw:
        try:
            sub_r = requests.get(sub_url_raw, timeout=10, verify=False)
            if sub_r.ok:
                r2.put_object(Bucket=R2_BUCKET, Key=ksub, Body=sub_r.content, ContentType='text/vtt')
                final_sub_r2 = f"{R2_PUBLIC}/{ksub}"
        except: pass

    raw = TEMP_DIR / f"raw_{ep_no}.mp4"
    o720 = TEMP_DIR / f"720_{ep_no}.mp4"
    o540 = TEMP_DIR / f"540_{ep_no}.mp4"

    for vurl in vurls:
        with requests.get(vurl, stream=True, headers={'User-Agent': 'Mozilla/5.0'}, verify=False, timeout=60) as r_dl:
            if r_dl.status_code == 200:
                with open(raw, 'wb') as f:
                    for c in r_dl.iter_content(2*1024*1024):
                        if c: f.write(c)
                break

    cmd = [FFMPEG_BIN, '-y', '-i', str(raw), '-c:v', 'libx264', '-crf', '26', '-maxrate', '1500k', '-bufsize', '3000k',
           '-c:a', 'aac', '-b:a', '128k', '-movflags', '+faststart', '-loglevel', 'error', str(o720)]
    subprocess.run(cmd, check=True)

    cmd2 = [FFMPEG_BIN, '-y', '-i', str(o720), '-vf', 'scale=-2:540', '-c:v', 'libx264', '-crf', '28', '-preset', 'fast',
            '-c:a', 'aac', '-b:a', '96k', '-movflags', '+faststart', '-loglevel', 'error', str(o540)]
    subprocess.run(cmd2, check=True)

    r2.upload_file(str(o720), R2_BUCKET, k720, ExtraArgs={'ContentType': 'video/mp4'})
    r2.upload_file(str(o540), R2_BUCKET, k540, ExtraArgs={'ContentType': 'video/mp4'})

    u720 = f"{R2_PUBLIC}/{k720}"
    u540 = f"{R2_PUBLIC}/{k540}"

    payload = {'episodeNumber': ep_no, 'title': f'Episode {ep_no}', 'videoUrl': u720, 'isActive': True, 'videoUrl540p': u540}
    r_api = requests.post(f"{API_BASE}/admin/dramas/{db_id}/episodes", headers=ADMIN_HDR, json=payload, timeout=20)
    ep_id = r_api.json().get('id')
    if ep_id and final_sub_r2:
        sub_payload = {'language': 'indonesia', 'label': 'Indonesia', 'url': final_sub_r2, 'isDefault': True}
        requests.post(f"{API_BASE}/episodes/{ep_id}/subtitles", headers=ADMIN_HDR, json=sub_payload, timeout=10)

    try: shutil.copy2(o720, local_file)
    except: pass

    for p in [raw, o720, o540]:
        if p.exists():
            try: p.unlink()
            except: pass

    print(" SUKSES")

print("\nSELESAI_BACKFILL_PACAR")
