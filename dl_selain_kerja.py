# -*- coding: utf-8 -*-
import sys, boto3, requests, re, os
from botocore.config import Config
sys.stdout.reconfigure(encoding='utf-8', errors='replace')

R2_ENDPOINT = 'https://a142d3b29a5d64943cb251157e25eaf3.r2.cloudflarestorage.com'
R2_KEY_ID   = '07c99c897986ea52703c1285308d5e2c'
R2_SECRET   = '44788d376ffb216e1e73784b6fe1ff1423607928898a87c50819b52cdfc12e44'
BUCKET      = 'shortlovers'
DEST_ROOT   = 'D:/Video Drama/Upload Facebook'
API_BASE    = 'https://api.shortlovers.id'

r2 = boto3.client('s3', endpoint_url=R2_ENDPOINT, aws_access_key_id=R2_KEY_ID,
    aws_secret_access_key=R2_SECRET, config=Config(signature_version='s3v4'), region_name='auto')

TITLE       = 'Selain Kerja, Boleh Cinta'
PREFIX      = 'dramas/microdrama/selain-kerja-boleh-cinta/'
DEST_FOLDER = os.path.join(DEST_ROOT, TITLE)
os.makedirs(DEST_FOLDER, exist_ok=True)

# List semua file
paginator = r2.get_paginator('list_objects_v2')
all_files = []
for page in paginator.paginate(Bucket=BUCKET, Prefix=PREFIX):
    for obj in page.get('Contents', []):
        all_files.append(obj)

print(f'[INFO] Total file di R2: {len(all_files)}')
for f in all_files:
    size_mb = f.get('Size', 0) / (1024 * 1024)
    print(f'  {f["Key"]} ({size_mb:.1f} MB)')

# Pisahkan video dan cover
video_ext = ('.mp4', '.mkv', '.avi', '.mov', '.webm')
img_ext   = ('.jpg', '.jpeg', '.png', '.webp')

video_files = [f for f in all_files if f['Key'].lower().endswith(video_ext)]
img_files   = [f for f in all_files if f['Key'].lower().endswith(img_ext)]

# Pilih resolusi tertinggi:
# Jika ada file tanpa suffix resolusi (ep001.mp4) yang ukurannya > versi _540p,
# berarti itu adalah versi original/asli berkualitas lebih tinggi
orig_files = [f for f in video_files if not re.search(r'_\d+p\.', f['Key'])]
res_files_540 = [f for f in video_files if '_540p.' in f['Key']]
res_files_720 = [f for f in video_files if '_720p.' in f['Key']]
res_files_1080 = [f for f in video_files if '_1080p.' in f['Key']]

if res_files_1080:
    best_res = '1080p'
    res_files = res_files_1080
elif res_files_720:
    best_res = '720p'
    res_files = res_files_720
elif orig_files:
    # File tanpa suffix = original quality (biasanya lebih besar dari 540p)
    avg_orig = sum(f.get('Size',0) for f in orig_files) / max(len(orig_files),1)
    avg_540  = sum(f.get('Size',0) for f in res_files_540) / max(len(res_files_540),1)
    if avg_orig > avg_540 * 1.5:
        best_res = 'original (tertinggi)'
        res_files = orig_files
    else:
        best_res = '540p'
        res_files = res_files_540 if res_files_540 else orig_files
elif res_files_540:
    best_res = '540p'
    res_files = res_files_540
else:
    best_res = 'unknown'
    res_files = video_files

print(f'\n[VIDEO] Resolusi terbaik: {best_res} | {len(res_files)} episode')

def download_file(r2_key, dest_path):
    os.makedirs(os.path.dirname(dest_path), exist_ok=True)
    head = r2.head_object(Bucket=BUCKET, Key=r2_key)
    total_size = head.get('ContentLength', 0)
    size_mb = total_size / (1024 * 1024)
    fname = os.path.basename(dest_path)
    print(f'  [DL] {fname} ({size_mb:.1f} MB)')
    downloaded = [0]
    def progress(chunk):
        downloaded[0] += chunk
        pct = (downloaded[0] / total_size * 100) if total_size else 0
        print(f'\r       {pct:.1f}% ({downloaded[0]/(1024*1024):.1f}/{size_mb:.1f} MB)', end='', flush=True)
    r2.download_file(Bucket=BUCKET, Key=r2_key, Filename=dest_path, Callback=progress)
    print()

# Download cover
cover = None
if img_files:
    for kw in ['cover', 'thumb', 'poster']:
        for f in img_files:
            if kw in f['Key'].lower():
                cover = f
                break
        if cover:
            break
    if not cover:
        cover = max(img_files, key=lambda x: x.get('Size', 0))

if cover:
    ext = os.path.splitext(cover['Key'])[1] or '.jpg'
    cover_dest = os.path.join(DEST_FOLDER, 'cover' + ext)
    download_file(cover['Key'], cover_dest)
    print(f'  [DONE] Cover: {cover_dest}')
else:
    # Coba ambil cover dari API
    print('[INFO] Tidak ada cover di R2, coba dari API...')
    try:
        r = requests.get(f'{API_BASE}/api/dramas?limit=1000', timeout=30)
        dramas = r.json()
        if not isinstance(dramas, list):
            dramas = dramas.get('dramas', dramas.get('data', []))
        for d in dramas:
            if 'selain kerja' in d.get('title','').lower():
                cover_url = d.get('cover','')
                if cover_url:
                    print(f'  [API] Cover URL: {cover_url}')
                    resp = requests.get(cover_url, stream=True, timeout=30)
                    if resp.ok:
                        ext = os.path.splitext(cover_url.split('?')[0])[1] or '.jpg'
                        cover_dest = os.path.join(DEST_FOLDER, 'cover' + ext)
                        with open(cover_dest, 'wb') as cf:
                            for chunk in resp.iter_content(8192):
                                cf.write(chunk)
                        print(f'  [DONE] Cover: {cover_dest}')
                break
    except Exception as e:
        print(f'  [WARN] Cover API error: {e}')

# Download semua video
for vid in res_files:
    ep_name  = os.path.basename(vid['Key'])
    vid_dest = os.path.join(DEST_FOLDER, ep_name)
    if os.path.exists(vid_dest) and os.path.getsize(vid_dest) == vid.get('Size', 0):
        print(f'  [SKIP] {ep_name} sudah ada')
        continue
    try:
        download_file(vid['Key'], vid_dest)
    except Exception as e:
        print(f'  [FAIL] {ep_name}: {e}')

print(f'\n[SELESAI] Semua file disimpan di: {DEST_FOLDER}')
