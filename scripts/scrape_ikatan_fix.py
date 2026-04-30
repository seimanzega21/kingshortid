import sys
import requests
import boto3
import subprocess
import time
import json
import tempfile
import urllib3
import re
from pathlib import Path
from botocore.config import Config

urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

# ── Config ──────────────────────────────────────────────────────────────────
API_BASE    = 'https://api.shortlovers.id'
ADMIN_KEY   = '00ca04e3e2702be565d7bf44e783255247708289bce9b2fb6187a2e117f87fd14'
ADMIN_HDR   = {'x-admin-key': ADMIN_KEY, 'Content-Type': 'application/json'}

R2_ENDPOINT = 'https://a142d3b29a5d64943cb251157e25eaf3.r2.cloudflarestorage.com'
R2_KEY_ID   = '07c99c897986ea52703c1285308d5e2c'
R2_SECRET   = '44788d376ffb216e1e73784b6fe1ff1423607928898a87c50819b52cdfc12e44'
R2_BUCKET   = 'shortlovers'
R2_PUBLIC   = 'https://stream.shortlovers.id'

VIDRAMA_API = 'https://vidrama.asia/api/netshortv2'
# ── Load Cookies ─────────────────────────────────────────────────────────────
COOKIES_FILE = Path('d:/kingshortid/scripts/vidrama_cookies_final.txt')
if COOKIES_FILE.exists():
    with open(COOKIES_FILE, 'r', encoding='utf-8') as f:
        VIDRAMA_COOKIE = f.read().strip()
else:
    VIDRAMA_COOKIE = "_fbp=fb.1.1770653154777.876935444165455244; _tt_enable_cookie=1; _ttp=01KH1JE0K4H648BY6E3FQ6EXRZ_.tt.1; _ga=GA1.1.1826262121.1771037718; HstCfa5004644=1772873251576; c_ref_5004644=https%3A%2F%2Fwww.google.com%2F; __dtsu=4C301774685394D291D3AB624E4AA57E; _pubcid=8a5abbf9-164b-422f-b349-0e1ba702ea69; _cc_id=a4a99f9a552125d19ea447bfafb9c63b; HstCmu5004644=1776164034743; HstPn5004644=1; cf_clearance=AQRjv4.Cj2nHbg_KLivmkViGOllnwGPpIVkj35_jfKI-1777471778-1.2.1.1-TEdhFr7wBXOwe6l8ybhNx3V3OAO2FmEP81fCwLc_mclcsLHuLye6b0vcwrShIGHIdgmlaY14VoOLGlccyUA11WHrRIEncihkGDwdc8C44c79F_3U4SEVsPeQAtPP.1_v6j.daxeE5gMBUPycNwj8rIn4fxg5dhhxrCsZvPIyDKo0BUWtkSEcjfRXcll7MrK8y3YSM8WhGmqI.PzKcfsFF.006ENmy7BGlLwqjy_QDYg8Y7xuxVKlIr_3ApmsnXItGKvJ2DDt_XQUqh1H5hqKnf50BS4QFNfxQEUeytk94ofP8SYQwlqg1HEIz3BMlJC4OQhzn5m0L6muYtASD.jwaw; HstCla5004644=1777471778959; HstPt5004644=72; HstCnv5004644=31; HstCns5004644=35; panoramaId_expiry=1777558180696; _ga_HCQQPKGEVH=GS2.1.s1777476684$o70$g1$t1777477281$j55$l0$h0; ttcsid_D5SNQPRC77UDQTF8A5EG=1777476683162::JiaNdPsba2GCy8oVLuyE.75.1777477294114.1; ttcsid=1777476683155::c9Pa9Oee_DaSEml_Mj5I.85.1777477294114.0::1.610918.6485::610880.63.113.1122::610008.512.600"

WEB_HDRS    = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36',
    'Referer': 'https://vidrama.asia/',
    'Cookie': VIDRAMA_COOKIE
}

TEMP_DIR = Path(tempfile.gettempdir()) / 'ikatan_scraper'
TEMP_DIR.mkdir(exist_ok=True)

# ── Drama Info ─────────────────────────────────────────────────────────────
DRAMA_TITLE = "Ikatan Cantik, Kekuatan Abadi"
DRAMA_ID    = "2021413378848690178"
DRAMA_SLUG  = "ikatan-cantik-kekuatan-abadi"
KING_DB_ID  = "l3xutuuntoqmq71cof1c0rze"
PREFIX      = f"netshortv2/{DRAMA_SLUG}"

# ── R2 ────────────────────────────────────────────────────────────────────────
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

# ── Vidrama API ───────────────────────────────────────────────────────────────
def get_drama_detail(drama_id):
    url = f"{VIDRAMA_API}/detail/{drama_id}?lang=id_ID"
    r = requests.get(url, headers=WEB_HDRS, timeout=15, verify=False)
    return r.json()['data']

def get_episode_url(drama_id, ep_no, retries=3):
    url = f"{VIDRAMA_API}/episode/{drama_id}/{ep_no}?lang=id_ID"
    for attempt in range(retries):
        try:
            r = requests.get(url, headers=WEB_HDRS, timeout=15, verify=False)
            data = r.json()
            if data.get('code') == 200:
                videos = data['data'].get('videos', [])
                # Extract Subtitles
                subs = data['data'].get('subtitles', [])
                id_sub = next((s['url'] for s in subs if s.get('language') == 'id_ID'), None)
                if not id_sub and subs: id_sub = subs[0]['url'] 
                
                best_video = None
                for q in ['720p', '1080p', '540p']:
                    for v in videos:
                        if v.get('quality') == q: 
                            best_video = v['url']
                            break
                    if best_video: break
                
                if not best_video and videos: best_video = videos[0]['url']
                return best_video, id_sub
        except: time.sleep(2)
    return None, None

# ── Backend API ───────────────────────────────────────────────────────────────
def api_upsert_episode(drama_db_id, ep_no, url_720, url_540=None, sub_url=None):
    payload = {'episodeNumber': ep_no, 'title': f'Episode {ep_no}', 'videoUrl': url_720, 'isActive': True}
    if url_540: payload['videoUrl540p'] = url_540
    r = requests.post(f"{API_BASE}/api/admin/dramas/{drama_db_id}/episodes", headers=ADMIN_HDR, json=payload, timeout=20)
    if not r.ok: 
        print(f"      [DB ERROR] {r.status_code} {r.text}")
        return None
    
    ep_id = r.json().get('id')
    if ep_id and sub_url:
        sub_payload = {'language': 'indonesia', 'label': 'Indonesia', 'url': sub_url, 'isDefault': True}
        requests.post(f"{API_BASE}/api/episodes/{ep_id}/subtitles", headers=ADMIN_HDR, json=sub_payload, timeout=10)
    time.sleep(2)
    return ep_id

def api_update_total_episodes(drama_db_id, total):
    payload = {'totalEpisodes': total}
    r = requests.patch(f"{API_BASE}/api/admin/dramas/{drama_db_id}", headers=ADMIN_HDR, json=payload, timeout=20)
    time.sleep(2)
    return r.ok

# ── Processing ───────────────────────────────────────────────────────────────
def encode_720_and_540(inp, out_720, out_540):
    cmd = ['ffmpeg', '-y', '-i', str(inp), '-c:v', 'libx264', '-crf', '26', '-maxrate', '1500k', '-bufsize', '3000k',
           '-c:a', 'aac', '-b:a', '128k', '-movflags', '+faststart', '-loglevel', 'error', str(out_720)]
    res = subprocess.run(cmd, timeout=600)
    if res.returncode != 0: return False
    cmd3 = ['ffmpeg', '-y', '-i', str(out_720), '-vf', 'scale=-2:540', '-c:v', 'libx264', '-crf', '28', '-preset', 'fast',
            '-c:a', 'aac', '-b:a', '96k', '-movflags', '+faststart', '-loglevel', 'error', str(out_540)]
    return subprocess.run(cmd3, timeout=600).returncode == 0

def main():
    print(f"[START] Scraping {DRAMA_TITLE} ({DRAMA_ID})")
    r2 = get_r2()
    
    detail = get_drama_detail(DRAMA_ID)
    total_vidrama = detail['totalEpisodes']
    print(f"[INFO] Vidrama total episodes: {total_vidrama}")
    
    # Update total episodes in DB
    if api_update_total_episodes(KING_DB_ID, total_vidrama):
        print(f"[DB] Updated total episodes to {total_vidrama}")
    
    episodes = detail.get('episodes', [])
    
    # Ensure Drama is ACTIVE
    requests.patch(f"{API_BASE}/api/admin/dramas/{KING_DB_ID}", headers=ADMIN_HDR, json={'isActive': True}, timeout=10)
    print(f"[DB] Drama {KING_DB_ID} is ACTIVE")

    for ep in episodes:
        no = ep['episodeNo']
        if no < 47: continue # Episodes 1-46 are already handled (except 32)
        
        print(f"\n--- Episode {no} ---")
        k720, k540 = f"{PREFIX}/ep{no:03d}.mp4", f"{PREFIX}/ep{no:03d}_540p.mp4"
        
        # Check R2
        if r2_exists(r2, k720) and r2_exists(r2, k540):
            print(f"  ALREADY in R2, syncing to DB...")
            # Still need subtitle check
            _, v_sub_url = get_episode_url(DRAMA_ID, no)
            final_sub_r2 = None
            if v_sub_url:
                sub_key = f"{PREFIX}/ep{no:03d}.vtt"
                if not r2_exists(r2, sub_key):
                    try:
                        sub_r = requests.get(v_sub_url, timeout=10, verify=False)
                        if sub_r.ok:
                            r2.put_object(Bucket=R2_BUCKET, Key=sub_key, Body=sub_r.content, ContentType='text/vtt')
                            final_sub_r2 = f"{R2_PUBLIC}/{sub_key}"
                    except: pass
                else:
                    final_sub_r2 = f"{R2_PUBLIC}/{sub_key}"
            
            api_upsert_episode(KING_DB_ID, no, f"{R2_PUBLIC}/{k720}", f"{R2_PUBLIC}/{k540}", final_sub_r2)
            continue
            
        # Process new
        print(f"  Fetching URL...")
        vurl, v_sub_url = get_episode_url(DRAMA_ID, no)
        if not vurl:
            print(f"  [ERROR] No video URL found!")
            continue
            
        final_sub_r2 = None
        if v_sub_url:
            sub_key = f"{PREFIX}/ep{no:03d}.vtt"
            try:
                sub_r = requests.get(v_sub_url, timeout=10, verify=False)
                if sub_r.ok:
                    r2.put_object(Bucket=R2_BUCKET, Key=sub_key, Body=sub_r.content, ContentType='text/vtt')
                    final_sub_r2 = f"{R2_PUBLIC}/{sub_key}"
            except: pass

        raw, o720, o540 = TEMP_DIR/f"raw.mp4", TEMP_DIR/f"720.mp4", TEMP_DIR/f"540.mp4"
        try:
            print(f"  Downloading...")
            with requests.get(vurl, stream=True, headers=WEB_HDRS, verify=False, timeout=60) as r:
                if not r.ok:
                    print(f"  [ERROR] Download failed: {r.status_code} {r.reason}")
                    if r.status_code == 403:
                        print("  [TIP] 403 Forbidden! Cookie might be invalid or IP blocked.")
                    continue
                
                with open(raw, 'wb') as f:
                    for c in r.iter_content(4*1024*1024): 
                        if c: f.write(c)
            
            # Check if file exists and has size
            if not raw.exists() or raw.stat().st_size < 1000:
                print(f"  [ERROR] Downloaded file is too small or missing!")
                continue

            print(f"  Encoding...")
            if encode_720_and_540(raw, o720, o540):
                print(f"  Uploading...")
                u720 = r2_upload(r2, o720, k720)
                u540 = r2_upload(r2, o540, k540)
                
                print(f"  Syncing to DB...")
                api_upsert_episode(KING_DB_ID, no, u720, u540, final_sub_r2)
                print(f"  DONE.")
            else:
                print(f"  [ERROR] Ffmpeg failed!")
        except Exception as e:
            print(f"  [ERROR] {e}")

        finally:
            for p in [raw, o720, o540]:
                if p.exists():
                    for _ in range(5):
                        try:
                            p.unlink()
                            break
                        except:
                            time.sleep(1)

    print("\n[FINISH]")

if __name__ == "__main__":
    main()
