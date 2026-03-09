"""
Stage 2+3: Download HLS → ffmpeg MP4 faststart → R2 Upload
============================================================
For each drama in dubbed_series_ids.json:
  - Fetch episode list with Indonesian dubbed audio URLs
  - Download HLS stream and convert to MP4 with:
    * libx264 CRF 28 (smaller file, good quality for mobile)
    * -movflags faststart (MP4 ready for streaming)
    * 720p max resolution
  - Upload MP4 + cover to R2
  - Save metadata.json per drama

Run: python download_pipeline.py [--limit N] [--drama-id ID] [--workers N]
Resume-safe: skips already-uploaded episodes.
"""
import sys, json, time, os, re, base64, hashlib, subprocess, tempfile
import requests, concurrent.futures
from pathlib import Path
from cryptography.hazmat.primitives.ciphers import Cipher, algorithms, modes
from cryptography.hazmat.backends import default_backend
import boto3
from botocore.config import Config

sys.stdout.reconfigure(encoding='utf-8', errors='replace')

# ── CONFIG ────────────────────────────────────────────────────────────────────
APP_SECRET  = '8IAcbWyCsVhYv82S2eofRqK1DF3nNDAv'
AES_KEY     = b'2r36789f45q01ae5'
BASE_API    = 'https://api.mydramawave.com/h5-api'
R2_ENDPOINT = 'https://a142d3b29a5d64943cb251157e25eaf3.r2.cloudflarestorage.com'
R2_KEY_ID   = '07c99c897986ea52703c1285308d5e2c'
R2_SECRET   = '44788d376ffb216e1e73784b6fe1ff1423607928898a87c50819b52cdfc12e44'
R2_BUCKET   = 'shortlovers'
R2_PUBLIC   = 'https://stream.shortlovers.id'

# ffmpeg settings — optimized for mobile (small file, fast start)
FFMPEG_OPTS = [
    '-c:v', 'libx264',   # H264 — universally compatible
    '-crf', '28',         # Quality: 23=high, 28=good/smaller, 32=small/ok
    '-preset', 'fast',    # Speed vs compression tradeoff
    '-profile:v', 'baseline',  # Baseline = most compatible for mobile
    '-level', '3.1',
    '-c:a', 'aac',        # AAC audio
    '-b:a', '96k',        # Audio bitrate
    '-ar', '44100',
    '-vf', 'scale=-2:720',  # Max 720p, maintain aspect ratio
    '-movflags', 'faststart',  # ← critical: move moov atom to front
    '-y',                  # Overwrite output
]

FFMPEG_CMD = 'ffmpeg'
WORKERS = 1  # Conservative — avoid rate limiting
TEMP_DIR = Path(tempfile.gettempdir()) / 'freereels_download'
TEMP_DIR.mkdir(exist_ok=True)

# ── AES ───────────────────────────────────────────────────────────────────────
def dec(t):
    try:
        r = base64.b64decode(t); iv, ct = r[:16], r[16:]
        c = Cipher(algorithms.AES(AES_KEY[:16]), modes.CBC(iv), backend=default_backend())
        p = c.decryptor().update(ct) + c.decryptor().finalize()
        return json.loads(p[:-p[-1]].decode())
    except:
        try: return json.loads(t)
        except: return None

# ── API CLIENT ────────────────────────────────────────────────────────────────
class Client:
    def __init__(self):
        self.dh = hashlib.md5(b'freereels_pipeline_v1').hexdigest()
        self.ak = self.ase = None
        self.sess = requests.Session()
        self.sess.headers.update({
            'app-name': 'com.dramawave.h5', 'device': 'h5', 'app-version': '1.2.20',
            'device-id': self.dh, 'device-hash': self.dh,
            'country': 'ID', 'language': 'id', 'shortcode': 'id',
            'User-Agent': 'Mozilla/5.0 (Linux; Android 12)',
        })

    def login(self):
        r = self.sess.post(f'{BASE_API}/anonymous/login', json={'device_id': self.dh},
                           headers={'Content-Type': 'application/json', 'Skip-Encrypt': '1'}, timeout=15)
        d = (dec(r.text) or r.json() or {}).get('data', {})
        self.ak  = d.get('auth_key', '')
        self.ase = d.get('auth_secret', '')
        print(f'[AUTH] key={self.ak[:8]}...')
        return bool(self.ak)

    def _auth(self):
        sig = hashlib.md5(f'{APP_SECRET}&{self.ase}'.encode()).hexdigest()
        return {'authorization': f'oauth_signature={sig},oauth_token={self.ak},ts={int(time.time()*1000)}'}

    def drama_info(self, series_id):
        r = self.sess.get(f'{BASE_API}/drama/info', headers=self._auth(),
                          params={'series_id': series_id}, timeout=20)
        resp = dec(r.text) or {}
        if resp.get('code') not in [200, 0]: return None
        data = resp.get('data', {})
        return data.get('info', data) if isinstance(data, dict) else data

# ── R2 ────────────────────────────────────────────────────────────────────────
def get_r2():
    return boto3.client(
        's3', endpoint_url=R2_ENDPOINT,
        aws_access_key_id=R2_KEY_ID, aws_secret_access_key=R2_SECRET,
        config=Config(signature_version='s3v4'), region_name='auto',
    )

def r2_exists(r2, key):
    try: r2.head_object(Bucket=R2_BUCKET, Key=key); return True
    except: return False

def r2_upload(r2, file_path, key, content_type='video/mp4'):
    with open(file_path, 'rb') as f:
        r2.upload_fileobj(f, R2_BUCKET, key,
                          ExtraArgs={'ContentType': content_type},
                          Config=boto3.s3.transfer.TransferConfig(multipart_threshold=50*1024*1024))
    return f"{R2_PUBLIC}/{key}"

def r2_upload_bytes(r2, data, key, content_type='application/json'):
    r2.put_object(Bucket=R2_BUCKET, Key=key, Body=data, ContentType=content_type)
    return f"{R2_PUBLIC}/{key}"

# ── HELPERS ───────────────────────────────────────────────────────────────────
def safe_folder(title):
    s = re.sub(r'\(Sulih Suara\)', '', title, flags=re.IGNORECASE).strip()
    s = re.sub(r'[^\w\s-]', '', s.lower())
    return re.sub(r'[\s_-]+', '_', s).strip('_')[:50] or 'drama'

def find_indonesian_subtitle(episode):
    for sub in (episode.get('subtitle_list') or []):
        if sub.get('language') == 'id-ID':
            return sub.get('vtt', '') or sub.get('subtitle', '')
    return ''

def has_indo_audio(ep):
    return (
        'id-ID' in ep.get('audio', []) or
        bool(ep.get('external_audio_h264_m3u8', ''))
    )

def download_and_convert_episode(hls_url, out_mp4):
    """Download HLS stream and convert to compressed MP4 with faststart."""
    if not hls_url:
        return False, 'No HLS URL'
    
    cmd = [
        FFMPEG_CMD, '-i', hls_url,
        *FFMPEG_OPTS,
        str(out_mp4)
    ]
    
    try:
        result = subprocess.run(
            cmd, capture_output=True, text=True, timeout=300,
            encoding='utf-8', errors='replace'
        )
        if result.returncode != 0:
            # Try simpler approach if encoding fails
            err_snippet = result.stderr[-300:] if result.stderr else '?'
            # Fallback: copy stream, just add faststart
            cmd2 = [
                FFMPEG_CMD, '-i', hls_url,
                '-c', 'copy', '-movflags', 'faststart', '-y',
                str(out_mp4)
            ]
            result2 = subprocess.run(
                cmd2, capture_output=True, text=True, timeout=300,
                encoding='utf-8', errors='replace'
            )
            if result2.returncode != 0:
                return False, err_snippet
        
        if not out_mp4.exists() or out_mp4.stat().st_size < 10000:
            return False, 'Output file too small or missing'
        
        return True, str(out_mp4.stat().st_size // 1024) + 'KB'
    
    except subprocess.TimeoutExpired:
        return False, 'Timeout (300s)'
    except Exception as e:
        return False, str(e)

def download_cover(url):
    """Download cover image bytes."""
    try:
        r = requests.get(url, timeout=15, headers={'User-Agent': 'Mozilla/5.0'})
        if r.ok: return r.content
    except: pass
    return None

# ── PROCESS ONE DRAMA ─────────────────────────────────────────────────────────
def process_drama(r2, client, series_id, drama_meta, dry_run=False):
    """Download all episodes of a drama, upload to R2, save metadata."""
    title   = drama_meta.get('title', series_id)
    folder  = safe_folder(title)
    prefix  = f'freereels/{folder}'
    meta_key = f'{prefix}/metadata.json'
    
    print(f'\n  Drama: {title}')
    print(f'  Folder: {folder}')
    
    # Fetch full episode list
    info = client.drama_info(series_id)
    if not info:
        print(f'  SKIP: cannot fetch drama info')
        return None
    
    ep_list = info.get('episode_list', [])
    indo_eps = [ep for ep in ep_list if has_indo_audio(ep)]
    
    if not indo_eps:
        print(f'  SKIP: no Indonesian audio episodes')
        return None
    
    print(f'  Episodes with ID audio: {len(indo_eps)}/{len(ep_list)}')
    
    # Upload cover
    cover_key = f'{prefix}/cover.jpg'
    cover_r2  = f'{R2_PUBLIC}/{cover_key}'
    if not dry_run and not r2_exists(r2, cover_key):
        cover_url = info.get('cover', '') or drama_meta.get('cover', '')
        if cover_url:
            img = download_cover(cover_url)
            if img:
                r2_upload_bytes(r2, img, cover_key, 'image/jpeg')
                print(f'  Cover → R2 ✓')
    
    # Process each episode
    episodes_meta = []
    success_eps   = 0
    
    for i, ep in enumerate(indo_eps, 1):
        ep_id  = ep.get('id', f'ep{i}')
        ep_num = ep.get('index', i)
        hls    = ep.get('external_audio_h264_m3u8', '') or ep.get('m3u8_url', '')
        cover  = ep.get('cover', '')
        dur    = ep.get('duration', 0)
        subtitle_vtt = find_indonesian_subtitle(ep)
        
        mp4_key = f'{prefix}/ep_{ep_num:03d}.mp4'
        
        ep_meta = {
            'episode':     ep_num,
            'episodeId':   ep_id,
            'title':       f'Episode {ep_num}',
            'cover':       f'{R2_PUBLIC}/{prefix}/ep_{ep_num:03d}_thumb.jpg',
            'duration':    dur,
            'hlsSource':   hls,
            'videoUrl':    f'{R2_PUBLIC}/{mp4_key}',
            'subtitleVtt': subtitle_vtt,
            'free':        ep.get('video_type') == 'free',
            'uploaded':    False,
        }
        
        if dry_run:
            ep_meta['uploaded'] = True
            success_eps += 1
            episodes_meta.append(ep_meta)
            continue
        
        # Skip if already exists in R2
        if r2_exists(r2, mp4_key):
            ep_meta['uploaded'] = True
            success_eps += 1
            episodes_meta.append(ep_meta)
            print(f'  [{i:03d}/{len(indo_eps)}] ep{ep_num:03d} — already in R2, skip')
            continue
        
        if not hls:
            print(f'  [{i:03d}/{len(indo_eps)}] ep{ep_num:03d} — no HLS URL, skip')
            episodes_meta.append(ep_meta)
            continue
        
        # Download episode thumbnail
        thumb_key = f'{prefix}/ep_{ep_num:03d}_thumb.jpg'
        if cover and not r2_exists(r2, thumb_key):
            thumb = download_cover(cover)
            if thumb:
                r2_upload_bytes(r2, thumb, thumb_key, 'image/jpeg')
        
        # Download + convert HLS → MP4
        out_mp4 = TEMP_DIR / f'{folder}_ep{ep_num:03d}.mp4'
        ok, info_msg = download_and_convert_episode(hls, out_mp4)
        
        if ok:
            # Upload to R2
            url = r2_upload(r2, out_mp4, mp4_key, 'video/mp4')
            ep_meta['uploaded'] = True
            ep_meta['videoUrl'] = url
            success_eps += 1
            size_mb = out_mp4.stat().st_size / 1024 / 1024
            print(f'  [{i:03d}/{len(indo_eps)}] ep{ep_num:03d} ✓ {size_mb:.1f}MB → R2')
            # Clean up temp
            try: out_mp4.unlink()
            except: pass
        else:
            print(f'  [{i:03d}/{len(indo_eps)}] ep{ep_num:03d} ✗ {info_msg}')
        
        episodes_meta.append(ep_meta)
        time.sleep(0.5)  # Rate limit
    
    # Build drama metadata
    genres = drama_meta.get('genres', info.get('series_tag', []))
    metadata = {
        'source':        'freereels_dubbed',
        'series_id':     series_id,
        'title':         title,
        'titleClean':    re.sub(r'\(Sulih Suara\)', '', title, flags=re.IGNORECASE).strip(),
        'description':   info.get('desc', drama_meta.get('desc', '')),
        'cover':         cover_r2,
        'genres':        genres,
        'tags':          drama_meta.get('tags', info.get('tag', [])),
        'content_tags':  info.get('content_tags', drama_meta.get('content_tags', [])),
        'totalEpisodes': len(indo_eps),
        'uploadedEpisodes': success_eps,
        'status':        'complete' if info.get('finish_status') == 2 else 'ongoing',
        'language':      'Indonesia',
        'audioLanguage': 'id-ID',
        'country':       'China',
        'viewCount':     info.get('view_count', 0),
        'episodes':      episodes_meta,
        'r2Folder':      prefix,
        'scrapedAt':     int(time.time()),
        'imported':      False,  # Will be set to True after DB import
    }
    
    # Save metadata to R2
    if not dry_run:
        r2_upload_bytes(
            r2,
            json.dumps(metadata, ensure_ascii=False, indent=2).encode(),
            meta_key, 'application/json'
        )
        print(f'  Metadata → R2 ✓ ({success_eps}/{len(indo_eps)} eps uploaded)')
    else:
        print(f'  [DRY-RUN] {success_eps}/{len(indo_eps)} eps would be processed')
    
    return metadata

# ── MAIN ──────────────────────────────────────────────────────────────────────
def main():
    import argparse
    p = argparse.ArgumentParser(description='FreeReels Download + R2 Upload Pipeline')
    p.add_argument('--limit',    type=int, help='Max dramas to process')
    p.add_argument('--drama-id', help='Single drama series_id to process')
    p.add_argument('--test',     action='store_true', help='Dry run')
    p.add_argument('--ep-limit', type=int, default=0, help='Max episodes per drama (0=all)')
    a = p.parse_args()

    print('═'*55)
    print('  FreeReels Indonesian Dubbed — Download Pipeline')
    print('═'*55)
    print(f'  Mode: {"DRY-RUN" if a.test else "PRODUCTION"}')
    print(f'  ffmpeg: {FFMPEG_CMD}')

    # Load drama list
    ids_file = Path('dubbed_series_ids.json')
    if not ids_file.exists():
        print(f'\n[ERROR] {ids_file} not found. Run discover_dramas.py first.')
        sys.exit(1)

    with open(ids_file, encoding='utf-8') as f:
        all_dramas = json.load(f)
    
    if a.drama_id:
        target = {a.drama_id: all_dramas.get(a.drama_id, {'title': a.drama_id})}
    else:
        target = all_dramas
    
    if a.limit:
        items = list(target.items())[:a.limit]
        target = dict(items)
    
    print(f'\n  Total dramas: {len(target)}')
    print(f'  Source: {ids_file}')
    
    # Auth + R2
    client = Client()
    if not client.login():
        print('[ERROR] Login failed'); sys.exit(1)

    r2 = None if a.test else get_r2()

    # Process
    results  = []
    ok = skip = fail = 0

    for i, (sid, meta) in enumerate(target.items(), 1):
        print(f'\n[{i}/{len(target)}] {sid}')
        try:
            res = process_drama(r2, client, sid, meta, dry_run=a.test)
            if res:
                ok += 1
                results.append({'series_id': sid, 'title': res['title'],
                                 'uploaded': res['uploadedEpisodes'],
                                 'total': res['totalEpisodes']})
            else:
                skip += 1
        except Exception as e:
            import traceback; traceback.print_exc()
            fail += 1
        
        # Re-auth every 30 dramas to avoid token expiry
        if i % 30 == 0:
            client.login()

    print(f'\n{"═"*55}')
    print(f'  ✓ Processed: {ok}  ⊘ Skipped: {skip}  ✗ Failed: {fail}')
    with open('pipeline_results.json', 'w', encoding='utf-8') as f:
        json.dump(results, f, ensure_ascii=False, indent=2)
    print(f'Results → pipeline_results.json')

if __name__ == '__main__':
    main()
