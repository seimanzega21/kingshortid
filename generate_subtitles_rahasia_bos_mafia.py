# -*- coding: utf-8 -*-
"""
Generate Indonesian WebVTT Subtitles for Rahasia Bos Mafia (70 Episodes)
- Extracts audio from KingShort R2 stream
- Uses local 9router Gemini 3.8 Flash to transcribe & translate into natural Indonesian
- Formats as standard WebVTT (.vtt)
- Uploads to Cloudflare R2: dramas/rahasia-bos-mafia/epXXX.vtt
- Registers to KingShort Database (/api/episodes/{id}/subtitles)
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

DRAMA_ID_DB = 'or0w0pt2n3g3mzmrje5sdqq7'
DRAMA_SLUG  = 'rahasia-bos-mafia'

ROUTER_URL  = 'http://localhost:20128/v1/chat/completions'
ROUTER_KEY  = 'sk-6c5720214189ea51-otb97y-5446d478'
ROUTER_HDR  = {'Authorization': f'Bearer {ROUTER_KEY}', 'Content-Type': 'application/json'}

TEMP_DIR    = 'D:/kingshortid/temp_stardust'
os.makedirs(TEMP_DIR, exist_ok=True)

# ─── R2 CLIENT ─────────────────────────────────────────────────────────────
def get_r2():
    return boto3.client(
        's3', endpoint_url=R2_ENDPOINT,
        aws_access_key_id=R2_KEY_ID, aws_secret_access_key=R2_SECRET,
        config=Config(signature_version='s3v4'), region_name='auto'
    )

# ─── GEMINI SUBTITLE GENERATION ─────────────────────────────────────────────
SYSTEM_PROMPT = """You are an expert subtitle translator for cinematic drama.
Listen to the English audio dialogue and translate all spoken words directly into fluent, natural, dramatic Indonesian (Bahasa Indonesia).
Output MUST be strict standard WebVTT format (.vtt).
DO NOT include any markdown code fences, notes, explanation, or commentary. Start immediately with 'WEBVTT' on the first line.
Timing rules:
- Timestamps must accurately match the spoken speech: 00:00:00.000 --> 00:00:00.000
- Keep subtitles concise and readable (max 2 lines per cue).
"""

def generate_vtt_from_audio(audio_path, ep_no):
    """Sends audio to 9router Gemini 3.8 Flash to get WebVTT in Indonesian"""
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
                    {'type': 'text', 'text': f'Transcribe Episode {ep_no} dialogue and translate into Indonesian WebVTT format.'},
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
                vtt = data['choices'][0]['message']['content'].strip()
                # Strip markdown code blocks if model added them
                if vtt.startswith('```'):
                    lines = vtt.split('\n')
                    if lines[0].startswith('```'): lines = lines[1:]
                    if lines and lines[-1].startswith('```'): lines = lines[:-1]
                    vtt = '\n'.join(lines).strip()
                if not vtt.startswith('WEBVTT'):
                    vtt = 'WEBVTT\n\n' + vtt
                return vtt
            else:
                print(f"    [WARN] EP {ep_no} 9router HTTP {r.status_code}: {r.text[:100]}")
        except Exception as e:
            print(f"    [WARN] EP {ep_no} 9router error (attempt {attempt}/3): {e}")
        time.sleep(3)
    return None

# ─── EPISODE PROCESSING ────────────────────────────────────────────────────
def process_episode_subtitle(ep, r2, total_eps):
    ep_no = ep['episodeNumber']
    ep_id = ep['id']
    video_url = ep.get('videoUrl540p') or ep.get('videoUrl')

    r2_key = f'dramas/{DRAMA_SLUG}/ep{ep_no:03d}.vtt'
    vtt_url = f'{R2_PUBLIC}/{r2_key}'

    # 1. Check if subtitle is already registered in DB
    try:
        sub_check = requests.get(f'{API_BASE}/api/episodes/{ep_id}/subtitles', timeout=10)
        if sub_check.ok:
            existing_subs = sub_check.json().get('subtitles', [])
            if any(s.get('language') == 'id' for s in existing_subs):
                return ep_no, True, 'already in DB'
    except Exception:
        pass

    # 2. Check if already in R2
    in_r2 = False
    try:
        r2.head_object(Bucket=R2_BUCKET, Key=r2_key)
        in_r2 = True
    except Exception:
        pass

    # 3. If not in R2, extract audio and generate VTT
    if not in_r2:
        temp_audio = os.path.join(TEMP_DIR, f'{DRAMA_SLUG}_ep{ep_no:03d}_audio.mp3')
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
            return ep_no, False, 'audio extract failed'

        vtt_content = generate_vtt_from_audio(temp_audio, ep_no)

        if os.path.exists(temp_audio):
            try: os.remove(temp_audio)
            except: pass

        if not vtt_content:
            return ep_no, False, 'vtt generation failed'

        # Upload to R2
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

# ─── MAIN ───────────────────────────────────────────────────────────────────
def main():
    print("=" * 65)
    print("🌐 GENERATING INDONESIAN SUBTITLES: Rahasia Bos Mafia")
    print(f"   Drama ID : {DRAMA_ID_DB}")
    print(f"   Model    : ag/gemini-3.8-flash-low via 9Router")
    print(f"   Storage  : Cloudflare R2 ({R2_BUCKET})")
    print("=" * 65)

    r2 = get_r2()

    # Fetch episodes
    r = requests.get(f'{API_BASE}/api/dramas/{DRAMA_ID_DB}/episodes', timeout=15)
    if not r.ok:
        print(f"[ERROR] Failed to fetch episodes: {r.status_code}")
        return

    episodes = r.json()
    episodes.sort(key=lambda x: x['episodeNumber'])
    total_eps = len(episodes)
    print(f"\nTotal episodes to check: {total_eps}")

    start_time = time.time()
    success_count = 0
    fail_count = 0

    # Process with 3 parallel workers
    with ThreadPoolExecutor(max_workers=3) as executor:
        future_map = {
            executor.submit(process_episode_subtitle, ep, r2, total_eps): ep
            for ep in episodes
        }

        for future in as_completed(future_map):
            ep_no, ok, msg = future.result()
            if ok:
                success_count += 1
                elapsed = time.time() - start_time
                eta_min = ((elapsed / max(success_count, 1)) * (total_eps - success_count)) / 60
                print(f"  [EP {ep_no:02d}/{total_eps}] OK ({msg}) | Progress: {success_count}/{total_eps} | ETA: {eta_min:.1f} min")
            else:
                fail_count += 1
                print(f"  [EP {ep_no:02d}/{total_eps}] FAILED: {msg} | Progress: {success_count}/{total_eps}")

    elapsed = time.time() - start_time
    print("\n" + "=" * 65)
    print("🏁 SUBTITLE GENERATION COMPLETE!")
    print(f"   Total Episodes : {total_eps}")
    print(f"   Success        : {success_count}/{total_eps}")
    print(f"   Failed         : {fail_count}/{total_eps}")
    print(f"   Duration       : {elapsed/60:.1f} minutes")
    print("=" * 65)

if __name__ == '__main__':
    main()
