import requests, subprocess, boto3, shutil, urllib3
from botocore.config import Config
from pathlib import Path

urllib3.disable_warnings()

API_BASE    = 'https://api.shortlovers.id/api'
ADMIN_KEY   = '00ca04e3e2702be565d7bf44e783255247708289bce9b2fb6187a2e117f87fd14'
ADMIN_HDR   = {'x-admin-key': ADMIN_KEY, 'Content-Type': 'application/json'}

R2_ENDPOINT = 'https://a142d3b29a5d64943cb251157e25eaf3.r2.cloudflarestorage.com'
R2_KEY_ID   = '07c99c897986ea52703c1285308d5e2c'
R2_SECRET   = '44788d376ffb216e1e73784b6fe1ff1423607928898a87c50819b52cdfc12e44'
R2_BUCKET   = 'shortlovers'
R2_PUBLIC   = 'https://stream.shortlovers.id'

s3 = boto3.client('s3', endpoint_url=R2_ENDPOINT,
                  aws_access_key_id=R2_KEY_ID, aws_secret_access_key=R2_SECRET,
                  config=Config(signature_version='s3v4'), region_name='auto')

headers = {'User-Agent': 'Mozilla/5.0'}

items_to_patch = [
    # (movie_id, slug, title, missing_eps)
    ('7543054473279573009', 'rubah-suci-pembawa-keberuntungan', 'Rubah Suci Pembawa Keberuntungan', [41, 42]),
    ('7563548465666460725', 'nama-terukir-di-abu-kenangan', 'Nama Terukir di Abu Kenangan', [2])
]

for movie_id, slug, title, missing_eps in items_to_patch:
    print(f"\n--- Patching {title} ---")
    url = f"https://vidrama.asia/api/melolov3/multi-video?id={movie_id}&lang=id"
    r = requests.get(url, headers=headers, verify=False, timeout=15)
    eps_data = r.json().get('episodes', [])
    eps_map = {e.get('index'): e.get('stream_url') for e in eps_data}

    # Get drama ID in DB
    r_search = requests.get(f"{API_BASE}/dramas/search?q={requests.utils.quote(title)}")
    d_info = r_search.json().get('dramas', [])[0]
    drama_id = d_info['id']

    local_dir = Path(f"D:/Video Drama/Facebook/{title}")
    local_dir.mkdir(parents=True, exist_ok=True)

    for ep_no in missing_eps:
        stream_url = eps_map.get(ep_no)
        if not stream_url:
            print(f"No stream url for ep {ep_no}")
            continue

        raw_path = Path(f"temp_{slug}_raw_{ep_no}.mp4")
        o720_path = Path(f"temp_{slug}_720_{ep_no}.mp4")
        o540_path = Path(f"temp_{slug}_540_{ep_no}.mp4")

        print(f"Downloading ep{ep_no:03d}...")
        subprocess.run(['yt-dlp', '--retries', '10', '-o', str(raw_path), stream_url], check=True)

        print(f"Transcoding ep{ep_no:03d}...")
        subprocess.run([
            'ffmpeg', '-y', '-i', str(raw_path),
            '-c:v', 'libx264', '-crf', '26', '-maxrate', '1500k', '-bufsize', '3000k',
            '-c:a', 'aac', '-b:a', '128k', '-movflags', '+faststart',
            '-loglevel', 'error', str(o720_path)
        ], check=True)

        subprocess.run([
            'ffmpeg', '-y', '-i', str(o720_path),
            '-vf', 'scale=-2:540',
            '-c:v', 'libx264', '-crf', '28', '-preset', 'fast',
            '-c:a', 'aac', '-b:a', '96k', '-movflags', '+faststart',
            '-loglevel', 'error', str(o540_path)
        ], check=True)

        k720 = f"melolov3/{slug}/ep{ep_no:03d}.mp4"
        k540 = f"melolov3/{slug}/ep{ep_no:03d}_540p.mp4"

        print(f"Uploading ep{ep_no:03d} to R2...")
        s3.upload_file(str(o720_path), R2_BUCKET, k720, ExtraArgs={'ContentType': 'video/mp4'})
        s3.upload_file(str(o540_path), R2_BUCKET, k540, ExtraArgs={'ContentType': 'video/mp4'})

        payload = {
            'dramaId': drama_id,
            'episodeNumber': ep_no,
            'title': f'Episode {ep_no}',
            'videoUrl': f'{R2_PUBLIC}/{k720}',
            'videoUrl540p': f'{R2_PUBLIC}/{k540}',
            'isActive': True
        }
        requests.post(f"{API_BASE}/episodes", headers=ADMIN_HDR, json=payload)

        shutil.copy2(o720_path, local_dir / f"ep{ep_no:03d}.mp4")
        print(f"ep{ep_no:03d} patched successfully!")

        for p in [raw_path, o720_path, o540_path]:
            if p.exists(): p.unlink()

print("\nAll missing episodes successfully patched!")
