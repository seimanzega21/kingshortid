#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
KingShort - Netshort V2 Queue Auto-Scraper
Membaca scripts/netshortv2_queue.json, memproses episode, mengunggah ke R2,
mendaftarkan ke database KingShort, dan menyimpan backup video lokal 720p.
"""
import sys
if sys.platform == 'win32':
    sys.stdout.reconfigure(encoding='utf-8', errors='replace')
    sys.stderr.reconfigure(encoding='utf-8', errors='replace')

import requests, boto3, subprocess, time, tempfile, urllib3, re, os, shutil, json
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

VIDRAMA_API = 'https://vidrama.asia/api/netshortv2'

WEB_HDRS    = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/147.0.0.0 Safari/537.36',
    'Referer': 'https://vidrama.asia/',
}

QUEUE_PATH  = Path(__file__).parent / 'netshortv2_queue.json'
TEMP_DIR    = Path(tempfile.gettempdir()) / 'ns2_queue_scraper'
TEMP_DIR.mkdir(exist_ok=True)

FFMPEG_BIN = r'C:\ProgramData\chocolatey\bin\ffmpeg.exe'
if not os.path.exists(FFMPEG_BIN):
    FFMPEG_BIN = shutil.which('ffmpeg') or 'ffmpeg'

# ── Helpers ──────────────────────────────────────────────────────────────────
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

def check_duplicate_in_db(title):
    try:
        r = requests.get(f"{API_BASE}/dramas/search?q={title}", timeout=10)
        dramas = r.json().get('dramas', [])
        for d in dramas:
            if d['title'].lower().strip() == title.lower().strip():
                return d['id']
    except: pass
    return None

def get_episode_url(drama_id, ep_no, retries=3):
    url = f"{VIDRAMA_API}/episode/{drama_id}/{ep_no}?lang=id_ID"
    for attempt in range(retries):
        try:
            r = requests.get(url, headers=WEB_HDRS, timeout=15, verify=False)
            data = r.json()
            if data.get('code') == 200:
                videos = data['data'].get('videos', [])
                subs = data['data'].get('subtitles', [])
                id_sub = next((s['url'] for s in subs if s.get('language') == 'id_ID'), None)
                if not id_sub and subs: id_sub = subs[0]['url']

                video_urls = []
                for q in ['720p', '1080p', '540p']:
                    for v in videos:
                        if v.get('quality') == q and v['url'] not in video_urls:
                            video_urls.append(v['url'])

                for v in videos:
                    if v['url'] not in video_urls:
                        video_urls.append(v['url'])

                return video_urls, id_sub
        except: time.sleep(2)
    return [], None

def api_get_or_create_drama(detail, slug, cover_url):
    title = detail.get('title', 'Unknown Title')
    payload = {
        'title': title,
        'description': detail.get('description', title),
        'cover': cover_url,
        'genres': detail.get('labels', ['Drama']) or ['Drama'],
        'totalEpisodes': detail.get('totalEpisodes', 0),
        'isComplete': detail.get('isFinished', False),
        'country': 'China', 'language': 'Indonesia',
        'status': 'completed' if detail.get('isFinished') else 'ongoing',
        'isActive': False, # Pending review di admin panel
    }
    r = requests.post(f"{API_BASE}/admin/dramas", headers=ADMIN_HDR, json=payload, timeout=20)
    return r.json().get('id') if r.ok else None

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

def load_queue():
    if not QUEUE_PATH.exists():
        return []
    try:
        with open(QUEUE_PATH, 'r', encoding='utf-8') as f:
            return json.load(f)
    except:
        return []

def save_queue(queue):
    try:
        with open(QUEUE_PATH, 'w', encoding='utf-8') as f:
            json.dump(queue, f, indent=2, ensure_ascii=False)
    except: pass

def scrape_single_drama(r2, vidrama_id, slug, provided_title=None):
    TEMP_DIR.mkdir(parents=True, exist_ok=True)
    prefix = f"netshortv2/{slug}"
    detail_url = f"{VIDRAMA_API}/detail/{vidrama_id}?lang=id_ID"
    print(f"[*] Mengambil detail metadata: {vidrama_id}")
    detail_r = requests.get(detail_url, headers=WEB_HDRS, timeout=15, verify=False)

    if not detail_r.ok or detail_r.json().get('code') != 200:
        print(f"[ERROR] Gagal mengambil metadata ID {vidrama_id}")
        return False

    detail = detail_r.json()['data']
    title = detail.get('title', provided_title or slug)
    total_eps = detail.get('totalEpisodes', 0)

    print(f"[+] Judul: {title}")
    print(f"[+] Total Episode: {total_eps}")

    local_save_dir = Path("D:/Video Drama/Facebook") / title.replace(":", " ").replace("/", " ")
    local_save_dir.mkdir(parents=True, exist_ok=True)

    cover_key = f"{prefix}/cover.webp"
    r2_cover_url = f"{R2_PUBLIC}/{cover_key}"

    db_id = check_duplicate_in_db(title)
    if db_id:
        print(f"[INFO] Drama '{title}' sudah ada di DB (ID: {db_id})")
    else:
        db_id = api_get_or_create_drama(detail, slug, r2_cover_url)
        if not db_id:
            print("[ERROR] Gagal membuat drama di database KingShort")
            return False
        print(f"[DB] Terdaftar ID: {db_id} (Pending Review)")

    # Cover
    if not r2_exists(r2, cover_key):
        try:
            cov = requests.get(detail['cover'], headers=WEB_HDRS, timeout=30, verify=False)
            p = TEMP_DIR / f"{slug}_cov"
            p.write_bytes(cov.content)
            r2_upload(r2, p, cover_key, 'image/webp')
            p.unlink()
            print("[COVER] Upload berhasil")
        except Exception as e:
            print(f"[WARN] Cover gagal: {e}")

    skipped = success = failed = 0
    for ep_no in range(1, total_eps + 1):
        k720 = f"{prefix}/ep{ep_no:03d}.mp4"
        k540 = f"{prefix}/ep{ep_no:03d}_540p.mp4"
        ksub = f"{prefix}/ep{ep_no:03d}.vtt"
        local_file = local_save_dir / f"ep{ep_no:03d}.mp4"

        if r2_exists(r2, k720):
            print(f"  ep{ep_no:03d}: SUDAH ADA di R2, skip download...", flush=True)
            u720 = f"{R2_PUBLIC}/{k720}"
            u540 = f"{R2_PUBLIC}/{k540}" if r2_exists(r2, k540) else None
            sub_url = f"{R2_PUBLIC}/{ksub}" if r2_exists(r2, ksub) else None
            api_upsert_episode(db_id, ep_no, u720, u540, sub_url)

            if not local_file.exists():
                try:
                    r_dl = requests.get(u720, stream=True, timeout=60)
                    if r_dl.ok:
                        with open(local_file, 'wb') as f:
                            for chunk in r_dl.iter_content(1024*1024):
                                if chunk: f.write(chunk)
                except: pass
            success += 1
            continue

        print(f"  ep{ep_no:03d}: Mencari stream URL...", end="", flush=True)
        vurls, sub_url_raw = get_episode_url(vidrama_id, ep_no)
        if not vurls:
            print(" [WARN] URL stream kosong!")
            skipped += 1
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
            TEMP_DIR.mkdir(parents=True, exist_ok=True)
            for vurl in vurls:
                if download_success: break
                for dl_attempt in range(2):
                    cdn_hdrs = {
                        'User-Agent': WEB_HDRS['User-Agent'],
                        'Referer': 'https://vidrama.asia/',
                        'Accept': '*/*'
                    }
                    try:
                        with requests.get(vurl, stream=True, headers=cdn_hdrs, verify=False, timeout=60) as r:
                            if r.status_code == 200:
                                with open(raw, 'wb') as f:
                                    for c in r.iter_content(2*1024*1024):
                                        if c: f.write(c)
                                size_kb = raw.stat().st_size / 1024 if raw.exists() else 0
                                if size_kb > 50:
                                    download_success = True
                                    break
                            elif r.status_code == 403:
                                curl_cmd = [
                                    "curl", "-s", "-L",
                                    "-H", f"User-Agent: {cdn_hdrs['User-Agent']}",
                                    "-H", f"Referer: {cdn_hdrs['Referer']}",
                                    "-o", str(raw),
                                    vurl
                                ]
                                subprocess.run(curl_cmd, timeout=60)
                                size_kb = raw.stat().st_size / 1024 if raw.exists() else 0
                                if size_kb > 50:
                                    download_success = True
                                    break
                    except Exception as err:
                        print(f" [EXC: {err}]", end="", flush=True)
                    time.sleep(1)

            if not download_success:
                print(" [ERROR] Gagal download dari CDN!")
                failed += 1
                continue

            print(" Mengompres ffmpeg (720p & 540p)...", end="", flush=True)
            if encode_720_and_540(raw, o720, o540):
                u720 = r2_upload(r2, o720, k720)
                u540 = r2_upload(r2, o540, k540) if o540.exists() else None
                api_upsert_episode(db_id, ep_no, u720, u540, final_sub_r2)

                try:
                    shutil.copy2(o720, local_file)
                except: pass

                print(" SUKSES")
                success += 1
            else:
                print(" [ERROR] Gagal ffmpeg!")
                failed += 1

        except Exception as e:
            print(f" [ERROR] {e}")
            failed += 1
        finally:
            for p in [raw, o720, o540]:
                if p.exists():
                    try: p.unlink()
                    except: pass

    print(f"\n[DONE] {title}: Sukses {success}/{total_eps} (Gagal: {failed}, Skip: {skipped})")
    return success > 0 and failed == 0

def run_queue():
    r2 = get_r2()
    print("="*60)
    print("🚀 MEMULAI SEDOT 10 DRAMA TERBARU NETSHORT V2")
    print("="*60)

    while True:
        queue = load_queue()
        pending_items = [it for it in queue if it.get('status') in ['pending', 'processing']]
        if not pending_items:
            print("\n🎉 SELURUH ANTRIAN 10 DRAMA TELAH SELESAI DIPROSES!")
            break

        current = pending_items[0]
        vid_id = current['id']
        title = current['title']
        slug = current['slug']

        print(f"\n{'='*60}")
        print(f"[*] MEMPROSES ({title}) [ID: {vid_id}]")
        print(f"{'='*60}")

        current['status'] = 'processing'
        save_queue(queue)

        success = False
        try:
            success = scrape_single_drama(r2, vid_id, slug, provided_title=title)
        except Exception as e:
            print(f"[ERROR EXCEPTION] {e}")

        # Update status
        queue = load_queue()
        for it in queue:
            if it['id'] == vid_id:
                it['status'] = 'done' if success else 'failed'
        save_queue(queue)

if __name__ == '__main__':
    run_queue()
