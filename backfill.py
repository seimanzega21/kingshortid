import requests, boto3, subprocess, time, os, urllib3, re
from pathlib import Path
from botocore.config import Config

urllib3.disable_warnings()

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
    # Using fresh cookies from scrape_vidrama_standalone.py which worked for ep32
    'Cookie': '_fbp=fb.1.1770653154777.876935444165455244; _tt_enable_cookie=1; _ttp=01KH1JE0K4H648BY6E3FQ6EXRZ_.tt.1; _ga=GA1.1.1826262121.1771037718; HstCfa5004644=1772873251576; c_ref_5004644=https%3A%2F%2Fwww.google.com%2F; __dtsu=4C301774685394D291D3AB624E4AA57E; _pubcid=8a5abbf9-164b-422f-b349-0e1ba702ea69; _cc_id=a4a99f9a552125d19ea447bfafb9c63b; HstCmu5004644=1776164034743; HstPn5004644=1; cf_clearance=AQRjv4.Cj2nHbg_KLivmkViGOllnwGPpIVkj35_jfKI-1777471778-1.2.1.1-TEdhFr7wBXOwe6l8ybhNx3V3OAO2FmEP81fCwLc_mclcsLHuLye6b0vcwrShIGHIdgmlaY14VoOLGlccyUA11WHrRIEncihkGDwdc8C44c79F_3U4SEVsPeQAtPP.1_v6j.daxeE5gMBUPycNwj8rIn4fxg5dhhxrCsZvPIyDKo0BUWtkSEcjfRXcll7MrK8y3YSM8WhGmqI.PzKcfsFF.006ENmy7BGlLwqjy_QDYg8Y7xuxVKlIr_3ApmsnXItGKvJ2DDt_XQUqh1H5hqKnf50BS4QFNfxQEUeytk94ofP8SYQwlqg1HEIz3BMlJC4OQhzn5m0L6muYtASD.jwaw; HstCla5004644=1777471778959; HstPt5004644=72; HstCnv5004644=31; HstCns5004644=35; panoramaId_expiry=1777558180696; _ga_HCQQPKGEVH=GS2.1.s1777476684$o70$g1$t1777477281$j55$l0$h0; ttcsid_D5SNQPRC77UDQTF8A5EG=1777476683162::JiaNdPsba2GCy8oVLuyE.75.1777477294114.1; ttcsid=1777476683155::c9Pa9Oee_DaSEml_Mj5I.85.1777477294114.0::1.610918.6485::610880.63.113.1122::610008.512.600'
}

TARGETS = [
    {'id': '2050068409973997569', 'slug': 'raja-yang-ditakuti-musuh', 'title': 'Raja yang Ditakuti Musuh', 'total': 82},
    {'id': '2033798825713336321', 'slug': 'menghabisi-yang-jahat', 'title': 'Menghabisi yang Jahat', 'total': 91},
    {'id': '2020778605549871106', 'slug': 'dua-kuasa-menjadi-satu', 'title': 'Dua Kuasa Menjadi Satu', 'total': 102}
]

TEMP_DIR = Path("D:/kingshortid/scripts/tmp")
TEMP_DIR.mkdir(parents=True, exist_ok=True)

def get_r2():
    return boto3.client('s3', endpoint_url=R2_ENDPOINT,
                        aws_access_key_id=R2_KEY_ID, aws_secret_access_key=R2_SECRET,
                        config=Config(signature_version='s3v4'), region_name='auto')

def r2_upload(r2, local_path, key, content_type='video/mp4'):
    r2.upload_file(str(local_path), R2_BUCKET, key, ExtraArgs={'ContentType': content_type})
    return f"{R2_PUBLIC}/{key}"

def get_episode_data(drama_id, ep_no):
    url = f"{VIDRAMA_API}/episode/{drama_id}/{ep_no}?lang=id_ID"
    try:
        r = requests.get(url, headers=WEB_HDRS, timeout=15, verify=False)
        if r.ok:
            data = r.json()
            if data.get('code') == 200: return data['data']
    except:
        pass
    return None

def download_and_encode(ep_url, raw_path, out720, out540):
    try:
        with requests.get(ep_url, stream=True, headers=WEB_HDRS, verify=False) as r:
            with open(raw_path, 'wb') as f:
                for c in r.iter_content(2*1024*1024): f.write(c)
        
        # Encode 720p
        cmd720 = ['ffmpeg', '-y', '-i', str(raw_path), '-c:v', 'libx264', '-crf', '28', '-preset', 'ultrafast', '-maxrate', '1500k', '-bufsize', '3000k', '-c:a', 'aac', '-b:a', '96k', '-movflags', '+faststart', '-loglevel', 'error', str(out720)]
        subprocess.run(cmd720, check=True)
        
        # Encode 540p
        cmd540 = ['ffmpeg', '-y', '-i', str(out720), '-vf', 'scale=-2:540', '-c:v', 'libx264', '-crf', '30', '-preset', 'ultrafast', '-maxrate', '800k', '-bufsize', '1600k', '-c:a', 'aac', '-b:a', '96k', '-movflags', '+faststart', '-loglevel', 'error', str(out540)]
        subprocess.run(cmd540, check=True)
        return True
    except Exception as e:
        print(f"Encode error: {e}")
        return False
    finally:
        if raw_path.exists(): raw_path.unlink()

def process_episode(drama, ep_no, r2):
    ep_data = get_episode_data(drama['id'], ep_no)
    if not ep_data:
        print(f"  [WARN] Failed to get URL for ep {ep_no}")
        return None
    
    videos = ep_data.get('videos', [])
    vurl = next((v['url'] for q in ['720p', '1080p', '540p'] for v in videos if v.get('quality') == q), None)
    if not vurl:
        print(f"  [WARN] No video URL for ep {ep_no}")
        return None
    
    raw = TEMP_DIR / f"raw_{ep_no}.mp4"
    o720 = TEMP_DIR / "720.mp4"
    o540 = TEMP_DIR / "540.mp4"
    
    if not download_and_encode(vurl, raw, o720, o540):
        return None
    
    # Upload to R2
    prefix = f"netshortv2/{drama['slug']}"
    r2_upload(r2, o720, f"{prefix}/ep{ep_no:03d}.mp4")
    r2_upload(r2, o540, f"{prefix}/ep{ep_no:03d}_540p.mp4")
    
    # Subtitle
    subs = ep_data.get('subtitles', [])
    id_sub = next((s['url'] for s in subs if s.get('language') == 'id_ID'), None)
    if id_sub:
        sr = requests.get(id_sub, verify=False, timeout=15)
        if sr.ok:
            r2.put_object(Bucket=R2_BUCKET, Key=f"{prefix}/ep{ep_no:03d}.vtt", Body=sr.content, ContentType='text/vtt')
    
    if o720.exists(): o720.unlink()
    if o540.exists(): o540.unlink()
    
    return True

def backfill_drama(drama):
    print(f"\n[*] BACKFILLING: {drama['title']}")
    r2 = get_r2()
    
    for ep_no in range(1, drama['total'] + 1):
        print(f"  > Ep {ep_no}/{drama['total']}", end=" & ", flush=True)
        
        # Check if already exists
        try:
            r2.head_object(Bucket=R2_BUCKET, Key=f"netshortv2/{drama['slug']}/ep{ep_no:03d}.mp4")
            print("SKIP (exists in R2)")
            continue
        except:
            pass
        
        # Retry logic
        retries = 3
        for attempt in range(retries):
            if process_episode(drama, ep_no, r2):
                print("OK")
                break
            elif attempt < retries - 1:
                time.sleep(5)
            else:
                print("FAILED after 3 retries.")
    
    print(f"FINISHED: {drama['title']}")

if __name__ == "__main__":
    for d in TARGETS:
        backfill_drama(d)
    print("\nALL BACKFILL COMPLETE.")
