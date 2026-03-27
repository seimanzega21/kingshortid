"""
FreeReels — Full Episode Scraper (All Episodes)
================================================
Estrategi: Parse __NUXT_DATA__ dari m.mydramawave.com/series/{series_key}
untuk mendapatkan semua episode dengan HLS URL lengkap.

Usage:
  python freereels_full_eps.py --run              # Scrape semua episode drama yang ada di R2
  python freereels_full_eps.py --run --limit 5    # Test 5 drama dulu
  python freereels_full_eps.py --series KEY       # Satu drama spesifik
"""
import sys, json, time, os, re, subprocess, argparse, hashlib
import requests, psycopg2, urllib.request
from pathlib import Path
import boto3
from botocore.config import Config

sys.stdout.reconfigure(encoding='utf-8', errors='replace')

# ── CONFIG ────────────────────────────────────────────────────────────────────
H5_BASE     = 'https://m.mydramawave.com'
APP_SECRET  = '8IAcbWyCsVhYv82S2eofRqK1DF3nNDAv'
FR_BASE     = 'https://apiv2.free-reels.com/frv2-api'

R2_ENDPOINT = 'https://a142d3b29a5d64943cb251157e25eaf3.r2.cloudflarestorage.com'
R2_KEY_ID   = '07c99c897986ea52703c1285308d5e2c'
R2_SECRET   = '44788d376ffb216e1e73784b6fe1ff1423607928898a87c50819b52cdfc12e44'
R2_BUCKET   = 'shortlovers'
R2_PUBLIC   = 'https://stream.shortlovers.id'

DATABASE_URL = 'postgresql://postgres:seiman21@localhost:5432/kingshort'
TEMP_DIR     = Path(os.environ.get('TEMP', '/tmp')) / 'fr_eps_dl'
TEMP_DIR.mkdir(exist_ok=True)

# VIP auth credentials from user's browser session (Facebook login)
VIP_AUTH_PARAMS = (
    '%7B%22auth_key%22%3A%220mbsk7VVLt3JLNTqtC1EnJoK0pQAA3pW%22%2C'
    '%22auth_secret%22%3A%22DjRzZ0PoETLc8K9nq1N89pX2dtvuspc3%22%2C'
    '%22name%22%3A%22Seiman%20Zega%22%2C'
    '%22user_id%22%3A36848605951%2C'
    '%22user_type%22%3A1%7D'
)

# Browser-like headers for scraping H5 page (with VIP session cookie)
H5_HEADERS = {
    'User-Agent': ('Mozilla/5.0 (Linux; Android 11; Mobile) '
                   'AppleWebKit/537.36 (KHTML, like Gecko) '
                   'Chrome/120.0.0.0 Mobile Safari/537.36'),
    'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
    'Accept-Language': 'id-ID,id;q=0.9,en-US;q=0.8',
    'Referer': 'https://m.mydramawave.com/',
    'Cookie': f'auth_params={VIP_AUTH_PARAMS}',
}

FFMPEG_OPTS = [
    '-c:v', 'libx264', '-crf', '26', '-preset', 'fast',
    '-profile:v', 'baseline', '-level', '3.1',
    '-c:a', 'aac', '-b:a', '96k', '-ar', '44100',
    '-vf', 'scale=-2:min(720\\,ih)',
    '-movflags', 'faststart', '-y'
]

# ── R2 ────────────────────────────────────────────────────────────────────────
def get_r2():
    return boto3.client('s3', endpoint_url=R2_ENDPOINT,
                        aws_access_key_id=R2_KEY_ID, aws_secret_access_key=R2_SECRET,
                        config=Config(signature_version='s3v4'), region_name='auto')

def r2_exists(r2c, key):
    try: r2c.head_object(Bucket=R2_BUCKET, Key=key); return True
    except: return False

def r2_upload_file(r2c, path, key):
    with open(path, 'rb') as f:
        r2c.upload_fileobj(f, R2_BUCKET, key,
                           ExtraArgs={'ContentType': 'video/mp4'},
                           Config=boto3.s3.transfer.TransferConfig(
                               multipart_threshold=30*1024*1024,
                               multipart_chunksize=10*1024*1024))
    return f'{R2_PUBLIC}/{key}'

def r2_upload_bytes(r2c, data, key, ct='application/json'):
    r2c.put_object(Bucket=R2_BUCKET, Key=key, Body=data, ContentType=ct)
    return f'{R2_PUBLIC}/{key}'

# ── Parse Episode List from H5 Page ──────────────────────────────────────────
def fetch_episode_list(series_key: str) -> list:
    """
    Fetch all episodes for a drama from m.mydramawave.com/series/{key}.
    Strategy:
      1. Find the series dict in __NUXT_DATA__ that has 'episode_list'.
      2. Follow episode_list (int ref) -> list of episode indices.
      3. For each episode index, resolve each field 1 level (int -> flat[int]).
      4. Fallback: walk all dicts looking for video fields.
      5. Fallback: regex for HLS URLs in HTML.
    Returns list: [{'index', 'ep_key', 'hls', 'duration', 'sub_vtt', 'sub_srt', 'free'}]
    """
    url = f'{H5_BASE}/series/{series_key}'
    try:
        r = requests.get(url, headers=H5_HEADERS, timeout=25, allow_redirects=True)
        html = r.text
    except Exception as e:
        print(f'  HTTP error: {e}')
        return []

    # Extract __NUXT_DATA__
    nuxt_raw = None
    m = re.search(r'<script[^>]*id="__NUXT_DATA__"[^>]*>(.*?)</script>', html, re.DOTALL)
    if m:
        nuxt_raw = m.group(1).strip()

    episodes = {}

    if nuxt_raw:
        try:
            flat = json.loads(nuxt_raw)

            def r1(val):
                """Resolve one level: if val is int in range, return flat[val], else val."""
                if isinstance(val, int) and 0 <= val < len(flat):
                    return flat[val]
                return val

            def rstr(val):
                """Resolve val to string if possible (follow int refs until string)."""
                for _ in range(10):
                    if isinstance(val, str): return val
                    if isinstance(val, int) and 0 <= val < len(flat):
                        val = flat[val]
                    else:
                        return None
                return val if isinstance(val, str) else None

            def rint(val):
                """Resolve val to a small positive int (episode number 1-999).
                Values in flat array that look like episode numbers should be
                resolved via r1() first, since episode_number field raw value
                is an array index pointing to the actual episode number."""
                # Always try one level of resolution first
                resolved = r1(val)
                # If resolved is a small int (1-999), it's the episode number
                if isinstance(resolved, int) and 1 <= resolved <= 999:
                    return resolved
                # Try original val as small int
                if isinstance(val, int) and 1 <= val <= 999:
                    return val
                # Try string conversion
                if isinstance(resolved, str):
                    try: return int(resolved)
                    except: pass
                return None


            # Strategy A: Find series dict with episode_list
            for i, item in enumerate(flat):
                if not isinstance(item, dict): continue
                if 'episode_list' not in item: continue

                ep_list_ref = item['episode_list']
                ep_list = r1(ep_list_ref)
                if not isinstance(ep_list, list):
                    ep_list = r1(ep_list)  # two levels
                if not isinstance(ep_list, list):
                    continue

                for ep_ref in ep_list:
                    ep_dict = r1(ep_ref)
                    if not isinstance(ep_dict, dict):
                        continue

                    # Resolve episode_number / index field
                    ep_num = None
                    for fn in ['episode_number', 'index', 'ep_num']:
                        raw = ep_dict.get(fn)
                        if raw is None: continue
                        resolved = rint(raw)
                        if isinstance(resolved, int) and 1 <= resolved <= 999:
                            ep_num = resolved
                            break

                    # Resolve HLS URL
                    hls = ''
                    for fn in ['external_audio_h264_m3u8', 'm3u8_url', 'video_url', 'play_url']:
                        raw = ep_dict.get(fn)
                        if raw is None: continue
                        resolved = rstr(raw)
                        if isinstance(resolved, str) and resolved.startswith('http'):
                            hls = resolved
                            break

                    # Resolve subtitles
                    sub_vtt = sub_srt = ''
                    subtitle_list_raw = ep_dict.get('subtitle_list')
                    sub_list = r1(subtitle_list_raw) if subtitle_list_raw is not None else []
                    if isinstance(sub_list, list):
                        for sub_ref in sub_list:
                            sub_item = r1(sub_ref)
                            if not isinstance(sub_item, dict): continue
                            lang = rstr(sub_item.get('language', ''))
                            if lang == 'id-ID':
                                sub_vtt = rstr(sub_item.get('vtt', '')) or ''
                                sub_srt = rstr(sub_item.get('subtitle', '')) or ''
                                break

                    # ep_key
                    ep_key = rstr(ep_dict.get('id', '')) or ''

                    # free/paid
                    vtype_raw = ep_dict.get('video_type')
                    vtype = rstr(vtype_raw) or ''
                    is_free = (vtype == 'free')

                    if ep_num and hls and ep_num not in episodes:
                        episodes[ep_num] = {
                            'index':    ep_num,
                            'ep_key':   ep_key,
                            'hls':      hls,
                            'duration': rint(ep_dict.get('duration', 0)) or 0,
                            'sub_vtt':  sub_vtt,
                            'sub_srt':  sub_srt,
                            'free':     is_free,
                        }

                if episodes:
                    break  # found episodes from this series dict, done

        except Exception as e:
            print(f'  NUXT parse error: {e}')

    # Strategy B: regex HLS extraction fallback
    if not episodes:
        hls_urls = re.findall(r'https://video-[^\"\'\\\s]+\.m3u8(?:[^\"\'\\\s]*)?', html)
        seen_hls = set()
        idx = 1
        for h in hls_urls:
            if h in seen_hls: continue
            seen_hls.add(h)
            sub = ''
            h_pos = html.find(h)
            if h_pos > 0:
                nearby = html[max(0, h_pos-500):h_pos+500]
                sm = re.search(r'https://[^\"\'\\\s]+id-ID[^\"\'\\\s]*\.(?:srt|vtt)', nearby)
                if sm: sub = sm.group(0)
            episodes[idx] = {
                'index': idx, 'ep_key': '', 'hls': h,
                'duration': 0, 'sub_vtt': '', 'sub_srt': sub, 'free': True,
            }
            idx += 1

    result = sorted(episodes.values(), key=lambda x: x['index'])
    return result

# ── Helpers ───────────────────────────────────────────────────────────────────
def safe_folder(title):
    s = re.sub(r'\((?:Sulih Suara|Dubbed?|Dubbing)\)', '', title, flags=re.IGNORECASE).strip()
    s = re.sub(r'[^\w\s-]', '', s.lower())
    return re.sub(r'[\s_-]+', '_', s).strip('_')[:50] or 'drama'

def ffmpeg_convert(hls_url, out_mp4):
    if not hls_url: return False, 'no URL'
    cmd = ['ffmpeg', '-i', hls_url, *FFMPEG_OPTS, str(out_mp4)]
    try:
        res = subprocess.run(cmd, capture_output=True, timeout=360,
                             encoding='utf-8', errors='replace')
        if res.returncode != 0 or not out_mp4.exists() or out_mp4.stat().st_size < 5000:
            out_mp4.unlink(missing_ok=True)
            cmd2 = ['ffmpeg', '-i', hls_url, '-c', 'copy',
                    '-movflags', 'faststart', '-y', str(out_mp4)]
            res2 = subprocess.run(cmd2, capture_output=True, timeout=360,
                                  encoding='utf-8', errors='replace')
            if res2.returncode != 0 or not out_mp4.exists() or out_mp4.stat().st_size < 5000:
                return False, res.stderr[-120:]
        return True, f'{out_mp4.stat().st_size // 1024}KB'
    except subprocess.TimeoutExpired: return False, 'timeout'
    except Exception as e: return False, str(e)

# ── List dramas from R2 ───────────────────────────────────────────────────────
def list_r2_dramas(r2c) -> list:
    files, token = [], None
    while True:
        kw = {'Bucket': R2_BUCKET, 'Prefix': 'freereels/', 'MaxKeys': 1000}
        if token: kw['ContinuationToken'] = token
        resp = r2c.list_objects_v2(**kw)
        files += [o['Key'] for o in resp.get('Contents', [])
                  if o['Key'].endswith('/metadata.json')]
        token = resp.get('NextContinuationToken')
        if not token: break
    return files

# ── Main: Process a single drama ─────────────────────────────────────────────
def process_drama(r2c, meta: dict) -> dict:
    """Download all missing episodes for one drama. Returns stats dict."""
    series_key    = meta.get('series_key', '')
    title         = meta.get('title', series_key)
    total_eps     = meta.get('totalEpisodes', 1)
    prefix        = meta.get('r2Folder', f'freereels/{safe_folder(title)}')
    already_done  = {e['episode'] for e in meta.get('episodes', []) if e.get('uploaded')}

    print(f'\n  Series: {series_key} | {title[:40]}')
    print(f'  Total ep: {total_eps} | Ya di R2: {len(already_done)}')

    if len(already_done) >= total_eps:
        print(f'  ✓ Semua episode sudah lengkap!')
        return {'ok': 0, 'skip': total_eps, 'fail': 0}

    # Fetch episode list from H5 page
    print(f'  🌐 Fetching episode list dari web...', end=' ', flush=True)
    eps_list = fetch_episode_list(series_key)
    if not eps_list:
        print(f'✗ Tidak bisa fetch episode list')
        return {'ok': 0, 'skip': 0, 'fail': 1}
    print(f'✓ {len(eps_list)} episodes ditemukan')

    ok = skip = fail = 0
    new_episodes  = list(meta.get('episodes', []))  # existing episodes from metadata
    existing_nums = {e['episode'] for e in new_episodes}

    for ep in eps_list:
        ep_num = ep['index']
        if ep_num == 0: continue  # skip invalid
        hls    = ep['hls']

        if ep_num in already_done:
            skip += 1
            continue

        mp4_key = f'{prefix}/ep_{ep_num:03d}.mp4'
        if r2_exists(r2c, mp4_key):
            # Already uploaded but not in metadata — add it
            if ep_num not in existing_nums:
                new_episodes.append({
                    'episode':    ep_num,
                    'title':      f'Episode {ep_num}',
                    'duration':   ep['duration'],
                    'videoUrl':   f'{R2_PUBLIC}/{mp4_key}',
                    'subtitleVtt': ep['sub_vtt'],
                    'subtitleSrt': ep['sub_srt'],
                    'uploaded':   True,
                    'free':       ep['free'],
                })
                existing_nums.add(ep_num)
            skip += 1
            continue

        # Compress + upload
        folder_name = prefix.split('/')[-1]
        out = TEMP_DIR / f'{folder_name}_ep{ep_num:03d}.mp4'
        out.unlink(missing_ok=True)

        print(f'    ep{ep_num:03d} compress...', end=' ', flush=True)
        ok2, msg = ffmpeg_convert(hls, out)
        if not ok2:
            print(f'✗ {msg[:60]}')
            fail += 1
            continue

        size_mb = out.stat().st_size / 1024 / 1024
        print(f'✓ {size_mb:.1f}MB  upload...', end=' ', flush=True)
        r2_upload_file(r2c, out, mp4_key)
        print(f'✓')
        try: out.unlink()
        except: pass

        new_episodes.append({
            'episode':    ep_num,
            'title':      f'Episode {ep_num}',
            'duration':   ep['duration'],
            'videoUrl':   f'{R2_PUBLIC}/{mp4_key}',
            'subtitleVtt': ep['sub_vtt'],
            'subtitleSrt': ep['sub_srt'],
            'uploaded':   True,
            'free':       ep['free'],
        })
        existing_nums.add(ep_num)
        ok += 1
        time.sleep(0.2)

    # Update metadata.json in R2
    new_meta = dict(meta)
    new_meta['episodes']         = sorted(new_episodes, key=lambda x: x['episode'])
    new_meta['uploadedEpisodes'] = len([e for e in new_meta['episodes'] if e.get('uploaded')])
    meta_key = f'{prefix}/metadata.json'
    r2_upload_bytes(r2c, json.dumps(new_meta, ensure_ascii=False, indent=2).encode(), meta_key)
    print(f'  📋 Metadata diperbarui ({new_meta["uploadedEpisodes"]}/{total_eps} eps) ✓')

    return {'ok': ok, 'skip': skip, 'fail': fail}

# ── Update DB episodes ────────────────────────────────────────────────────────
def update_db_episodes(meta: dict):
    """Insert missing episodes into PostgreSQL."""
    series_key = meta.get('series_key', '')
    episodes   = [e for e in meta.get('episodes', []) if e.get('uploaded') and e.get('videoUrl')]
    if not episodes: return

    try:
        conn = psycopg2.connect(DATABASE_URL)
        conn.autocommit = False
        cur  = conn.cursor()

        cur.execute('SELECT id FROM "Drama" WHERE description LIKE %s LIMIT 1',
                    (f'%[FRkey:{series_key}]%',))
        row = cur.fetchone()
        if not row:
            conn.close()
            return

        drama_id = row[0]
        added = 0
        for ep in episodes:
            ep_num = ep.get('episode', 0)
            cur.execute('SELECT id FROM "Episode" WHERE "dramaId"=%s AND "episodeNumber"=%s',
                        (drama_id, ep_num))
            if cur.fetchone(): continue

            cur.execute("""
                INSERT INTO "Episode" (
                    id, "dramaId", "episodeNumber", title, description,
                    thumbnail, "videoUrl", duration,
                    "isVip", "coinPrice", views, "isActive", "releaseDate",
                    "createdAt", "updatedAt"
                ) VALUES (
                    gen_random_uuid(), %s, %s, %s, '',
                    %s, %s, %s,
                    false, 0, 0, false, NOW(),
                    NOW(), NOW()
                ) RETURNING id
            """, (drama_id, ep_num, ep.get('title', f'Episode {ep_num}'),
                  meta.get('cover', ''), ep.get('videoUrl', ''), ep.get('duration', 0)))
            ep_id = cur.fetchone()[0]
            added += 1

            sub = ep.get('subtitleVtt') or ep.get('subtitleSrt') or ''
            if sub:
                cur.execute('SELECT id FROM "Subtitle" WHERE "episodeId"=%s LIMIT 1', (ep_id,))
                if not cur.fetchone():
                    cur.execute("""
                        INSERT INTO "Subtitle"
                            (id, "episodeId", language, label, url, "isDefault", "createdAt")
                        VALUES
                            (gen_random_uuid(), %s, 'id', 'Bahasa Indonesia', %s, true, NOW())
                    """, (ep_id, sub))

        # Update totalEpisodes in Drama
        cur.execute('UPDATE "Drama" SET "totalEpisodes"=%s, "updatedAt"=NOW() WHERE id=%s',
                    (meta.get('uploadedEpisodes', 1), drama_id))

        conn.commit()
        if added:
            print(f'  🗄️  DB +{added} episode(s) ✓')
        cur.close(); conn.close()

    except Exception as e:
        print(f'  DB ERROR: {e}')

# ── MAIN ──────────────────────────────────────────────────────────────────────
def main():
    p = argparse.ArgumentParser(description='FreeReels — Scrape All Episodes')
    p.add_argument('--run',    action='store_true', help='Scrape semua episode dari dramas di R2')
    p.add_argument('--series', type=str, default=None, help='Process 1 drama spesifik (series key)')
    p.add_argument('--limit',  type=int, default=None, help='Batasi jumlah drama')
    p.add_argument('--test',   action='store_true', help='Test parse H5 page only (no download)')
    a = p.parse_args()

    if not any([a.run, a.series, a.test]):
        p.print_help(); return

    print('═' * 55)
    print('  FreeReels — Full Episode Scraper')
    print('═' * 55)

    r2c = get_r2()

    # Test mode: just parse one drama
    if a.test or a.series:
        key = a.series or 'qQKGMS5WbW'
        print(f'\nTest parse: {H5_BASE}/series/{key}')
        eps = fetch_episode_list(key)
        print(f'Found {len(eps)} episodes')
        for ep in eps[:5]:
            print(f'  ep{ep["index"]:03d}: hls={ep["hls"][:60]}...')
            print(f'         sub_id={ep["sub_vtt"][:50] if ep["sub_vtt"] else "(none)"}')
        if not a.run: return

    # List all dramas from R2
    meta_keys = list_r2_dramas(r2c)
    print(f'\nDrama di R2: {len(meta_keys)}')

    if a.limit:
        meta_keys = meta_keys[:a.limit]

    total_ok = total_skip = total_fail = 0

    for i, mkey in enumerate(meta_keys, 1):
        obj  = r2c.get_object(Bucket=R2_BUCKET, Key=mkey)
        meta = json.loads(obj['Body'].read().decode('utf-8'))

        print(f'\n[{i:02d}/{len(meta_keys)}] {meta.get("title", "?")[:50]}')
        stats = process_drama(r2c, meta)

        # Update DB with new episodes
        if stats['ok'] > 0:
            update_db_episodes(meta)

        total_ok   += stats['ok']
        total_skip += stats['skip']
        total_fail += stats['fail']
        time.sleep(0.5)

    print(f'\n{"="*55}')
    print(f'✓ Episode baru: {total_ok}')
    print(f'⊘ Sudah ada:    {total_skip}')
    print(f'✗ Gagal:        {total_fail}')

if __name__ == '__main__':
    main()
