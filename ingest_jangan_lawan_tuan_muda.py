# -*- coding: utf-8 -*-
"""
Ingest & Subtitle Pipeline: Jangan Lawan Tuan Muda (StardustTV, ID: 23995)
- 60 episodes
- Source: https://vidrama.asia/watch/jangan-lawan-tuan-muda--23995/1?provider=stardusttv
- 720p stream copy + 540p transcode -> Cloudflare R2
- Indonesian WebVTT subtitle generation via 9Router (Gemini 3.8 Flash) -> Cloudflare R2
- Upsert episodes & subtitles to KingShort DB
- Activate drama on completion
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
import re
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

DRAMA_ID_STARDUST = '23995'
DRAMA_SLUG        = 'jangan-lawan-tuan-muda'
GENRES            = ['Drama', 'Reinkarnasi', 'Balas Dendam', 'Aksi', 'Eksklusif']

ROUTER_URL  = 'http://localhost:20128/v1/chat/completions'
ROUTER_KEY  = 'sk-6c5720214189ea51-otb97y-5446d478'
ROUTER_HDR  = {'Authorization': f'Bearer {ROUTER_KEY}', 'Content-Type': 'application/json'}

TEMP_DIR    = 'D:/kingshortid/temp_stardust'
os.makedirs(TEMP_DIR, exist_ok=True)

FFMPEG_HEADERS = (
    "User-Agent: Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
    "(KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36\r\n"
    "Referer: https://vidrama.asia/\r\n"
)

SYSTEM_PROMPT = """You are an automated subtitle generator for streaming dramas.
Translate spoken dialogue (English, etc.) directly into natural, fluent, and dramatic Indonesian (Bahasa Indonesia).
You MUST output ONLY valid WebVTT format (.vtt).
DO NOT write any preamble, intro, notes, explanations, or markdown code blocks. Start strictly with 'WEBVTT' on line 1.

Example format:
WEBVTT

00:00:04.200 --> 00:00:07.500
Teks terjemahan bahasa Indonesia di sini.

00:00:08.100 --> 00:00:12.300
Baris percakapan berikutnya.
"""

# ─── R2 CLIENT ─────────────────────────────────────────────────────────────
def get_r2():
    return boto3.client(
        's3', endpoint_url=R2_ENDPOINT,
        aws_access_key_id=R2_KEY_ID, aws_secret_access_key=R2_SECRET,
        config=Config(signature_version='s3v4'), region_name='auto'
    )

# ─── METADATA ──────────────────────────────────────────────────────────────
def fetch_drama_details():
    url = f'https://vidrama.asia/api/stardusttv?action=detail&id={DRAMA_ID_STARDUST}&lang=id'
    headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'}
    for attempt in range(1, 4):
        try:
            r = requests.get(url, headers=headers, timeout=20)
            if r.ok:
                data = r.json()
                if data.get('success') and data.get('data'):
                    return data['data']
            print(f"  [WARN] Detail HTTP {r.status_code} (attempt {attempt}/3)")
        except Exception as e:
            print(f"  [WARN] Detail error (attempt {attempt}/3): {e}")
        time.sleep(3)
    return None

def fetch_episode_url_fallback(ep_no):
    url = f'https://vidrama.asia/api/stardusttv?action=episode&id={DRAMA_ID_STARDUST}&episode={ep_no}&lang=id'
    headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'}
    try:
        r = requests.get(url, headers=headers, timeout=20)
        if r.ok:
            data = r.json()
            if data.get('success') and data.get('data'):
                ep_data = data['data']
                return ep_data.get('videoUrl') or ep_data.get('url') or ep_data.get('fallbackUrl')
    except Exception as e:
        print(f"    [WARN] Fallback EP {ep_no} error: {e}")
    return None

# ─── COVER PROCESSING ──────────────────────────────────────────────────────
def upload_cover(r2, cover_url):
    r2_key = f'dramas/{DRAMA_SLUG}/cover_hq.jpg'
    try:
        r2.head_object(Bucket=R2_BUCKET, Key=r2_key)
        url = f'{R2_PUBLIC}/{r2_key}'
        print(f"  [OK] Cover already in R2: {url}")
        return url
    except Exception:
        pass

    print("  Downloading & converting cover...")
    raw_path = os.path.join(TEMP_DIR, f'{DRAMA_SLUG}_cover_raw')
    clean_path = os.path.join(TEMP_DIR, f'{DRAMA_SLUG}_cover_clean.jpg')
    try:
        r = requests.get(cover_url, timeout=30, verify=False)
        r.raise_for_status()
        with open(raw_path, 'wb') as f:
            f.write(r.content)

        result = subprocess.run(
            ['ffmpeg', '-y', '-i', raw_path, '-update', '1', '-q:v', '2', clean_path],
            capture_output=True, timeout=60
        )
        upload_path = clean_path if (result.returncode == 0 and os.path.exists(clean_path)) else raw_path
        with open(upload_path, 'rb') as f:
            r2.upload_fileobj(
                f, R2_BUCKET, r2_key,
                ExtraArgs={'ContentType': 'image/jpeg', 'CacheControl': 'public, max-age=31536000'}
            )
        url = f'{R2_PUBLIC}/{r2_key}'
        print(f"  [OK] Cover uploaded: {url}")
        for p in [raw_path, clean_path]:
            if os.path.exists(p):
                try: os.remove(p)
                except: pass
        return url
    except Exception as e:
        print(f"  [ERROR] Cover upload failed: {e}")
        return cover_url

# ─── DRAMA REGISTRATION ────────────────────────────────────────────────────
def register_drama(metadata, cover_r2_url):
    title = metadata.get('title', 'Jangan Lawan Tuan Muda')
    r = requests.get(f'{API_BASE}/api/dramas/search', params={'q': title}, timeout=15)
    if r.ok:
        dramas_list = r.json().get('dramas', [])
        for d in dramas_list:
            if title.lower() in d.get('title', '').lower():
                print(f"  [OK] Drama already in DB: {d['id']} ({d['title']})")
                return d['id']

    payload = {
        'title': title,
        'description': metadata.get('description') or metadata.get('introduction') or '',
        'cover': cover_r2_url,
        'genres': GENRES,
        'totalEpisodes': len(metadata.get('list', [])),
        'status': 'completed',
        'country': 'China',
        'language': 'Indonesia',
        'isActive': False,
        'isVip': False,
    }
    r = requests.post(f'{API_BASE}/api/admin/dramas', headers=ADMIN_HDR, json=payload, timeout=30)
    if r.ok:
        resp = r.json()
        drama_id = resp.get('id') or resp.get('drama', {}).get('id')
        print(f"  [OK] Drama registered! ID: {drama_id}")
        return drama_id
    else:
        print(f"  [ERROR] Drama registration failed: {r.status_code} {r.text[:300]}")
        return None

# ─── SUBTITLE GENERATION ───────────────────────────────────────────────────
def clean_vtt_text(raw_text):
    text = raw_text.strip()
    if '```' in text:
        text = text.replace('```vtt', '').replace('```', '')
    match = re.search(r'\d{1,2}:\d{2}:\d{2}\.\d{3}\s*-->', text)
    if match:
        cues_part = text[match.start():]
        return 'WEBVTT\n\n' + cues_part.strip() + '\n'
    idx = text.rfind('WEBVTT')
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
                raw_vtt = r.json()['choices'][0]['message']['content']
                return clean_vtt_text(raw_vtt)
            else:
                print(f"    [WARN] EP {ep_no} 9router HTTP {r.status_code}")
        except Exception as e:
            print(f"    [WARN] EP {ep_no} 9router error (attempt {attempt}/3): {e}")
        time.sleep(3)
    return None

# ─── EPISODE PIPELINE (VIDEO + SUBTITLE) ────────────────────────────────────
def process_single_episode(ep, drama_id, drama_title, r2, total_eps):
    ep_no = int(ep.get('episodeNumber') or ep.get('episodeNo', 0))
    m3u8_url = ep.get('h264') or ep.get('videoUrl') or ep.get('videoPath', '')

    if not ep_no or not m3u8_url:
        return ep_no, False, 'missing url'

    r2_key_720 = f'dramas/{DRAMA_SLUG}/ep{ep_no:03d}_720p.mp4'
    r2_key_540 = f'dramas/{DRAMA_SLUG}/ep{ep_no:03d}_540p.mp4'
    r2_key_vtt = f'dramas/{DRAMA_SLUG}/ep{ep_no:03d}.vtt'

    url_720 = None
    url_540 = None
    url_vtt = f'{R2_PUBLIC}/{r2_key_vtt}'

    # Check R2 for 720p and 540p
    try:
        r2.head_object(Bucket=R2_BUCKET, Key=r2_key_720)
        url_720 = f'{R2_PUBLIC}/{r2_key_720}'
    except Exception: pass

    try:
        r2.head_object(Bucket=R2_BUCKET, Key=r2_key_540)
        url_540 = f'{R2_PUBLIC}/{r2_key_540}'
    except Exception: pass

    vtt_in_r2 = False
    try:
        r2.head_object(Bucket=R2_BUCKET, Key=r2_key_vtt)
        vtt_in_r2 = True
    except Exception: pass

    local_720 = os.path.join(TEMP_DIR, f'{DRAMA_SLUG}_ep{ep_no:03d}_720p.mp4')
    local_540 = os.path.join(TEMP_DIR, f'{DRAMA_SLUG}_ep{ep_no:03d}_540p.mp4')
    temp_audio = os.path.join(TEMP_DIR, f'{DRAMA_SLUG}_ep{ep_no:03d}_audio.mp3')

    # Step 1: Download & Transcode Video if not in R2
    if not url_720:
        for f in [local_720, local_540]:
            if os.path.exists(f):
                try: os.remove(f)
                except: pass

        # Download 720p stream copy
        success_720 = False
        urls_to_try = [m3u8_url]
        for attempt in range(1, 4):
            cur_url = urls_to_try[0]
            cmd = [
                'ffmpeg', '-y',
                '-headers', FFMPEG_HEADERS,
                '-i', cur_url,
                '-c', 'copy',
                '-movflags', '+faststart',
                '-loglevel', 'warning',
                local_720
            ]
            res = subprocess.run(cmd, capture_output=True, text=True, errors='ignore', timeout=600)
            if res.returncode == 0 and os.path.exists(local_720) and os.path.getsize(local_720) > 50000:
                success_720 = True
                break
            else:
                if attempt == 1:
                    fb = fetch_episode_url_fallback(ep_no)
                    if fb and fb != cur_url:
                        urls_to_try = [fb]
                time.sleep(4)

        if not success_720:
            return ep_no, False, '720p download failed'

        # Transcode 540p
        cmd_540 = [
            'ffmpeg', '-y',
            '-i', local_720,
            '-vf', 'scale=-2:540',
            '-c:v', 'libx264', '-crf', '26', '-preset', 'veryfast',
            '-maxrate', '1000k', '-bufsize', '2000k',
            '-c:a', 'aac', '-b:a', '96k',
            '-movflags', '+faststart',
            '-loglevel', 'warning',
            local_540
        ]
        subprocess.run(cmd_540, capture_output=True, text=True, errors='ignore', timeout=300)
        has_540 = os.path.exists(local_540) and os.path.getsize(local_540) > 50000

        # Upload 720p
        with open(local_720, 'rb') as f:
            r2.upload_fileobj(f, R2_BUCKET, r2_key_720, ExtraArgs={'ContentType': 'video/mp4', 'CacheControl': 'public, max-age=31536000'})
        url_720 = f'{R2_PUBLIC}/{r2_key_720}'

        # Upload 540p
        if has_540:
            with open(local_540, 'rb') as f:
                r2.upload_fileobj(f, R2_BUCKET, r2_key_540, ExtraArgs={'ContentType': 'video/mp4', 'CacheControl': 'public, max-age=31536000'})
            url_540 = f'{R2_PUBLIC}/{r2_key_540}'

    # Step 2: Register Episode in KingShort DB
    payload_ep = {
        'episodeNumber': ep_no,
        'title': f'Episode {ep_no}',
        'videoUrl': url_720 or url_540 or '',
        'videoUrl540p': url_540 or '',
        'isVip': False,
        'coinPrice': 0,
        'isActive': True,
    }
    ep_id = None
    for _ in range(3):
        try:
            r = requests.post(f'{API_BASE}/api/admin/dramas/{drama_id}/episodes', headers=ADMIN_HDR, json=payload_ep, timeout=25)
            if r.ok:
                ep_id = r.json().get('id')
                break
            r2_patch = requests.patch(f'{API_BASE}/api/admin/dramas/{drama_id}/episodes/{ep_no}', headers=ADMIN_HDR, json=payload_ep, timeout=25)
            if r2_patch.ok:
                ep_id = r2_patch.json().get('id')
                break
        except Exception:
            time.sleep(2)

    if not ep_id:
        # Try fetching episode ID from DB
        try:
            er = requests.get(f'{API_BASE}/api/dramas/{drama_id}/episodes', timeout=15)
            for item in er.json():
                if item.get('episodeNumber') == ep_no:
                    ep_id = item.get('id')
                    break
        except Exception: pass

    # Step 3: Subtitle Generation & Upload
    sub_registered = False
    if ep_id:
        # Check if already registered in DB
        try:
            sr = requests.get(f'{API_BASE}/api/episodes/{ep_id}/subtitles', timeout=10)
            if sr.ok and any(s.get('language') == 'id' for s in sr.json().get('subtitles', [])):
                sub_registered = True
        except Exception: pass

    if not sub_registered:
        if not vtt_in_r2:
            # Extract audio from local file if available, else from stream URL
            audio_source = local_540 if os.path.exists(local_540) else (local_720 if os.path.exists(local_720) else (url_540 or url_720 or m3u8_url))
            cmd_audio = ['ffmpeg', '-y', '-i', audio_source, '-vn', '-ac', '1', '-ar', '16000', '-b:a', '32k', '-loglevel', 'warning', temp_audio]
            subprocess.run(cmd_audio, capture_output=True, timeout=120)

            if os.path.exists(temp_audio):
                vtt_text = generate_vtt_from_audio(temp_audio, ep_no, drama_title)
                try: os.remove(temp_audio)
                except: pass

                if vtt_text:
                    r2.put_object(
                        Bucket=R2_BUCKET, Key=r2_key_vtt,
                        Body=vtt_text.encode('utf-8'),
                        ContentType='text/vtt; charset=utf-8',
                        CacheControl='public, max-age=31536000'
                    )
                    vtt_in_r2 = True

        # Register Subtitle in DB
        if ep_id and vtt_in_r2:
            sub_payload = {
                'language': 'id',
                'label': 'Indonesian',
                'url': url_vtt,
                'isDefault': True
            }
            for _ in range(3):
                try:
                    s_resp = requests.post(f'{API_BASE}/api/episodes/{ep_id}/subtitles', headers=ADMIN_HDR, json=sub_payload, timeout=20)
                    if s_resp.ok:
                        sub_registered = True
                        break
                except Exception:
                    time.sleep(2)

    # Cleanup local files
    for f in [local_720, local_540, temp_audio]:
        if os.path.exists(f):
            try: os.remove(f)
            except: pass

    return ep_no, True, f'ep:{ep_id} sub:{"OK" if sub_registered else "pending"}'

# ─── MAIN ───────────────────────────────────────────────────────────────────
def main():
    print("=" * 65)
    print("🎬 INGESTING & TRANSLATING: Jangan Lawan Tuan Muda (StardustTV)")
    print(f"   Stardust ID : {DRAMA_ID_STARDUST}")
    print(f"   Slug        : {DRAMA_SLUG}")
    print(f"   Temp Dir    : {TEMP_DIR}")
    print("=" * 65)

    r2 = get_r2()

    # 1. Fetch metadata
    print("\n[1/5] Fetching drama metadata...")
    metadata = fetch_drama_details()
    if not metadata:
        print("[ERROR] Failed to fetch metadata. Aborting.")
        return

    episodes = metadata.get('list', [])
    total_eps = len(episodes)
    drama_title = metadata.get('title', 'Jangan Lawan Tuan Muda')
    print(f"  Title   : {drama_title}")
    print(f"  Episodes: {total_eps}")

    # 2. Upload cover
    print("\n[2/5] Processing cover...")
    cover_url = metadata.get('cover') or metadata.get('poster') or metadata.get('image', '')
    cover_r2_url = upload_cover(r2, cover_url)

    # 3. Register drama
    print("\n[3/5] Registering drama in DB...")
    drama_id = register_drama(metadata, cover_r2_url)
    if not drama_id:
        print("[ERROR] Drama registration failed. Aborting.")
        return

    # 4. Check already done episodes (with subtitle)
    done_eps = set()
    try:
        er = requests.get(f'{API_BASE}/api/dramas/{drama_id}/episodes', timeout=15)
        if er.ok:
            for item in er.json():
                ep_num = int(item.get('episodeNumber', 0))
                # Check if subtitle exists
                sr = requests.get(f'{API_BASE}/api/episodes/{item["id"]}/subtitles', timeout=10)
                if sr.ok and any(s.get('language') == 'id' for s in sr.json().get('subtitles', [])):
                    done_eps.add(ep_num)
    except Exception as e:
        print(f"  [WARN] Check existing error: {e}")

    print(f"\n[4/5] Already fully done in DB: {len(done_eps)} / {total_eps} episodes")
    remaining = [ep for ep in episodes if int(ep.get('episodeNumber') or ep.get('episodeNo', 0)) not in done_eps]
    print(f"  Remaining to process: {len(remaining)} episodes")

    # 5. Process episodes with 2 parallel workers
    print(f"\n[5/5] Processing remaining episodes with 2 workers...\n")
    start_time = time.time()
    success_count = len(done_eps)
    fail_count = 0

    with ThreadPoolExecutor(max_workers=2) as executor:
        future_map = {
            executor.submit(process_single_episode, ep, drama_id, drama_title, r2, total_eps): ep
            for ep in remaining
        }

        for future in as_completed(future_map):
            ep_no, ok, msg = future.result()
            if ok:
                success_count += 1
                elapsed = time.time() - start_time
                done_now = success_count - len(done_eps)
                rem_now = len(remaining) - done_now
                eta_min = ((elapsed / max(done_now, 1)) * rem_now) / 60
                print(f"  [EP {ep_no:02d}/{total_eps}] DONE ({msg}) | Progress: {success_count}/{total_eps} | ETA: {eta_min:.1f} min")
            else:
                fail_count += 1
                print(f"  [EP {ep_no:02d}/{total_eps}] FAILED: {msg} | Progress: {success_count}/{total_eps}")

    # 6. Activate drama
    print(f"\n[6/6] Activating drama in DB...")
    r = requests.patch(
        f'{API_BASE}/api/admin/dramas/{drama_id}',
        headers=ADMIN_HDR,
        json={'isActive': True, 'totalEpisodes': success_count},
        timeout=20
    )
    if r.ok:
        print("  [OK] Drama activated successfully!")
    else:
        print(f"  [WARN] Activation response: {r.status_code} {r.text[:200]}")

    elapsed = time.time() - start_time
    print("\n" + "=" * 65)
    print("🏁 INGESTION & SUBTITLES FINISHED!")
    print(f"   Drama ID  : {drama_id}")
    print(f"   Success   : {success_count}/{total_eps} episodes")
    print(f"   Failed    : {fail_count}/{total_eps} episodes")
    print(f"   Duration  : {elapsed/60:.1f} minutes")
    print("=" * 65)

if __name__ == '__main__':
    main()
