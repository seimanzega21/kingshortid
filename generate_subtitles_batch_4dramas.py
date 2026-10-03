# -*- coding: utf-8 -*-
"""
Batch Subtitle Generator & Translator for 4 KingShort Dramas:
1. Agen Maut, Bodyguard Sang CEO (59 eps)
2. 11 Tahun Kemudian, Aku Bela Kamu (39 eps)
3. Bangkitnya Penguasa Roma (60 eps)
4. Cinta Takkan Berbalik (36 eps)

Workflow:
- Extracts lightweight audio from existing R2 video streams
- Translates dialogue (English / Mandarin) to fluent Indonesian WebVTT using Gemini 3.8 Flash via 9Router
- Uploads .vtt subtitles to Cloudflare R2
- Registers subtitles to KingShort DB
- Activates dramas (isActive: True) upon completion
"""
import requests
import boto3
import json
import time
import os
import sys
import subprocess
import urllib3
import base64
import tempfile
from concurrent.futures import ThreadPoolExecutor, as_completed
from botocore.config import Config

urllib3.disable_warnings()

# ─── CONFIG ────────────────────────────────────────────────────────────────
API_BASE    = 'https://api.shortlovers.id'
ADMIN_KEY   = '00ca04e3e2702be565d7bf44e783255247708289bce9b2fb6187a2e117f87fd14'
ADMIN_HDR   = {'x-admin-key': ADMIN_KEY, 'Content-Type': 'application/json'}

R2_ENDPOINT = 'https://a142d3b29a5d64943cb251157e25eaf3.r2.cloudflarestorage.com'
R2_KEY_ID   = '07c99c897986ea52703c1285308d5e2c'
R2_SECRET   = '44788d376ffb216e1e73784b6fe1ff1423607928898a87c50819b52cdfc12e44'
R2_BUCKET   = 'shortlovers'
R2_PUBLIC   = 'https://stream.shortlovers.id'

ROUTER_URL  = 'http://localhost:20128/v1/chat/completions'
ROUTER_KEY  = 'sk-6c5720214189ea51-otb97y-5446d478'
ROUTER_HDR  = {'Authorization': f'Bearer {ROUTER_KEY}', 'Content-Type': 'application/json'}

TEMP_DIR    = 'D:/kingshortid/temp_stardust'
os.makedirs(TEMP_DIR, exist_ok=True)

DRAMAS_TO_PROCESS = [
    {
        'title': 'Agen Maut, Bodyguard Sang CEO',
        'id': 'o9b24zsogwcge3g4hvcmvhlq',
        'slug': 'agen-maut-bodyguard-sang-ceo'
    },
    {
        'title': '11 Tahun Kemudian, Aku Bela Kamu',
        'id': 'a5dk4kk75mtqnz9y8oz5dqd6',
        'slug': '11-tahun-kemudian-aku-bela-kamu'
    },
    {
        'title': 'Bangkitnya Penguasa Roma',
        'id': 'dg8lv4fwsa3rsjr4k1nydv0u',
        'slug': 'bangkitnya-penguasa-roma'
    },
    {
        'title': 'Cinta Takkan Berbalik',
        'id': 'artmyoh4vsh9ehxh8cujk0bv',
        'slug': 'cinta-takkan-berbalik'
    }
]

# ─── R2 CLIENT ─────────────────────────────────────────────────────────────
def get_r2():
    return boto3.client(
        's3', endpoint_url=R2_ENDPOINT,
        aws_access_key_id=R2_KEY_ID, aws_secret_access_key=R2_SECRET,
        config=Config(signature_version='s3v4'), region_name='auto'
    )

# ─── GEMINI PROMPT & GENERATION ─────────────────────────────────────────────
SYSTEM_PROMPT = """You are an automated subtitle generator for streaming dramas.
Translate spoken dialogue (English, Mandarin Chinese, etc.) directly into natural, fluent, and dramatic Indonesian (Bahasa Indonesia).
You MUST output ONLY valid WebVTT format (.vtt).
DO NOT write any preamble, intro, notes, explanations, or markdown code blocks. Start strictly with 'WEBVTT' on line 1.

Example format:
WEBVTT

00:00:04.200 --> 00:00:07.500
Teks terjemahan bahasa Indonesia di sini.

00:00:08.100 --> 00:00:12.300
Baris percakapan berikutnya.
"""

def clean_vtt_text(raw_text):
    text = raw_text.strip()
    # Strip markdown code blocks
    if '```' in text:
        text = text.replace('```vtt', '').replace('```', '')
    idx = text.find('WEBVTT')
    if idx != -1:
        text = text[idx:]
    else:
        text = 'WEBVTT\n\n' + text
    return text.strip()

def generate_vtt_from_audio(audio_path, ep_no, drama_title):
    with open(audio_path, 'rb') as f:
        audio_b64 = base64.b64encode(f.read()).decode('utf-8')

    payload = {
        'model': 'ag/gemini-3.8-flash-low',
        'stream': False,
        'messages': [
            {'role': 'system', 'content': SYSTEM_PROMPT},
            {
                'role': 'user',
                'content': [
                    {'type': 'text', 'text': f'Transcribe dialogue from {drama_title} Episode {ep_no} and translate into Indonesian WebVTT.'},
                    {'type': 'input_audio', 'input_audio': {'data': audio_b64, 'format': 'mp3'}}
                ]
            }
        ],
        'temperature': 0.1
    }

    for attempt in range(1, 4):
        try:
            r = requests.post(ROUTER_URL, headers=ROUTER_HDR, json=payload, timeout=90)
            if r.ok:
                data = r.json()
                raw_vtt = data['choices'][0]['message']['content']
                return clean_vtt_text(raw_vtt)
            else:
                print(f"    [WARN] EP {ep_no} 9router HTTP {r.status_code}")
        except Exception as e:
            print(f"    [WARN] EP {ep_no} 9router error (attempt {attempt}/3): {e}")
        time.sleep(3)
    return None

# ─── PROCESS SINGLE EPISODE ────────────────────────────────────────────────
def process_episode(ep, drama_info, r2, total_eps):
    ep_no = ep['episodeNumber']
    ep_id = ep['id']
    slug = drama_info['slug']
    title = drama_info['title']
    video_url = ep.get('videoUrl540p') or ep.get('videoUrl')

    r2_key = f'dramas/{slug}/ep{ep_no:03d}.vtt'
    vtt_url = f'{R2_PUBLIC}/{r2_key}'

    # 1. Check if subtitle exists in DB
    try:
        sr = requests.get(f'{API_BASE}/api/episodes/{ep_id}/subtitles', timeout=10)
        if sr.ok:
            subs = sr.json().get('subtitles', [])
            if any(s.get('language') == 'id' for s in subs):
                return ep_no, True, 'in DB'
    except Exception:
        pass

    # 2. Check if already in R2
    in_r2 = False
    try:
        r2.head_object(Bucket=R2_BUCKET, Key=r2_key)
        in_r2 = True
    except Exception:
        pass

    # 3. If not in R2, extract audio & generate VTT
    if not in_r2:
        temp_audio = os.path.join(TEMP_DIR, f'{slug}_ep{ep_no:03d}_audio.mp3')
        if os.path.exists(temp_audio):
            try: os.remove(temp_audio)
            except: pass

        cmd = [
            'ffmpeg', '-y',
            '-i', video_url,
            '-vn', '-ac', '1', '-ar', '16000', '-b:a', '32k',
            '-loglevel', 'warning',
            temp_audio
        ]
        res = subprocess.run(cmd, capture_output=True, timeout=120)
        if res.returncode != 0 or not os.path.exists(temp_audio):
            return ep_no, False, 'audio extraction failed'

        vtt_content = generate_vtt_from_audio(temp_audio, ep_no, title)

        if os.path.exists(temp_audio):
            try: os.remove(temp_audio)
            except: pass

        if not vtt_content:
            return ep_no, False, 'vtt generation failed'

        # Upload VTT to R2
        try:
            r2.put_object(
                Bucket=R2_BUCKET,
                Key=r2_key,
                Body=vtt_content.encode('utf-8'),
                ContentType='text/vtt; charset=utf-8',
                CacheControl='public, max-age=31536000'
            )
        except Exception as e:
            return ep_no, False, f'R2 upload failed: {e}'

    # 4. Register subtitle to DB
    sub_payload = {
        'language': 'id',
        'label': 'Indonesian',
        'url': vtt_url,
        'isDefault': True
    }
    for attempt in range(1, 4):
        try:
            sub_r = requests.post(f'{API_BASE}/api/episodes/{ep_id}/subtitles', headers=ADMIN_HDR, json=sub_payload, timeout=20)
            if sub_r.ok:
                return ep_no, True, 'sub registered'
        except Exception:
            time.sleep(2)

    return ep_no, False, 'DB registration failed'

# ─── PROCESS SINGLE DRAMA ──────────────────────────────────────────────────
def process_drama(drama_info, r2, drama_idx, total_dramas):
    title = drama_info['title']
    did = drama_info['id']
    slug = drama_info['slug']

    print("\n" + "=" * 65)
    print(f"[{drama_idx}/{total_dramas}] {title}")
    print(f"  Drama ID : {did}")
    print(f"  Slug     : {slug}")
    print("=" * 65)

    # Fetch episodes
    r = requests.get(f'{API_BASE}/api/dramas/{did}/episodes', timeout=15)
    if not r.ok:
        print(f"  [ERROR] Failed to fetch episodes: {r.status_code}")
        return False

    episodes = r.json()
    episodes.sort(key=lambda x: x['episodeNumber'])
    total_eps = len(episodes)
    print(f"  Total episodes: {total_eps}")

    start_time = time.time()
    success_count = 0
    fail_count = 0

    with ThreadPoolExecutor(max_workers=3) as executor:
        future_map = {
            executor.submit(process_episode, ep, drama_info, r2, total_eps): ep
            for ep in episodes
        }

        for future in as_completed(future_map):
            ep_no, ok, msg = future.result()
            if ok:
                success_count += 1
                elapsed = time.time() - start_time
                eta_min = ((elapsed / max(success_count, 1)) * (total_eps - success_count)) / 60
                print(f"  [EP {ep_no:02d}/{total_eps}] OK ({msg}) | Done: {success_count}/{total_eps} | ETA: {eta_min:.1f} min")
            else:
                fail_count += 1
                print(f"  [EP {ep_no:02d}/{total_eps}] FAILED: {msg} | Done: {success_count}/{total_eps}")

    # Activate drama
    print(f"\n  Activating drama '{title}'...")
    r_act = requests.patch(
        f'{API_BASE}/api/admin/dramas/{did}',
        headers=ADMIN_HDR,
        json={'isActive': True, 'totalEpisodes': total_eps},
        timeout=20
    )
    if r_act.ok:
        print(f"  [OK] Drama '{title}' is now ACTIVE!")
    else:
        print(f"  [WARN] Activation response: {r_act.status_code} {r_act.text[:200]}")

    elapsed = time.time() - start_time
    print(f"  Finished in {elapsed/60:.1f} minutes ({success_count}/{total_eps} success)")
    return True

# ─── MAIN ───────────────────────────────────────────────────────────────────
def main():
    print("=" * 65)
    print("🎬 STARTING BATCH SUBTITLE GENERATION (4 DRAMAS)")
    print("=" * 65)

    r2 = get_r2()
    overall_start = time.time()

    for idx, d in enumerate(DRAMAS_TO_PROCESS, 1):
        try:
            process_drama(d, r2, idx, len(DRAMAS_TO_PROCESS))
        except Exception as e:
            print(f"ERROR on drama {d['title']}: {e}")
            import traceback
            traceback.print_exc()

    total_elapsed = time.time() - overall_start
    print("\n" + "=" * 65)
    print("ALL 4 DRAMAS SUBTITLE GENERATION COMPLETE!")
    print(f"Total time elapsed: {total_elapsed/60:.1f} minutes")
    print("=" * 65)

if __name__ == '__main__':
    main()
