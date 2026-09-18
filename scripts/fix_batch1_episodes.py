#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Fix / Backfill episode bolong untuk 2 drama Batch 1:
1. Panduan Menaklukkan Raja Duyung (35 eps, bolong 17 eps)
2. Mangsa Adipati Iblis (30 eps, bolong 6 eps)
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

TEMP_DIR = Path(tempfile.gettempdir()) / 'ns2_backfill'
TEMP_DIR.mkdir(exist_ok=True)

FFMPEG_BIN = r'C:\ProgramData\chocolatey\bin\ffmpeg.exe'
if not os.path.exists(FFMPEG_BIN):
    FFMPEG_BIN = shutil.which('ffmpeg') or 'ffmpeg'

def get_r2():
    return boto3.client('s3', endpoint_url=R2_ENDPOINT,
                        aws_access_key_id=R2_KEY_ID, aws_secret_access_key=R2_SECRET,
                        config=Config(signature_version='s3v4'), region_name='auto')

def r2_exists(r2, key):
    try:
        r2.head_object(Bucket=R2_BUCKET, Key=key)
        return True
    except:
        return False

def r2_upload(r2, local_path, key, content_type='video/mp4'):
    r2.upload_file(str(local_path), R2_BUCKET, key, ExtraArgs={'ContentType': content_type},
                    Config=boto3.s3.transfer.TransferConfig(multipart_threshold=30*1024*1024, multipart_chunksize=10*1024*1024))
    return f"{R2_PUBLIC}/{key}"

def get_episode_url(drama_id, ep_no, retries=5):
    url = f"{VIDRAMA_API}/episode/{drama_id}/{ep_no}?lang=id_ID"
    for attempt in range(retries):
        try:
            r = requests.get(url, headers=WEB_HDRS, timeout=20, verify=False)
            data = r.json()
            if data.get('code') == 200:
                videos = data['data'].get('videos', [])
                subs = data['data'].get('subtitles', [])
                id_sub = next((s['url'] for s in subs if s.get('language') == 'id_ID'), None)
                if not id_sub and subs: id_sub = subs[0]['url']
                vurls = [v['url'] for v in videos]
                if vurls:
                    return vurls, id_sub
        except: pass
        time.sleep(1.5 * (attempt + 1))
    return [], None

def api_upsert_episode(drama_db_id, ep_no, url_720, url_540=None, sub_url=None):
    payload = {'episodeNumber': ep_no, 'title': f'Episode {ep_no}', 'videoUrl': url_720, 'isActive': True}
    if url_540: payload['videoUrl540p'] = url_540
    r = requests.post(f"{API_BASE}/admin/dramas/{drama_db_id}/episodes", headers=ADMIN_HDR, json=payload, timeout=20)
    if not r.ok: return None
    ep_id = r.json().get('id')
    if ep_id and sub_url:
        sub_payload = {'language': 'indonesia', 'label': 'Indonesia', 'url': sub_url, 'isDefault': True}
        requests.post(f"{API_BASE}/episodes/{ep_id}/subtitles", headers=ADMIN_HDR, json=sub_payload, timeout=10)
    return ep_id

def encode_720_and_540(inp, out_720, out_540):
    cmd = [FFMPEG_BIN, '-y', '-i', str(inp), '-c:v', 'libx264', '-crf', '26', '-maxrate', '1500k', '-bufsize', '3000k',
           '-c:a', 'aac', '-b:a', '128k', '-movflags', '+faststart', '-loglevel', 'error', str(out_720)]
    res = subprocess.run(cmd, timeout=600)
    if res.returncode != 0: return False
    cmd3 = [FFMPEG_BIN, '-y', '-i', str(out_720), '-vf', 'scale=-2:540', '-c:v', 'libx264', '-crf', '28', '-preset', 'fast',
            '-c:a', 'aac', '-b:a', '96k', '-movflags', '+faststart', '-loglevel', 'error', str(out_540)]
    return subprocess.run(cmd3, timeout=600).returncode == 0

def backfill_drama(r2, vidrama_id, slug, db_id, total_eps, title):
    prefix = f"netshortv2/{slug}"
    local_save_dir = Path("D:/Video Drama/Facebook") / title.replace(":", " ").replace("/", " ")
    local_save_dir.mkdir(parents=True, exist_ok=True)
    print(f"\n[*] MEMERIKSA EPISODE BOLONG: {title} ({total_eps} eps)")

    for ep_no in range(1, total_eps + 1):
        k720 = f"{prefix}/ep{ep_no:03d}.mp4"
        k540 = f"{prefix}/ep{ep_no:03d}_540p.mp4"
        ksub = f"{prefix}/ep{ep_no:03d}.vtt"
        local_file = local_save_dir / f"ep{ep_no:03d}.mp4"

        # Cek jika di R2 sudah ada
        if r2_exists(r2, k720):
            u720 = f"{R2_PUBLIC}/{k720}"
            u540 = f"{R2_PUBLIC}/{k540}" if r2_exists(r2, k540) else None
            sub_url = f"{R2_PUBLIC}/{ksub}" if r2_exists(r2, ksub) else None
            api_upsert_episode(db_id, ep_no, u720, u540, sub_url)
            continue

        print(f"  -> Mendownload episode bolong: ep{ep_no:03d}...", end="", flush=True)
        vurls, sub_url_raw = get_episode_url(vidrama_id, ep_no)
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

        raw = TEMP_DIR / f"{slug}_raw_{ep_no}.mp4"
        o720 = TEMP_DIR / f"{slug}_720_{ep_no}.mp4"
        o540 = TEMP_DIR / f"{slug}_540_{ep_no}.mp4"

        try:
            download_success = False
            for vurl in vurls:
                if download_success: break
                for attempt in range(3):
                    cdn_hdrs = {'User-Agent': WEB_HDRS['User-Agent'], 'Referer': 'https://vidrama.asia/', 'Accept': '*/*'}
                    try:
                        with requests.get(vurl, stream=True, headers=cdn_hdrs, verify=False, timeout=60) as r:
                            if r.status_code == 200:
                                with open(raw, 'wb') as f:
                                    for c in r.iter_content(2*1024*1024):
                                        if c: f.write(c)
                                if raw.exists() and (raw.stat().st_size / 1024) > 50:
                                    download_success = True
                                    break
                    except: pass
                    time.sleep(1)

            if not download_success:
                print(" [GAGAL DOWNLOAD]")
                continue

            print(" Mengompres...", end="", flush=True)
            if encode_720_and_540(raw, o720, o540):
                u720 = r2_upload(r2, o720, k720)
                u540 = r2_upload(r2, o540, k540) if o540.exists() else None
                api_upsert_episode(db_id, ep_no, u720, u540, final_sub_r2)
                try: shutil.copy2(o720, local_file)
                except: pass
                print(" SUKSES")
            else:
                print(" [GAGAL ENCODE]")

        except Exception as e:
            print(f" [ERROR: {e}]")
        finally:
            for p in [raw, o720, o540]:
                if p.exists():
                    try: p.unlink()
                    except: pass

def main():
    r2 = get_r2()
    print("="*60)
    print("🛠️ MEMULAI PERBAIKAN EPISODE BOLONG BATCH 1")
    print("="*60)

    # 1. Mangsa Adipati Iblis (24/30 eps)
    backfill_drama(
        r2,
        vidrama_id='2100050898689167361',
        slug='mangsa-adipati-iblis',
        db_id='ln0iti4x72297dc3gdj4xh26',
        total_eps=30,
        title='Mangsa Adipati Iblis'
    )

    # 2. Panduan Menaklukkan Raja Duyung (18/35 eps)
    backfill_drama(
        r2,
        vidrama_id='2100051779434283009',
        slug='panduan-menaklukkan-raja-duyung',
        db_id='m7v9212j2q6s82m049q46462',
        total_eps=35,
        title='Panduan Menaklukkan Raja Duyung'
    )

    print("\n🎉 PERBAIKAN EPISODE SELESAI!")

if __name__ == '__main__':
    main()
