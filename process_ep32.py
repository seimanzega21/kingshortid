import requests, boto3, subprocess, time, os, urllib3
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

VIDRAMA_ID = '1894650560457961473'
EP_NO = 32
SLUG = 'romantis-di-musim-dingin'
DB_ID = 'cxe8nonlnv3057higcrvddzg'

WEB_HDRS = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
    'Referer': 'https://vidrama.asia/',
    'Cookie': '_fbp=fb.1.1770653154777.876935444165455244; _tt_enable_cookie=1; _ttp=01KH1JE0K4H648BY6E3FQ6EXRZ_.tt.1; _ga=GA1.1.1826262121.1771037718; HstCfa5004644=1772873251576; c_ref_5004644=https%3A%2F%2Fwww.google.com%2F; __dtsu=4C301774685394D291D3AB624E4AA57E; _pubcid=8a5abbf9-164b-422f-b349-0e1ba702ea69; _cc_id=a4a99f9a552125d19ea447bfafb9c63b; HstCmu5004644=1776164034743; HstPn5004644=1; cf_clearance=AQRjv4.Cj2nHbg_KLivmkViGOllnwGPpIVkj35_jfKI-1777471778-1.2.1.1-TEdhFr7wBXOwe6l8ybhNx3V3OAO2FmEP81fCwLc_mclcsLHuLye6b0vcwrShIGHIdgmlaY14VoOLGlccyUA11WHrRIEncihkGDwdc8C44c79F_3U4SEVsPeQAtPP.1_v6j.daxeE5gMBUPycNwj8rIn4fxg5dhhxrCsZvPIyDKo0BUWtkSEcjfRXcll7MrK8y3YSM8WhGmqI.PzKcfsFF.006ENmy7BGlLwqjy_QDYg8Y7xuxVKlIr_3ApmsnXItGKvJ2DDt_XQUqh1H5hqKnf50BS4QFNfxQEUeytk94ofP8SYQwlqg1HEIz3BMlJC4OQhzn5m0L6muYtASD.jwaw; HstCla5004644=1777471778959; HstPt5004644=72; HstCnv5004644=31; HstCns5004644=35; panoramaId_expiry=1777558180696; _ga_HCQQPKGEVH=GS2.1.s1777476684$o70$g1$t1777477281$j55$l0$h0; ttcsid_D5SNQPRC77UDQTF8A5EG=1777476683162::JiaNdPsba2GCy8oVLuyE.75.1777477294114.1; ttcsid=1777476683155::c9Pa9Oee_DaSEml_Mj5I.85.1777477294114.0::1.610918.6485::610880.63.113.1122::610008.512.600'
}

def get_r2():
    return boto3.client('s3', endpoint_url=R2_ENDPOINT,
                        aws_access_key_id=R2_KEY_ID, aws_secret_access_key=R2_SECRET,
                        config=Config(signature_version='s3v4'), region_name='auto')

def r2_upload(r2, local_path, key, content_type='video/mp4'):
    print(f"Uploading {local_path} to {key}...")
    r2.upload_file(str(local_path), R2_BUCKET, key, ExtraArgs={'ContentType': content_type})
    return f"{R2_PUBLIC}/{key}"

def get_episode_url():
    url = f"https://vidrama.asia/api/netshortv2/episode/{VIDRAMA_ID}/{EP_NO}?lang=id_ID"
    r = requests.get(url, headers=WEB_HDRS, timeout=15, verify=False)
    data = r.json()
    if data.get('code') == 200:
        videos = data['data'].get('videos', [])
        best_video = None
        for q in ['720p', '1080p', '540p']:
            for v in videos:
                if v.get('quality') == q:
                    return v['url']
        if videos: return videos[0]['url']
    return None

def encode(inp, out_720, out_540):
    print("Encoding 720p...")
    cmd720 = ['ffmpeg', '-y', '-i', str(inp), '-c:v', 'libx264', '-crf', '26', '-maxrate', '1500k', '-bufsize', '3000k',
              '-c:a', 'aac', '-b:a', '128k', '-movflags', '+faststart', str(out_720)]
    subprocess.run(cmd720, check=True)
    
    print("Encoding 540p...")
    cmd540 = ['ffmpeg', '-y', '-i', str(out_720), '-vf', 'scale=-2:540', '-c:v', 'libx264', '-crf', '28', '-preset', 'fast',
              '-c:a', 'aac', '-b:a', '96k', '-movflags', '+faststart', str(out_540)]
    subprocess.run(cmd540, check=True)

def main():
    vurl = get_episode_url()
    if not vurl:
        print("Failed to get video URL")
        return

    print(f"Video URL: {vurl[:100]}...")
    
    raw = Path('raw_ep32.mp4')
    o720 = Path('ep032.mp4')
    o540 = Path('ep032_540p.mp4')
    
    print("Downloading raw video...")
    with requests.get(vurl, stream=True, headers=WEB_HDRS, verify=False) as r:
        with open(raw, 'wb') as f:
            for chunk in r.iter_content(2*1024*1024): f.write(chunk)
            
    encode(raw, o720, o540)
    
    r2 = get_r2()
    prefix = f"netshortv2/{SLUG}"
    u720 = r2_upload(r2, o720, f"{prefix}/ep032.mp4")
    u540 = r2_upload(r2, o540, f"{prefix}/ep032_540p.mp4")
    
    print("Registering to KingShort API...")
    payload = {
        'episodeNumber': EP_NO,
        'title': f'Episode {EP_NO}',
        'videoUrl': u720,
        'videoUrl540p': u540,
        'isActive': True
    }
    r = requests.post(f"{API_BASE}/api/admin/dramas/{DB_ID}/episodes", headers=ADMIN_HDR, json=payload, timeout=20)
    
    if r.ok:
        print(f"SUCCESS! Episode {EP_NO} registered. ID: {r.json().get('id')}")
    else:
        print(f"FAILED to register: {r.status_code} {r.text}")
        
    # Cleanup
    for p in [raw, o720, o540]:
        if p.exists(): p.unlink()

if __name__ == "__main__":
    main()
