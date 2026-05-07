import requests, boto3, subprocess, time, os, urllib3, re, json
from pathlib import Path
from botocore.config import Config

urllib3.disable_warnings()

# ── CONFIG ──────────────────────────────────────────────────────────────────
API_BASE    = 'https://api.shortlovers.id'
ADMIN_KEY   = '00ca04e3e2702be565d7bf44e783255247708289bce9b2fb6187a2e117f87fd14'
ADMIN_HDR   = {'x-admin-key': ADMIN_KEY, 'Content-Type': 'application/json'}

R2_ENDPOINT = 'https://a142d3b29a5d64943cb251157e25eaf3.r2.cloudflarestorage.com'
R2_KEY_ID   = '07c99c897986ea52703c1285308d5e2c'
R2_SECRET   = '44788d376ffb216e1e73784b6fe1ff1423607928898a87c50819b52cdfc12e44'
R2_BUCKET   = 'shortlovers'
R2_PUBLIC   = 'https://stream.shortlovers.id'

VIDRAMA_API = 'https://vidrama.asia/api/netshortv2'
WEB_HDRS = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
    'Referer': 'https://vidrama.asia/',
    'Cookie': '_fbp=fb.1.1770653154777.876935444165455244; _tt_enable_cookie=1; _ttp=01KH1JE0K4H648BY6E3FQ6EXRZ_.tt.1; _ga=GA1.1.1826262121.1771037718; HstCfa5004644=1772873251576; cf_clearance=AQRjv4.Cj2nHbg_KLivmkViGOllnwGPpIVkj35_jfKI-1777471778-1.2.1.1-TEdhFr7wBXOwe6l8ybhNx3V3OAO2FmEP81fCwLc_mclcsLHuLye6b0vcwrShIGHIdgmlaY14VoOLGlccyUA11WHrRIEncihkGDwdc8C44c79F_3U4SEVsPeQAtPP.1_v6j.daxeE5gMBUPycNwj8rIn4fxg5dhhxrCsZvPIyDKo0BUWtkSEcjfRXcll7MrK8y3YSM8WhGmqI.PzKcfsFF.006ENmy7BGlLwqjy_QDYg8Y7xuxVKlIr_3ApmsnXItGKvJ2DDt_XQUqh1H5hqKnf50BS4QFNfxQEUeytk94ofP8SYQwlqg1HEIz3BMlJC4OQhzn5m0L6muYtASD.jwaw; HstCla5004644=1777471778959; HstPt5004644=72; HstCnv5004644=31; HstCns5004644=35; ttcsid=1777476683155::c9Pa9Oee_DaSEml_Mj5I.85.1777477294114.0'
}

DRAMAS = [
    {"vidrama_id": "2050068409973997569", "db_id": "cmlyu7p1q0001uxfx7dt279tt", "slug": "raja-yang-ditakuti-musuh", "total": 82},
    {"vidrama_id": "2033798825713336321", "db_id": "cmlyu8p1r0002uxfx8dt279tt", "slug": "menghabisi-yang-jahat", "total": 91},
    {"vidrama_id": "2020778605549871106", "db_id": "cmlyu9p1s0003uxfx9dt279tt", "slug": "dua-kuasa-menjadi-satu", "total": 102}
]

TEMP_DIR = Path("D:/kingshortid/scripts/tmp/bulk_process")
TEMP_DIR.mkdir(parents=True, exist_ok=True)

def get_r2():
    return boto3.client('s3', endpoint_url=R2_ENDPOINT,
                        aws_access_key_id=R2_KEY_ID, aws_secret_access_key=R2_SECRET,
                        config=Config(signature_version='s3v4'), region_name='auto')

def r2_upload(r2, local_path, key, content_type='video/mp4'):
    r2.upload_file(str(local_path), R2_BUCKET, key, ExtraArgs={'ContentType': content_type})
    return f"{R2_PUBLIC}/{key}"

def get_ep_data(vidrama_id, ep_no):
    url = f"{VIDRAMA_API}/episode/{vidrama_id}/{ep_no}?lang=id_ID"
    try:
        r = requests.get(url, headers=WEB_HDRS, timeout=15, verify=False)
        if r.ok:
            data = r.json()
            if data.get('code') == 200: return data['data']
    except: pass
    return None

def encode(inp, out_720, out_540):
    try:
        cmd720 = ['ffmpeg', '-y', '-i', str(inp), '-c:v', 'libx264', '-crf', '28', '-preset', 'ultrafast', '-maxrate', '1200k', '-bufsize', '2400k', '-c:a', 'aac', '-b:a', '96k', '-movflags', '+faststart', str(out_720)]
        subprocess.run(cmd720, check=True, capture_output=True)
        cmd540 = ['ffmpeg', '-y', '-i', str(out_720), '-vf', 'scale=-2:540', '-c:v', 'libx264', '-crf', '30', '-preset', 'ultrafast', '-maxrate', '800k', '-bufsize', '1600k', '-c:a', 'aac', '-b:a', '96k', '-movflags', '+faststart', str(out_540)]
        subprocess.run(cmd540, check=True, capture_output=True)
        return True
    except: return False

def process_drama(drama):
    print(f"\n[*] Processing: {drama['slug']}")
    r2 = get_r2()
    
    for ep_no in range(1, drama['total'] + 1):
        print(f"  > Ep {ep_no}/{drama['total']} ... ", end="", flush=True)
        
        # Paths
        k720 = f"netshortv2/{drama['slug']}/ep{ep_no:03d}.mp4"
        k540 = f"netshortv2/{drama['slug']}/ep{ep_no:03d}_540p.mp4"
        ksub = f"netshortv2/{drama['slug']}/ep{ep_no:03d}.vtt"
        
        # Check if already in R2
        try:
            r2.head_object(Bucket=R2_BUCKET, Key=k720)
            print("Already in R2. Skip.")
            continue
        except: pass

        ep_data = get_ep_data(drama['vidrama_id'], ep_no)
        if not ep_data:
            print("Failed to get URL.")
            continue
            
        videos = ep_data.get('videos', [])
        vurl = next((v['url'] for q in ['720p', '1080p', '540p'] for v in videos if v.get('quality') == q), None)
        if not vurl: 
            print("No video URL.")
            continue

        raw_path = TEMP_DIR / "raw.mp4"
        o720 = TEMP_DIR / "720.mp4"
        o540 = TEMP_DIR / "540.mp4"

        try:
            # Download
            with requests.get(vurl, stream=True, headers=WEB_HDRS, verify=False) as r:
                with open(raw_path, 'wb') as f:
                    for c in r.iter_content(2*1024*1024): f.write(c)
            
            # Encode
            if encode(raw_path, o720, o540):
                u720 = r2_upload(r2, o720, k720)
                u540 = r2_upload(r2, o540, k540)
                
                # Subtitle
                sub_url = None
                subs = ep_data.get('subtitles', [])
                id_sub = next((s['url'] for s in subs if s.get('language') == 'id_ID'), None)
                if id_sub:
                    sr = requests.get(id_sub, verify=False)
                    if sr.ok:
                        r2.put_object(Bucket=R2_BUCKET, Key=ksub, Body=sr.content, ContentType='text/vtt')
                        sub_url = f"{R2_PUBLIC}/{ksub}"
                
                # Register
                payload = {
                    'episodeNumber': ep_no,
                    'title': f'Episode {ep_no}',
                    'videoUrl': u720,
                    'videoUrl540p': u540,
                    'isActive': True
                }
                resp = requests.post(f"{API_BASE}/api/admin/dramas/{drama['db_id']}/episodes", headers=ADMIN_HDR, json=payload)
                if resp.ok and sub_url:
                    eid = resp.json().get('id')
                    requests.post(f"{API_BASE}/api/admin/episodes/{eid}/subtitles", headers=ADMIN_HDR, json={
                        'language': 'id', 'label': 'Bahasa Indonesia', 'url': sub_url, 'isDefault': True
                    })
                print("Success.")
            else:
                print("Encode failed.")
        except Exception as e:
            print(f"Error: {e}")
        finally:
            for p in [raw_path, o720, o540]:
                if p.exists(): p.unlink()

if __name__ == "__main__":
    for d in DRAMAS:
        process_drama(d)
        # Activation after completion
        requests.patch(f"{API_BASE}/api/admin/dramas/{d['db_id']}", headers=ADMIN_HDR, json={'isActive': True})
