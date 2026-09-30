# -*- coding: utf-8 -*-
"""
BATCH QUEUE: Ingest 9 StardustTV dramas sequentially (local Windows).
Dramas processed one by one, skipping already-done episodes.
"""
import sys
import requests
import boto3
import json
import time
import os
import subprocess
import urllib3
import tempfile
from botocore.config import Config

urllib3.disable_warnings()

# ─── CONFIG ────────────────────────────────────────────────────────────────
API_BASE  = 'https://api.shortlovers.id'
ADMIN_KEY = '00ca04e3e2702be565d7bf44e783255247708289bce9b2fb6187a2e117f87fd14'
ADMIN_HDR = {'x-admin-key': ADMIN_KEY, 'Content-Type': 'application/json'}

R2_ENDPOINT = 'https://a142d3b29a5d64943cb251157e25eaf3.r2.cloudflarestorage.com'
R2_KEY_ID   = '07c99c897986ea52703c1285308d5e2c'
R2_SECRET   = '44788d376ffb216e1e73784b6fe1ff1423607928898a87c50819b52cdfc12e44'
R2_BUCKET   = 'shortlovers'
R2_PUBLIC   = 'https://stream.shortlovers.id'

TEMP_DIR = tempfile.mkdtemp(prefix='stardust_batch2_')

FFMPEG_HEADERS = (
    "User-Agent: Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
    "(KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36\r\n"
    "Referer: https://vidrama.asia/\r\n"
)

# ─── DRAMA QUEUE ────────────────────────────────────────────────────────────
QUEUE = [
    {'id': '23201', 'slug': 'raja-telah-kembali-kamu-baru-sadar',               'genres': ['Action', 'Drama']},
    {'id': '21935', 'slug': 'pengemis-ternyata-raja-naga',                       'genres': ['Action', 'Fantasy', 'Drama']},
    {'id': '21510', 'slug': 'agen-maut-bodyguard-sang-ceo',                      'genres': ['Action', 'Romantis', 'Drama']},
    {'id': '18630', 'slug': 'sang-penagih-utang-takdir',                         'genres': ['Drama', 'Thriller']},
    {'id': '23208', 'slug': 'cinta-di-usia-50-hidup-sederhana-bernilai-tak-ternilai', 'genres': ['Romantis', 'Drama', 'Family']},
    {'id': '22584', 'slug': 'mertua-turun-tangan-menantu-hancur',                'genres': ['Drama', 'Komedi', 'Family']},
    {'id': '22984', 'slug': '11-tahun-kemudian-aku-bela-kamu',                   'genres': ['Romantis', 'Drama']},
    {'id': '21203', 'slug': 'bangkitnya-penguasa-roma',                          'genres': ['Action', 'Drama', 'Historical']},
    {'id': '20100', 'slug': 'cinta-takkan-berbalik',                             'genres': ['Romantis', 'Drama']},
]

# ─── R2 CLIENT ──────────────────────────────────────────────────────────────
def get_r2():
    return boto3.client(
        's3', endpoint_url=R2_ENDPOINT,
        aws_access_key_id=R2_KEY_ID, aws_secret_access_key=R2_SECRET,
        config=Config(signature_version='s3v4'), region_name='auto'
    )

# ─── FETCH DRAMA DETAILS ────────────────────────────────────────────────────
def fetch_drama_details(drama_id):
    url = 'https://vidrama.asia/api/stardusttv?action=detail&id=' + drama_id + '&lang=id'
    hdrs = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'}
    for attempt in range(1, 4):
        try:
            r = requests.get(url, headers=hdrs, timeout=20)
            if r.ok:
                data = r.json()
                if data.get('success') and data.get('data'):
                    return data['data']
            print('  ! HTTP ' + str(r.status_code) + ' (attempt ' + str(attempt) + '/3)')
        except Exception as e:
            print('  ! Error (attempt ' + str(attempt) + '/3): ' + str(e))
        time.sleep(3)
    return None

# ─── COVER: CONVERT & UPLOAD ────────────────────────────────────────────────
def upload_cover(r2, slug, cover_url):
    r2_key = 'dramas/' + slug + '/cover_hq.jpg'
    try:
        r2.head_object(Bucket=R2_BUCKET, Key=r2_key)
        url = R2_PUBLIC + '/' + r2_key
        print('  [cover] Already in R2: ' + url)
        return url
    except Exception:
        pass

    print('  [cover] Downloading & converting...')
    raw_path = os.path.join(TEMP_DIR, slug + '_cover_raw')
    clean_path = os.path.join(TEMP_DIR, slug + '_cover.jpg')
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
        url = R2_PUBLIC + '/' + r2_key
        print('  [cover] Uploaded: ' + url)
        return url
    except Exception as e:
        print('  [cover] Failed: ' + str(e))
        return cover_url

# ─── REGISTER DRAMA ─────────────────────────────────────────────────────────
def register_drama(metadata, slug, genres, cover_r2_url):
    title = metadata.get('title', '')
    r = requests.get(API_BASE + '/api/dramas', params={'search': title}, timeout=15)
    if r.ok:
        for d in r.json().get('dramas', []):
            if title.lower() in d.get('title', '').lower():
                print('  [drama] Already in DB: ' + d['id'])
                return d['id']

    episodes = metadata.get('list', [])
    payload = {
        'title': title,
        'description': metadata.get('description') or metadata.get('introduction') or '',
        'cover': cover_r2_url,
        'genres': genres,
        'totalEpisodes': len(episodes),
        'status': 'completed',
        'country': 'China',
        'language': 'Indonesia',
        'isActive': False,
        'isVip': False,
    }
    r = requests.post(API_BASE + '/api/admin/dramas', headers=ADMIN_HDR, json=payload, timeout=30)
    if r.ok:
        resp = r.json()
        drama_id = resp.get('id') or resp.get('drama', {}).get('id')
        print('  [drama] Registered! ID: ' + str(drama_id))
        return drama_id
    print('  [drama] Registration failed: ' + str(r.status_code) + ' ' + r.text[:200])
    return None

# ─── DOWNLOAD + TRANSCODE ───────────────────────────────────────────────────
def download_and_transcode(m3u8_url, slug, ep_no):
    local_720 = os.path.join(TEMP_DIR, slug + '_ep' + str(ep_no).zfill(3) + '_720p.mp4')
    local_540 = os.path.join(TEMP_DIR, slug + '_ep' + str(ep_no).zfill(3) + '_540p.mp4')

    for f in [local_720, local_540]:
        if os.path.exists(f):
            os.remove(f)

    # 720p stream copy + faststart
    success_720 = False
    for attempt in range(1, 4):
        cmd = [
            'ffmpeg', '-y',
            '-headers', FFMPEG_HEADERS,
            '-i', m3u8_url,
            '-c', 'copy',
            '-movflags', '+faststart',
            '-loglevel', 'warning',
            local_720
        ]
        res = subprocess.run(cmd, capture_output=True, text=True, errors='ignore', timeout=600)
        if res.returncode == 0 and os.path.exists(local_720) and os.path.getsize(local_720) > 50000:
            size_mb = os.path.getsize(local_720) / (1024 * 1024)
            print('    [720p] OK (' + str(round(size_mb, 1)) + ' MB)')
            success_720 = True
            break
        print('    [720p] Attempt ' + str(attempt) + '/3 failed')
        time.sleep(5)

    if not success_720:
        return None, None

    # 540p transcode + faststart
    success_540 = False
    for attempt in range(1, 4):
        cmd = [
            'ffmpeg', '-y',
            '-i', local_720,
            '-vf', 'scale=-2:540',
            '-c:v', 'libx264', '-crf', '26', '-preset', 'fast',
            '-maxrate', '1000k', '-bufsize', '2000k',
            '-c:a', 'aac', '-b:a', '96k',
            '-movflags', '+faststart',
            '-loglevel', 'warning',
            local_540
        ]
        res = subprocess.run(cmd, capture_output=True, text=True, errors='ignore', timeout=300)
        if res.returncode == 0 and os.path.exists(local_540) and os.path.getsize(local_540) > 50000:
            size_mb = os.path.getsize(local_540) / (1024 * 1024)
            print('    [540p] OK (' + str(round(size_mb, 1)) + ' MB)')
            success_540 = True
            break
        print('    [540p] Attempt ' + str(attempt) + '/3 failed')
        time.sleep(5)

    return local_720, (local_540 if success_540 else None)

# ─── UPLOAD TO R2 ───────────────────────────────────────────────────────────
def upload_to_r2(r2, local_path, r2_key):
    try:
        size_mb = os.path.getsize(local_path) / (1024 * 1024)
        with open(local_path, 'rb') as f:
            r2.upload_fileobj(
                f, R2_BUCKET, r2_key,
                ExtraArgs={'ContentType': 'video/mp4', 'CacheControl': 'public, max-age=31536000'}
            )
        print('    [r2] Uploaded ' + os.path.basename(r2_key) + ' (' + str(round(size_mb, 1)) + ' MB)')
        return R2_PUBLIC + '/' + r2_key
    except Exception as e:
        print('    [r2] Upload failed: ' + str(e))
        return None

# ─── REGISTER EPISODE ───────────────────────────────────────────────────────
def register_episode(drama_id, ep_no, url_720, url_540):
    payload = {
        'episodeNumber': ep_no,
        'title': 'Episode ' + str(ep_no),
        'videoUrl': url_720 or url_540 or '',
        'videoUrl540p': url_540 or '',
        'isVip': False,
        'coinPrice': 0,
        'isActive': True,
    }
    r = requests.post(
        API_BASE + '/api/admin/dramas/' + drama_id + '/episodes',
        headers=ADMIN_HDR, json=payload, timeout=20
    )
    if r.ok:
        return r.json().get('id')
    # Try PATCH if already exists
    r2 = requests.patch(
        API_BASE + '/api/admin/dramas/' + drama_id + '/episodes/' + str(ep_no),
        headers=ADMIN_HDR, json=payload, timeout=20
    )
    if r2.ok:
        return r2.json().get('id') or 'updated'
    return None

# ─── PROCESS SINGLE DRAMA ───────────────────────────────────────────────────
def process_drama(item, r2, queue_idx, queue_total):
    drama_id_src = item['id']
    slug         = item['slug']
    genres       = item['genres']

    print('')
    print('=' * 65)
    print('[' + str(queue_idx) + '/' + str(queue_total) + '] DRAMA: ' + slug + ' (ID: ' + drama_id_src + ')')
    print('=' * 65)

    # 1. Fetch metadata
    print('[1] Fetching metadata...')
    metadata = fetch_drama_details(drama_id_src)
    if not metadata:
        print('  FAIL: Could not fetch metadata. Skipping.')
        return False

    episodes = metadata.get('list', [])
    print('  Title   : ' + metadata.get('title', ''))
    print('  Episodes: ' + str(len(episodes)))

    # 2. Upload cover
    print('[2] Processing cover...')
    cover_url = metadata.get('cover') or metadata.get('image', '')
    cover_r2_url = upload_cover(r2, slug, cover_url)

    # 3. Register drama
    print('[3] Registering drama...')
    db_drama_id = register_drama(metadata, slug, genres, cover_r2_url)
    if not db_drama_id:
        print('  FAIL: Drama registration failed. Skipping.')
        return False

    # 4. Get already-done episodes
    done_eps = set()
    er = requests.get(API_BASE + '/api/dramas/' + db_drama_id + '/episodes', timeout=15)
    if er.ok:
        ep_data = er.json()
        eps_list = ep_data if isinstance(ep_data, list) else ep_data.get('episodes', [])
        for ep in eps_list:
            done_eps.add(int(ep.get('episodeNumber', 0)))
    print('[4] Already in DB: ' + str(len(done_eps)) + ' episodes')

    # 5. Process each episode
    success_count = 0
    fail_count    = 0
    ep_start      = time.time()

    for ep in episodes:
        ep_no     = int(ep.get('episodeNumber') or ep.get('episodeNo', 0))
        m3u8_url  = ep.get('h264') or ep.get('videoUrl') or ep.get('videoPath', '')

        if not ep_no or not m3u8_url:
            continue

        print('')
        print('  EP ' + str(ep_no) + '/' + str(len(episodes)) + ' [' + slug + ']')

        if ep_no in done_eps:
            print('    [skip] Already in DB')
            success_count += 1
            continue

        r2_key_720 = 'dramas/' + slug + '/ep' + str(ep_no).zfill(3) + '_720p.mp4'
        r2_key_540 = 'dramas/' + slug + '/ep' + str(ep_no).zfill(3) + '_540p.mp4'

        url_720 = url_540 = None

        # Check R2
        try:
            r2.head_object(Bucket=R2_BUCKET, Key=r2_key_720)
            url_720 = R2_PUBLIC + '/' + r2_key_720
            print('    [r2] 720p already exists')
        except Exception:
            pass

        try:
            r2.head_object(Bucket=R2_BUCKET, Key=r2_key_540)
            url_540 = R2_PUBLIC + '/' + r2_key_540
            print('    [r2] 540p already exists')
        except Exception:
            pass

        # Download + transcode + upload if needed
        if not url_720:
            local_720, local_540 = download_and_transcode(m3u8_url, slug, ep_no)
            if not local_720:
                print('    FAIL: Download/transcode failed for EP ' + str(ep_no))
                fail_count += 1
                continue

            url_720 = upload_to_r2(r2, local_720, r2_key_720)
            if local_540:
                url_540 = upload_to_r2(r2, local_540, r2_key_540)

            for f in [local_720, local_540]:
                if f and os.path.exists(f):
                    try:
                        os.remove(f)
                    except Exception:
                        pass

            if not url_720:
                print('    FAIL: R2 upload failed for EP ' + str(ep_no))
                fail_count += 1
                continue

        # Register episode in DB
        ep_id = register_episode(db_drama_id, ep_no, url_720, url_540)
        if ep_id:
            elapsed  = time.time() - ep_start
            done_so_far = success_count + 1
            remaining_eps = len(episodes) - done_so_far
            eta_sec  = (elapsed / done_so_far) * remaining_eps if done_so_far > 0 else 0
            print('    [db] OK id=' + str(ep_id) + ' | ETA: ' + str(round(eta_sec / 60, 1)) + ' min')
            success_count += 1
            done_eps.add(ep_no)
        else:
            print('    FAIL: DB registration failed for EP ' + str(ep_no))
            fail_count += 1

        time.sleep(0.3)

    # 6. Activate drama
    print('')
    print('[5] Activating drama...')
    r = requests.patch(
        API_BASE + '/api/admin/dramas/' + db_drama_id,
        headers=ADMIN_HDR, json={'isActive': True}, timeout=20
    )
    if r.ok:
        print('  Drama ACTIVATED!')
    else:
        print('  Activation warning: ' + str(r.status_code))

    print('')
    print('  DONE: ' + str(success_count) + '/' + str(len(episodes)) + ' success | ' + str(fail_count) + ' failed')
    return True

# ─── MAIN ───────────────────────────────────────────────────────────────────
def main():
    print('=' * 65)
    print('STARDUSTTV BATCH QUEUE — ' + str(len(QUEUE)) + ' dramas')
    print('Temp dir: ' + TEMP_DIR)
    print('=' * 65)

    r2 = get_r2()
    total_start = time.time()

    for idx, item in enumerate(QUEUE, start=1):
        try:
            process_drama(item, r2, idx, len(QUEUE))
        except Exception as e:
            print('')
            print('UNCAUGHT ERROR on ' + item['slug'] + ': ' + str(e))
            import traceback
            traceback.print_exc()

    elapsed = time.time() - total_start
    print('')
    print('=' * 65)
    print('ALL ' + str(len(QUEUE)) + ' DRAMAS IN QUEUE DONE!')
    print('Total time: ' + str(round(elapsed / 60, 1)) + ' minutes')
    print('=' * 65)

if __name__ == '__main__':
    main()
