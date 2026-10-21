import sys
if sys.platform == 'win32':
    sys.stdout.reconfigure(encoding='utf-8', errors='replace')
    sys.stderr.reconfigure(encoding='utf-8', errors='replace')

import os, re, json, uuid, shutil, base64, subprocess, requests, boto3
from pathlib import Path
from botocore.config import Config

API_BASE    = 'https://api.shortlovers.id/api'
ADMIN_KEY   = '00ca04e3e2702be565d7bf44e783255247708289bce9b2fb6187a2e117f87fd14'
ADMIN_HDR   = {'x-admin-key': ADMIN_KEY, 'Content-Type': 'application/json'}

R2_ENDPOINT = 'https://a142d3b29a5d64943cb251157e25eaf3.r2.cloudflarestorage.com'
R2_KEY_ID   = '07c99c897986ea52703c1285308d5e2c'
R2_SECRET   = '44788d376ffb216e1e73784b6fe1ff1423607928898a87c50819b52cdfc12e44'
R2_BUCKET   = 'shortlovers'
R2_PUBLIC   = 'https://stream.shortlovers.id'

TITLE       = 'Kelahiran Kembali Pemandian'
SLUG        = 'kelahiran-kembali-pemandian'
PREFIX      = f"dracinema/{SLUG}"
DRAMA_ID    = 'maokqmehxdt2z0rf1cumawbd'

LOCAL_DIR   = Path("D:/Video Drama/Facebook") / TITLE
TEMP_DIR    = Path("D:/temp_scraper") / SLUG
TEMP_DIR.mkdir(parents=True, exist_ok=True)

s3 = boto3.client('s3', endpoint_url=R2_ENDPOINT,
                  aws_access_key_id=R2_KEY_ID, aws_secret_access_key=R2_SECRET,
                  config=Config(signature_version='s3v4'), region_name='auto')

# 1. Get fresh URL for Ep 20 from bridge
payload = {
    'id': str(uuid.uuid4()),
    'movieKey': 'kelahiran-kembali-pemandian-dn_2102231938793574401',
    'episode': 20
}
r = requests.post('http://127.0.0.1:20199/request', json=payload, timeout=30)
pb = r.json().get('data', {})
video_url = pb.get('url')
print('Ep 20 Fresh URL obtained:', video_url[:60] if video_url else 'None')

raw_mp4 = TEMP_DIR / "raw_020_retry.mp4"
out_540 = TEMP_DIR / "out540_020_retry.mp4"
audio_mp3 = TEMP_DIR / "audio_020_retry.mp3"
local_file = LOCAL_DIR / "ep020.mp4"
local_vtt = LOCAL_DIR / "ep020.vtt"

# 2. Download
header_str = "User-Agent: Mozilla/5.0\r\nReferer: https://www.dracinema.com/\r\n"
cmd = ['ffmpeg', '-y', '-headers', header_str, '-i', video_url, '-c', 'copy', '-movflags', '+faststart', '-loglevel', 'error', str(raw_mp4)]
subprocess.run(cmd)

# 3. 540p
cmd_540 = ['ffmpeg', '-y', '-i', str(raw_mp4), '-vf', 'scale=-2:540', '-c:v', 'libx264', '-crf', '28', '-preset', 'fast', '-c:a', 'aac', '-b:a', '96k', '-movflags', '+faststart', '-loglevel', 'error', str(out_540)]
subprocess.run(cmd_540)

# 4. Audio & Subtitle
cmd_aud = ['ffmpeg', '-y', '-i', str(raw_mp4), '-vn', '-c:a', 'mp3', '-b:a', '64k', '-ar', '16000', '-loglevel', 'error', str(audio_mp3)]
subprocess.run(cmd_aud)

with open(audio_mp3, 'rb') as fp:
    audio_b64 = base64.b64encode(fp.read()).decode('utf-8')

prompt = (
    "Transcribe the dialogue in this Chinese audio clip and translate it into natural, fluent Indonesian in WebVTT subtitle format.\n"
    "Requirements:\n"
    "1. Output MUST start with 'WEBVTT'.\n"
    "2. Translate accurately into everyday natural Indonesian suitable for short drama dubbing/subtitles.\n"
    "3. Output ONLY the Indonesian translation text (do NOT include any Chinese characters).\n"
    "4. Output pure WebVTT text directly, no markdown formatting (no ```vtt blocks)."
)
headers = {'Authorization': 'Bearer sk-6c5720214189ea51-otb97y-5446d478', 'Content-Type': 'application/json'}
payload_ai = {
    'model': 'ag/gemini-3.8-flash-high',
    'stream': False,
    'messages': [{'role': 'user', 'content': [{'type': 'text', 'text': prompt}, {'type': 'input_audio', 'input_audio': {'data': audio_b64, 'format': 'mp3'}}]}]
}
r_ai = requests.post('http://localhost:20128/v1/chat/completions', headers=headers, json=payload_ai, timeout=60)
vtt_raw = r_ai.json().get('choices', [{}])[0].get('message', {}).get('content', '')

# Clean VTT
time_re = re.compile(r'(\d{2}:)?(\d{2}:\d{2}[.,]\d{3})\s*-->\s*(\d{2}:)?(\d{2}:\d{2}[.,]\d{3})')
cues = []
cur_time = None
cur_text = []
for line in vtt_raw.replace('\r\n', '\n').split('\n'):
    s = line.strip()
    if not s or s.startswith('WEBVTT') or s.startswith('NOTE'): continue
    m = time_re.search(s)
    if m:
        if cur_time and cur_text: cues.append((cur_time, '\n'.join(cur_text)))
        s1 = m.group(1) or '00:'
        s2 = m.group(2).replace(',', '.')
        e1 = m.group(3) or '00:'
        e2 = m.group(4).replace(',', '.')
        cur_time = f'{s1}{s2} --> {e1}{e2}'
        cur_text = []
    elif not s.isdigit():
        cs = re.sub(r'line:\d+%.*$', '', s).strip()
        cs = re.sub(r'<[^>]+>', '', cs)
        if cs: cur_text.append(cs)
if cur_time and cur_text: cues.append((cur_time, '\n'.join(cur_text)))

vtt_clean = 'WEBVTT\n\n' + '\n\n'.join(f'{i}\n{t}\n{txt}' for i, (t, txt) in enumerate(cues, 1)) + '\n'
local_vtt.write_text(vtt_clean, encoding='utf-8')
shutil.copy2(raw_mp4, local_file)

# 5. Upload R2
k720 = f"{PREFIX}/ep020.mp4"
k540 = f"{PREFIX}/ep020_540p.mp4"
kvtt = f"{PREFIX}/ep020.vtt"

s3.upload_file(str(raw_mp4), R2_BUCKET, k720, ExtraArgs={'ContentType': 'video/mp4'})
s3.upload_file(str(out_540), R2_BUCKET, k540, ExtraArgs={'ContentType': 'video/mp4'})
s3.upload_file(str(local_vtt), R2_BUCKET, kvtt, ExtraArgs={'ContentType': 'text/vtt'})

# 6. Upsert DB
ep_payload = {'episodeNumber': 20, 'title': 'Episode 20', 'videoUrl': f"{R2_PUBLIC}/{k720}", 'videoUrl540p': f"{R2_PUBLIC}/{k540}", 'isActive': True}
r_ep = requests.post(f"{API_BASE}/admin/dramas/{DRAMA_ID}/episodes", headers=ADMIN_HDR, json=ep_payload)
ep_id = r_ep.json().get('id') if r_ep.ok else None
if ep_id:
    sub_payload = {'language': 'indonesia', 'label': 'Indonesia', 'url': f"{R2_PUBLIC}/{kvtt}", 'isDefault': True}
    requests.post(f"{API_BASE}/episodes/{ep_id}/subtitles", headers=ADMIN_HDR, json=sub_payload)

# Clean temp
raw_mp4.unlink(missing_ok=True)
out_540.unlink(missing_ok=True)
audio_mp3.unlink(missing_ok=True)
print('Ep 20 successfully processed, uploaded to R2, and registered to DB!')
