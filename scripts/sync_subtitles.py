#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Sedot & Sinkronisasi Subtitle VTT untuk Drama Dracinema ke:
1. Local Storage (D:\Video Drama\Facebook\<TITLE>\ep{ep:03d}.vtt)
2. Cloudflare R2 ({prefix}/ep{ep:03d}.vtt)
3. KingShort DB (POST /episodes/{ep_id}/subtitles)
"""

import sys
if sys.platform == 'win32':
    sys.stdout.reconfigure(encoding='utf-8', errors='replace')
    sys.stderr.reconfigure(encoding='utf-8', errors='replace')

import os
import json
import time
import requests
import urllib3
import boto3
from pathlib import Path
from botocore.config import Config

urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

# ── CONFIG ───────────────────────────────────────────────────────────────────
API_BASE    = 'https://api.shortlovers.id/api'
ADMIN_KEY   = '00ca04e3e2702be565d7bf44e783255247708289bce9b2fb6187a2e117f87fd14'
ADMIN_HDR   = {'x-admin-key': ADMIN_KEY, 'Content-Type': 'application/json'}

R2_ENDPOINT = 'https://a142d3b29a5d64943cb251157e25eaf3.r2.cloudflarestorage.com'
R2_KEY_ID   = '07c99c897986ea52703c1285308d5e2c'
R2_SECRET   = '44788d376ffb216e1e73784b6fe1ff1423607928898a87c50819b52cdfc12e44'
R2_BUCKET   = 'shortlovers'
R2_PUBLIC   = 'https://stream.shortlovers.id'

s3 = boto3.client('s3', endpoint_url=R2_ENDPOINT,
                  aws_access_key_id=R2_KEY_ID, aws_secret_access_key=R2_SECRET,
                  config=Config(signature_version='s3v4'), region_name='auto')

DRAMA_TARGETS = [
    {
        "name": "Penguasa Sihir",
        "json_file": "drama1_urls.json",
        "prefix": "dracinema/penguasa-sihir",
        "local_dir": Path("D:/Video Drama/Facebook/Penguasa Sihir")
    },
    {
        "name": "Pengasuh Penakluk Bos Mafia",
        "json_file": "drama2_urls.json",
        "prefix": "dracinema/pengasuh-penakluk-bos-mafia",
        "local_dir": Path("D:/Video Drama/Facebook/Pengasuh Penakluk Bos Mafia")
    },
    {
        "name": "Ibu Tiri Bayaran Bos Mafia",
        "json_file": "drama3_urls.json",
        "prefix": "dracinema/ibu-tiri-bayaran-bos-mafia",
        "local_dir": Path("D:/Video Drama/Facebook/Ibu Tiri Bayaran Bos Mafia")
    }
]

def get_drama_id_by_title(title):
    try:
        r = requests.get(f"{API_BASE}/dramas?limit=1000&includeInactive=true", headers=ADMIN_HDR, timeout=15)
        if r.ok:
            for d in r.json().get('dramas', []):
                if d.get('title', '').strip().lower() == title.lower():
                    return d['id']
    except Exception as e:
        print(f"Error finding drama ID: {e}")
    return None

def get_episodes_map(drama_id):
    try:
        r = requests.get(f"{API_BASE}/dramas/{drama_id}/episodes", headers=ADMIN_HDR, timeout=15)
        if r.ok:
            # Map ep_num -> episode dict
            return {ep['episodeNumber']: ep for ep in r.json()}
    except Exception as e:
        print(f"Error fetching episodes map: {e}")
    return {}

def process_subtitles_for_drama(target):
    name = target['name']
    json_path = Path(__file__).parent / target['json_file']
    if not json_path.exists():
        print(f"File {json_path} tidak ditemukan!")
        return

    with open(json_path, 'r', encoding='utf-8') as f:
        ep_data = json.load(f)

    drama_id = get_or_create_id = get_drama_id_by_title(name)
    if not drama_id:
        print(f"[SKIP] Drama '{name}' belum terdaftar di database.")
        return

    ep_map = get_episodes_map(drama_id)
    print(f"\n[SUBTITLE] Memproses subtitle untuk '{name}' (ID: {drama_id}, {len(ep_map)} eps di DB)...")

    target['local_dir'].mkdir(parents=True, exist_ok=True)
    count = 0

    for item in ep_data:
        ep_num = item['ep']
        sub_url = item.get('sub')
        if not sub_url:
            continue

        ep_obj = ep_map.get(ep_num)
        if not ep_obj:
            continue
        ep_id = ep_obj['id']

        local_vtt = target['local_dir'] / f"ep{ep_num:03d}.vtt"
        r2_key = f"{target['prefix']}/ep{ep_num:03d}.vtt"
        r2_sub_url = f"{R2_PUBLIC}/{r2_key}"

        # 1. Download VTT
        if not local_vtt.exists() or local_vtt.stat().st_size < 50:
            try:
                r_sub = requests.get(sub_url, headers={'Referer': 'https://www.dracinema.com/'}, timeout=15)
                if r_sub.ok and len(r_sub.text) > 20:
                    with open(local_vtt, 'w', encoding='utf-8') as fp:
                        fp.write(r_sub.text)
                else:
                    print(f"  -> ep{ep_num:03d}: Gagal download subtitle (HTTP {r_sub.status_code})")
                    continue
            except Exception as e:
                print(f"  -> ep{ep_num:03d}: Error download sub: {e}")
                continue

        # 2. Upload to R2
        try:
            s3.upload_file(str(local_vtt), R2_BUCKET, r2_key, ExtraArgs={'ContentType': 'text/vtt'})
        except Exception as e:
            print(f"  -> ep{ep_num:03d}: Error upload R2 sub: {e}")
            continue

        # 3. Register to DB
        try:
            # Check existing
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
        except Exception as e:
            print(f"  -> ep{ep_num:03d}: DB sub error: {e}")

        count += 1
        print(f"  -> ep{ep_num:03d}.vtt: OK (Local + R2 + DB)")

    print(f"[SUBTITLE] Selesai '{name}': {count} subtitle terpasang!")

def main():
    print("=" * 60)
    print("SINKRONISASI SUBTITLE DRAMA DRACINEMA")
    print("=" * 60)
    for target in DRAMA_TARGETS:
        process_subtitles_for_drama(target)

if __name__ == "__main__":
    main()
