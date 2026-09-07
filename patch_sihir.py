import requests, os, subprocess, boto3, time

API_BASE = 'http://141.11.160.187:3000'
ADMIN_KEY = '00ca04e3e2702be565d7bf44e783255247708289bce9b2fb6187a2e117f87fd14'
ADMIN_HDR = {'x-admin-key': ADMIN_KEY, 'Content-Type': 'application/json'}
R2_ENDPOINT = 'https://a142d3b29a5d64943cb251157e25eaf3.r2.cloudflarestorage.com'
R2_KEY_ID   = '07c99c897986ea52703c1285308d5e2c'
R2_SECRET   = '44788d376ffb216e1e73784b6fe1ff1423607928898a87c50819b52cdfc12e44'
R2_BUCKET   = 'shortlovers'
R2_PUBLIC   = 'https://stream.shortlovers.id'

DRAMA_ID_DB = 'pblx23fpfucss8wmjk2f0n32'
BOOK_ID = '42000026716'
SLUG = 'sihir-curian-takdir-berdarah'
HDR = {'User-Agent': 'Mozilla/5.0'}

r2 = boto3.client('s3', endpoint_url=R2_ENDPOINT, aws_access_key_id=R2_KEY_ID, aws_secret_access_key=R2_SECRET)
TEMP_DIR = 'd:/kingshortid/temp_dramabox'
os.makedirs(TEMP_DIR, exist_ok=True)

# Fetch all episodes from DB (handling pagination)
er = requests.get(f'{API_BASE}/api/dramas/{DRAMA_ID_DB}/episodes?limit=100', timeout=15)
db_eps = {int(e['episodeNumber']): e['id'] for e in er.json()}

def process_missing_episode(ep_no):
    api_ep = ep_no - 1
    r = requests.get(f'https://vidrama.asia/api/dramabox?action=stream&id={BOOK_ID}&episode={api_ep}&lang=in', headers=HDR)
    data = r.json().get('data', {})
    video_url = data.get('videoUrl') or data.get('rawVideoUrl')
    if not video_url:
        print(f"Failed to get video URL for EP {ep_no}")
        return

    src = os.path.join(TEMP_DIR, f"src_{SLUG}_ep{ep_no:03d}.mp4")
    subprocess.run(['ffmpeg', '-y', '-i', video_url, '-c', 'copy', '-loglevel', 'warning', src])
    
    p720 = os.path.join(TEMP_DIR, f"{SLUG}_ep{ep_no:03d}_720p.mp4")
    subprocess.run(['ffmpeg', '-y', '-i', src, '-vf', 'scale=720:-2', '-c:v', 'libx264', '-crf', '23', '-preset', 'fast', '-maxrate', '1500k', '-bufsize', '3000k', '-c:a', 'aac', '-b:a', '128k', '-movflags', '+faststart', '-loglevel', 'warning', p720])
    
    p540 = os.path.join(TEMP_DIR, f"{SLUG}_ep{ep_no:03d}_540p.mp4")
    subprocess.run(['ffmpeg', '-y', '-i', src, '-vf', 'scale=540:-2', '-c:v', 'libx264', '-crf', '26', '-preset', 'fast', '-maxrate', '1000k', '-bufsize', '2000k', '-c:a', 'aac', '-b:a', '96k', '-movflags', '+faststart', '-loglevel', 'warning', p540])

    r2_key_720 = f"dramas/{SLUG}/ep{ep_no:03d}_720p.mp4"
    r2_key_540 = f"dramas/{SLUG}/ep{ep_no:03d}_540p.mp4"
    
    r2.upload_file(p720, R2_BUCKET, r2_key_720, ExtraArgs={'ContentType': 'video/mp4', 'CacheControl': 'public, max-age=31536000'})
    r2.upload_file(p540, R2_BUCKET, r2_key_540, ExtraArgs={'ContentType': 'video/mp4', 'CacheControl': 'public, max-age=31536000'})
    
    url_720 = f"{R2_PUBLIC}/{r2_key_720}"
    url_540 = f"{R2_PUBLIC}/{r2_key_540}"
    
    payload = {'episodeNumber': ep_no, 'title': f'Episode {ep_no}', 'videoUrl': url_720, 'videoUrl540p': url_540, 'isVip': False, 'coinPrice': 0, 'isActive': False}
    resp = requests.post(f"{API_BASE}/api/admin/dramas/{DRAMA_ID_DB}/episodes", headers=ADMIN_HDR, json=payload)
    
    print(f"✅ Fixed missing Episode {ep_no}, DB ID: {resp.json().get('id')}")
    db_eps[ep_no] = resp.json().get('id')
    for f in [src, p720, p540]:
        if os.path.exists(f): os.remove(f)

for ep in [17, 45]:
    if ep not in db_eps:
        print(f"Processing missing episode {ep}...")
        process_missing_episode(ep)

# Process subtitles for 9 to 57
for ep_no in range(9, 58):
    if ep_no not in db_eps: continue
    ep_id = db_eps[ep_no]
    
    # Check if subtitle already exists
    sub_chk = requests.get(f"{API_BASE}/api/episodes/{ep_id}/subtitles")
    if sub_chk.ok and len(sub_chk.json().get('subtitles', [])) > 0:
        print(f"Subtitle for EP {ep_no} already exists.")
        continue

    api_ep = ep_no - 1
    r = requests.get(f'https://vidrama.asia/api/dramabox?action=stream&id={BOOK_ID}&episode={api_ep}&lang=in', headers=HDR)
    data = r.json().get('data', {})
    subs = data.get('subtitles', [])
    
    indo_sub = next((s for s in subs if s.get('language') == 'in' or s.get('lang') == 'in'), None)
    if indo_sub:
        srt_url = indo_sub['url']
        srt_path = os.path.join(TEMP_DIR, f"{SLUG}_ep{ep_no}.srt")
        vtt_path = os.path.join(TEMP_DIR, f"{SLUG}_ep{ep_no}.vtt")
        
        sr_resp = requests.get(srt_url)
        with open(srt_path, 'wb') as f:
            f.write(sr_resp.content)
            
        subprocess.run(['ffmpeg', '-y', '-i', srt_path, vtt_path], capture_output=True)
        
        if os.path.exists(vtt_path):
            r2_key_vtt = f"dramas/{SLUG}/ep{ep_no:03d}_id.vtt"
            r2.upload_file(vtt_path, R2_BUCKET, r2_key_vtt, ExtraArgs={'ContentType': 'text/vtt', 'CacheControl': 'public, max-age=31536000'})
            vtt_url = f"{R2_PUBLIC}/{r2_key_vtt}"
            
            sub_payload = {
                "language": "id",
                "label": "Indonesian",
                "url": vtt_url,
                "isDefault": True
            }
            sub_post = requests.post(f"{API_BASE}/api/admin/episodes/{ep_id}/subtitles", headers=ADMIN_HDR, json=sub_payload)
            if not sub_post.ok:
                sub_post = requests.post(f"{API_BASE}/api/episodes/{ep_id}/subtitles", headers=ADMIN_HDR, json=sub_payload)
            print(f"✅ Added subtitle for EP {ep_no}: {sub_post.status_code}")
            
            os.remove(srt_path)
            os.remove(vtt_path)
    else:
        print(f"No Indo subtitle found for EP {ep_no}")

print("DONE!")
