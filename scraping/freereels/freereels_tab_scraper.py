"""
FreeReels Tab-514 Full Pipeline — Indonesian Dubbed
=====================================================
Features:
  - Auto-collect drama dari tab 514 (Indonesian audio only)
  - Auto-translate judul + deskripsi ke Bahasa Indonesia (MyMemory API)
  - Compress video HLS → MP4 via ffmpeg
  - Upload cover, MP4, metadata.json ke Cloudflare R2
  - Import ke PostgreSQL dengan status isActive=False (pending)

Usage:
  python freereels_tab_scraper.py --collect            # Stage 1: Collect drama list
  python freereels_tab_scraper.py --download           # Stage 2: Compress + Upload to R2
  python freereels_tab_scraper.py --import-db          # Stage 3: Import to DB (pending)
  python freereels_tab_scraper.py --all                # Jalankan semua stage
  python freereels_tab_scraper.py --status             # Cek status R2
  python freereels_tab_scraper.py --limit 10           # Batasi jumlah download
"""
import sys, json, time, os, re, hashlib, subprocess, argparse
import requests, psycopg2, urllib.request
from pathlib import Path
import boto3
from botocore.config import Config

sys.stdout.reconfigure(encoding='utf-8', errors='replace')

# ── CONFIG ────────────────────────────────────────────────────────────────────
APP_SECRET  = '8IAcbWyCsVhYv82S2eofRqK1DF3nNDAv'
FR_BASE     = 'https://apiv2.free-reels.com/frv2-api'

R2_ENDPOINT = 'https://a142d3b29a5d64943cb251157e25eaf3.r2.cloudflarestorage.com'
R2_KEY_ID   = '07c99c897986ea52703c1285308d5e2c'
R2_SECRET   = '44788d376ffb216e1e73784b6fe1ff1423607928898a87c50819b52cdfc12e44'
R2_BUCKET   = 'shortlovers'
R2_PUBLIC   = 'https://stream.shortlovers.id'

DATABASE_URL  = 'postgresql://postgres:seiman21@localhost:5432/kingshort'
TAB_DATA_FILE = Path('tab514_all_dramas.json')
TEMP_DIR      = Path(os.environ.get('TEMP', '/tmp')) / 'fr_tab_dl'
TEMP_DIR.mkdir(exist_ok=True)

# ffmpeg — compress ke H.264/AAC, cap 720p, mobile-optimized
FFMPEG_OPTS = [
    '-c:v', 'libx264', '-crf', '26', '-preset', 'fast',
    '-profile:v', 'baseline', '-level', '3.1',
    '-c:a', 'aac', '-b:a', '96k', '-ar', '44100',
    '-vf', 'scale=-2:min(720\\,ih)',
    '-movflags', 'faststart', '-y'
]

GENRES_MAP = {
    'Drama': 'Drama', 'Romance': 'Romance', 'Romantis': 'Romance',
    'Bisnis': 'Business', 'Business': 'Business', 'Aksi': 'Action',
    'Komedi': 'Comedy', 'Comedy': 'Comedy', 'Thriller': 'Thriller',
    'Misteri': 'Mystery', 'Mystery': 'Mystery', 'Fantasi': 'Fantasy',
    'Fantasy': 'Fantasy', 'Sejarah': 'Historical', 'Historical': 'Historical',
    'Kampus': 'School', 'School': 'School', 'Keluarga': 'Family',
    'Balas Dendam': 'Revenge', 'Revenge': 'Revenge',
    'Kontemporer': 'Contemporary', 'Contemporary': 'Contemporary',
    'Medical Drama': 'Medical', 'Period Drama': 'Historical',
    'Strong Female Lead': 'Strong Female Lead', 'Action': 'Action',
}

# ── Translation ───────────────────────────────────────────────────────────────
_trans_cache: dict = {}

def translate_to_id(text: str) -> str:
    """Translate text to Bahasa Indonesia via MyMemory (free, no key)."""
    if not text or not text.strip():
        return text
    # Already Indonesian? (simple check for common ID words)
    id_indicators = ['yang', 'dan', 'adalah', 'untuk', 'dengan', 'dalam',
                     'kepada', 'tidak', 'dia', 'mereka', 'itu', 'ini']
    words = text.lower().split()
    if sum(1 for w in words if w in id_indicators) >= 2:
        return text  # sudah Indonesia

    if text in _trans_cache:
        return _trans_cache[text]

    # Chunk text if too long (MyMemory limit ~500 chars per request)
    def _translate_chunk(chunk):
        try:
            url = 'https://api.mymemory.translated.net/get'
            r = requests.get(url, params={
                'q': chunk, 'langpair': 'en|id', 'de': 'scraper@kingshort.id'
            }, timeout=10)
            d = r.json() if r.ok else {}
            result = d.get('responseData', {}).get('translatedText', '')
            # MyMemory sometimes returns the original if quota exceeded
            if result and result.upper() != chunk.upper():
                return result
            return chunk
        except Exception:
            return chunk

    if len(text) <= 450:
        result = _translate_chunk(text)
    else:
        # Split by sentences
        sentences = re.split(r'(?<=[.!?])\s+', text)
        chunks, current = [], ''
        for s in sentences:
            if len(current) + len(s) < 450:
                current = (current + ' ' + s).strip()
            else:
                chunks.append(current)
                current = s
        if current:
            chunks.append(current)
        result = ' '.join(_translate_chunk(c) for c in chunks if c)
        time.sleep(0.3)

    _trans_cache[text] = result
    return result

def clean_title_id(title: str) -> str:
    """Remove (Dubbed)/(Sulih Suara) from title then translate."""
    clean = re.sub(r'\s*\((?:Dubbed?|Dubbing|Sulih Suara)\)', '', title, flags=re.IGNORECASE).strip()
    return translate_to_id(clean)

# ── Auth ──────────────────────────────────────────────────────────────────────
class FRClient:
    def __init__(self):
        self.dh   = hashlib.md5(b'freereels_tab_scraper_v2').hexdigest()
        self.ak   = self.ase = None
        self.sess = requests.Session()
        self.sess.headers.update({
            'app-name': 'com.freereels.app', 'device': 'android',
            'app-version': '2.2.10', 'device-id': self.dh, 'device-hash': self.dh,
            'country': 'ID', 'language': 'id', 'shortcode': 'id',
            'User-Agent': 'okhttp/4.12.0',
        })

    def login(self):
        r = self.sess.post(f'{FR_BASE}/anonymous/login', json={'device_id': self.dh},
                           headers={'Content-Type': 'application/json', 'Skip-Encrypt': '1'}, timeout=15)
        d = (r.json() if r.ok else {}).get('data', {})
        self.ak  = d.get('auth_key', '')
        self.ase = d.get('auth_secret', '')
        ok = bool(self.ak)
        print(f'[AUTH] {"OK key=" + self.ak[:8] + "..." if ok else "FAILED"}')
        return ok

    def _ah(self):
        sig = hashlib.md5(f'{APP_SECRET}&{self.ase}'.encode()).hexdigest()
        return {'authorization': f'oauth_signature={sig},oauth_token={self.ak},ts={int(time.time()*1000)}'}

    def tab_feed(self, page=1, page_size=20):
        r = self.sess.post(f'{FR_BASE}/homepage/v2/tab/feed',
                           json={'tab_key': '514', 'module_key': '514',
                                 'page': page, 'page_size': page_size},
                           headers={**self._ah(), 'Content-Type': 'application/json',
                                    'Skip-Encrypt': '1'},
                           timeout=15)
        resp = r.json() if r.ok else {}
        if resp.get('code') in [200, 0]:
            data = resp.get('data', {})
            return data.get('items') or data.get('list', [])
        return []

# ── R2 ────────────────────────────────────────────────────────────────────────
def get_r2():
    return boto3.client('s3', endpoint_url=R2_ENDPOINT,
                        aws_access_key_id=R2_KEY_ID, aws_secret_access_key=R2_SECRET,
                        config=Config(signature_version='s3v4'), region_name='auto')

def r2_exists(r2c, key):
    try: r2c.head_object(Bucket=R2_BUCKET, Key=key); return True
    except: return False

def r2_upload_file(r2c, path, key):
    size = Path(path).stat().st_size
    transfer_cfg = boto3.s3.transfer.TransferConfig(
        multipart_threshold=30 * 1024 * 1024,
        multipart_chunksize=10 * 1024 * 1024,
    )
    with open(path, 'rb') as f:
        r2c.upload_fileobj(f, R2_BUCKET, key,
                           ExtraArgs={'ContentType': 'video/mp4'},
                           Config=transfer_cfg)
    return f'{R2_PUBLIC}/{key}'

def r2_upload_bytes(r2c, data, key, ct='application/json'):
    r2c.put_object(Bucket=R2_BUCKET, Key=key, Body=data, ContentType=ct)
    return f'{R2_PUBLIC}/{key}'

# ── Helpers ───────────────────────────────────────────────────────────────────
def safe_folder(title):
    s = re.sub(r'\((?:Sulih Suara|Dubbed?|Dubbing)\)', '', title, flags=re.IGNORECASE).strip()
    s = re.sub(r'[^\w\s-]', '', s.lower())
    return re.sub(r'[\s_-]+', '_', s).strip('_')[:50] or 'drama'

def dl_bytes(url):
    if not url: return None
    try:
        req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0'})
        with urllib.request.urlopen(req, timeout=20) as f: return f.read()
    except: return None

def ffmpeg_convert(hls_url, out_mp4):
    if not hls_url: return False, 'no URL'
    cmd = ['ffmpeg', '-i', hls_url, *FFMPEG_OPTS, str(out_mp4)]
    try:
        res = subprocess.run(cmd, capture_output=True, timeout=360,
                             encoding='utf-8', errors='replace')
        if res.returncode != 0 or not out_mp4.exists() or out_mp4.stat().st_size < 5000:
            # Fallback: stream copy only
            out_mp4.unlink(missing_ok=True)
            cmd2 = ['ffmpeg', '-i', hls_url, '-c', 'copy',
                    '-movflags', 'faststart', '-y', str(out_mp4)]
            res2 = subprocess.run(cmd2, capture_output=True, timeout=360,
                                  encoding='utf-8', errors='replace')
            if res2.returncode != 0 or not out_mp4.exists() or out_mp4.stat().st_size < 5000:
                return False, (res.stderr[-150:] if res.returncode != 0 else 'too small')
        return True, f'{out_mp4.stat().st_size // 1024}KB'
    except subprocess.TimeoutExpired: return False, 'timeout'
    except Exception as e: return False, str(e)

def map_genres(tag_list):
    mapped = [GENRES_MAP.get(g, g) for g in (tag_list or []) if g]
    # Deduplicate, limit to 5
    seen, result = set(), []
    for g in mapped:
        if g not in seen:
            seen.add(g); result.append(g)
    return result[:5] if result else ['Drama', 'Romance']

def get_id_subtitle(sub_list):
    """Get Indonesian subtitle URL (prefer VTT, fallback SRT)."""
    for s in (sub_list or []):
        if s.get('language') == 'id-ID':
            return s.get('vtt') or s.get('subtitle') or ''
    return ''

def get_id_subtitle_srt(sub_list):
    """Get Indonesian subtitle SRT URL."""
    for s in (sub_list or []):
        if s.get('language') == 'id-ID':
            return s.get('subtitle') or ''
    return ''

# ── STAGE 1: Collect ─────────────────────────────────────────────────────────
def stage_collect(client, max_pages=100):
    existing = {}
    if TAB_DATA_FILE.exists():
        existing = json.loads(TAB_DATA_FILE.read_text(encoding='utf-8'))
        print(f'Loaded {len(existing)} existing dramas from file')

    for page in range(1, max_pages + 1):
        items = client.tab_feed(page=page, page_size=20)
        if not items:
            print(f'No more items at page {page}.')
            break

        new = 0
        for item in items:
            key = item.get('key')
            if not key or key in existing:
                continue

            ep_info  = item.get('episode_info', {}) or {}
            hls      = (ep_info.get('external_audio_h264_m3u8', '')
                        or ep_info.get('m3u8_url', ''))
            has_id   = 'id-ID' in (ep_info.get('audio') or [])
            tags_raw = [t.lower() for t in (item.get('tag') or []) + (item.get('series_tag') or [])]
            is_dubbed = any(t in ('dubbing', 'dubbed', 'sulih suara') for t in tags_raw)

            # Must have HLS URL and Indonesian audio or dubbed tag
            if not hls or (not has_id and not is_dubbed):
                continue

            sub_vtt = get_id_subtitle(ep_info.get('subtitle_list', []))
            sub_srt = get_id_subtitle_srt(ep_info.get('subtitle_list', []))

            existing[key] = {
                'series_key':   key,
                'title_orig':   item.get('title', key),      # judul asli (English)
                'title_id':     '',                           # diisi saat download (translate)
                'desc_orig':    item.get('desc', ''),         # desc asli (English)
                'desc_id':      '',                           # diisi saat download (translate)
                'cover':        item.get('cover', ''),
                'episode_count': item.get('episode_count', 0),
                'genres':       map_genres(item.get('series_tag', [])),
                'tags':         item.get('tag', []),
                'content_tags': item.get('content_tags', []),
                'free':         item.get('free', True),
                'view_count':   item.get('view_count', 0),
                'ep1_hls':      hls,
                'ep1_key':      ep_info.get('id', ''),
                'ep1_duration': ep_info.get('duration', 0),
                'ep1_sub_vtt':  sub_vtt,
                'ep1_sub_srt':  sub_srt,
                'has_id_audio': has_id,
                'is_dubbed':    is_dubbed,
            }
            new += 1

        print(f'  Page {page:3d}: +{new:3d} new (total: {len(existing):4d})')
        if not new:
            break
        if page % 10 == 0:
            client.login()
        time.sleep(0.5)

    TAB_DATA_FILE.write_text(json.dumps(existing, ensure_ascii=False, indent=2), encoding='utf-8')
    print(f'\n✓ Collected {len(existing)} dramas → {TAB_DATA_FILE}')
    return existing

# ── STAGE 2: Download → R2 ───────────────────────────────────────────────────
def stage_download(r2c, dramas, limit=None):
    # Sort: id-ID audio first
    all_ok = [v for v in dramas.values() if v.get('ep1_hls')
               and (v.get('has_id_audio') or v.get('is_dubbed'))]
    items  = sorted(all_ok, key=lambda x: (0 if x.get('has_id_audio') else 1))
    if limit:
        items = items[:limit]

    ok = skip = fail = 0
    total = len(items)

    for i, drama in enumerate(items, 1):
        key    = drama['series_key']
        t_orig = drama.get('title_orig') or drama.get('title', key)   # compat lama/baru
        hls    = drama.get('ep1_hls', '')

        # Folder name berdasarkan judul asli (lebih stabil)
        folder = safe_folder(t_orig)
        prefix = f'freereels/{folder}'
        meta_key = f'{prefix}/metadata.json'
        mp4_key  = f'{prefix}/ep_001.mp4'

        print(f'\n[{i:3d}/{total}] {key} — {t_orig[:45]}')

        if r2_exists(r2c, meta_key):
            print(f'  SKIP: already in R2')
            skip += 1
            continue

        if not hls:
            print(f'  SKIP: no HLS URL')
            skip += 1
            continue

        # 1. Translate judul & deskripsi → Bahasa Indonesia
        t_id = drama.get('title_id') or ''
        d_id = drama.get('desc_id')  or ''

        if not t_id:
            print(f'  🔤 Translate judul...', end=' ', flush=True)
            t_id = clean_title_id(t_orig)
            print(t_id[:50])
            drama['title_id'] = t_id
            time.sleep(0.3)

        if not d_id and drama.get('desc_orig'):
            print(f'  🔤 Translate deskripsi...', end=' ', flush=True)
            d_id = translate_to_id(drama['desc_orig'])
            print(d_id[:60] + '...')
            drama['desc_id'] = d_id
            time.sleep(0.3)
        elif not d_id:
            d_id = t_id + '. Drama pendek dubbing Indonesia.'
            drama['desc_id'] = d_id

        # 2. Upload cover
        cover_key = f'{prefix}/cover.jpg'
        cover_r2  = f'{R2_PUBLIC}/{cover_key}'
        if not r2_exists(r2c, cover_key):
            img = dl_bytes(drama.get('cover', ''))
            if img:
                r2_upload_bytes(r2c, img, cover_key, 'image/jpeg')
                print(f'  Cover ✓')

        # 3. Download + compress → MP4
        out  = TEMP_DIR / f'{folder}_ep001.mp4'
        out.unlink(missing_ok=True)
        print(f'  📥 Downloading + compressing...', end=' ', flush=True)
        ok2, msg = ffmpeg_convert(hls, out)

        if not ok2:
            print(f'✗ {msg}')
            fail += 1
            continue

        size_mb = out.stat().st_size / 1024 / 1024
        print(f'✓ {size_mb:.1f}MB')

        # 4. Upload MP4 → R2
        print(f'  ☁️  Uploading MP4...', end=' ', flush=True)
        r2_upload_file(r2c, out, mp4_key)
        print(f'✓')
        try: out.unlink()
        except: pass

        # 5. Build & upload metadata.json
        genres_final = drama.get('genres', ['Drama', 'Romance'])
        tags_final   = list(dict.fromkeys(drama.get('tags', []) + drama.get('content_tags', [])))

        metadata = {
            'source':          'freereels_tab514',
            'series_key':      key,
            'title':           t_id,           # Bahasa Indonesia
            'titleOriginal':   t_orig,          # Judul asli English
            'titleClean':      t_id,
            'description':     d_id,            # Bahasa Indonesia
            'descOriginal':    drama.get('desc_orig', ''),
            'cover':           cover_r2,
            'genres':          genres_final,
            'tags':            tags_final,
            'totalEpisodes':   drama.get('episode_count', 1),
            'uploadedEpisodes': 1,
            'status':          'ongoing',
            'language':        'Indonesia',
            'audioLanguage':   'id-ID',
            'country':         'China',
            'viewCount':       drama.get('view_count', 0),
            'r2Folder':        prefix,
            'episodes': [{
                'episode':     1,
                'title':       f'Episode 1',
                'duration':    drama.get('ep1_duration', 0),
                'videoUrl':    f'{R2_PUBLIC}/{mp4_key}',
                'subtitleVtt': drama.get('ep1_sub_vtt', ''),
                'subtitleSrt': drama.get('ep1_sub_srt', ''),
                'uploaded':    True,
                'free':        drama.get('free', True),
            }],
            'scrapedAt': int(time.time()),
        }

        r2_upload_bytes(
            r2c,
            json.dumps(metadata, ensure_ascii=False, indent=2).encode('utf-8'),
            meta_key
        )
        print(f'  📋 Metadata → R2 ✓')
        ok += 1
        time.sleep(0.3)

    # Save translate cache back to JSON
    TAB_DATA_FILE.write_text(
        json.dumps({k: v for k, v in dramas.items()}, ensure_ascii=False, indent=2),
        encoding='utf-8'
    )

    print(f'\n{"="*55}')
    print(f'✓ Berhasil: {ok}   ⊘ Dilewati: {skip}   ✗ Gagal: {fail}')

# ── STAGE 3: Import to DB ─────────────────────────────────────────────────────
def stage_import_db(r2c, dry_run=False):
    files, token = [], None
    while True:
        kw = {'Bucket': R2_BUCKET, 'Prefix': 'freereels/', 'MaxKeys': 1000}
        if token: kw['ContinuationToken'] = token
        resp = r2c.list_objects_v2(**kw)
        files += [o['Key'] for o in resp.get('Contents', [])
                  if o['Key'].endswith('/metadata.json')]
        token = resp.get('NextContinuationToken')
        if not token: break

    print(f'Found {len(files)} FreeReels dramas in R2')
    if not files: return

    conn = None if dry_run else psycopg2.connect(DATABASE_URL)
    if conn: conn.autocommit = False
    cur  = conn.cursor() if conn else None

    dramas_ok = eps_ok = skip = fail = 0

    for i, mkey in enumerate(files, 1):
        obj  = r2c.get_object(Bucket=R2_BUCKET, Key=mkey)
        meta = json.loads(obj['Body'].read().decode('utf-8'))

        sid     = meta.get('series_key', '')
        title   = meta.get('title') or meta.get('titleClean', '?')   # Bahasa Indonesia
        desc    = meta.get('description', '') or title + '. Drama pendek dubbing Indonesia.'
        eps     = [e for e in meta.get('episodes', [])
                   if e.get('uploaded') and e.get('videoUrl')]

        print(f'[{i:03d}] {title[:50]} ({len(eps)} eps)')
        if not eps:
            skip += 1; continue
        if dry_run:
            dramas_ok += 1; continue

        try:
            # Check already exists
            cur.execute('SELECT id FROM "Drama" WHERE description LIKE %s LIMIT 1',
                        (f'%[FRkey:{sid}]%',))
            row = cur.fetchone()

            if row:
                drama_id = row[0]
            else:
                desc_with_tag = desc.strip() + f'\n[FRkey:{sid}]'
                genres   = meta.get('genres', ['Drama', 'Romance'])
                tag_list = list(dict.fromkeys(meta.get('tags', []) + meta.get('content_tags', [])))

                cur.execute("""
                    INSERT INTO "Drama" (
                        id, title, description, cover, banner,
                        genres, "tagList", "totalEpisodes",
                        rating, views, likes, "reviewCount", "averageRating",
                        status, "isVip", "isFeatured", "isActive", "ageRating",
                        country, language, "createdAt", "updatedAt"
                    ) VALUES (
                        gen_random_uuid(), %s, %s, %s, %s,
                        %s::text[], %s::text[], %s,
                        0, %s, 0, 0, 0,
                        %s, false, false, false, 'all',
                        %s, %s, NOW(), NOW()
                    ) RETURNING id
                """, (
                    title,
                    desc_with_tag,
                    meta.get('cover', ''),
                    meta.get('cover', ''),
                    genres,
                    tag_list,
                    meta.get('totalEpisodes', 1),
                    meta.get('viewCount', 0),
                    meta.get('status', 'ongoing'),
                    meta.get('country', 'China'),
                    meta.get('language', 'Indonesia'),
                ))
                drama_id  = cur.fetchone()[0]
                dramas_ok += 1

            # Insert episodes
            for ep in eps:
                ep_num = ep.get('episode', 1)
                cur.execute(
                    'SELECT id FROM "Episode" WHERE "dramaId"=%s AND "episodeNumber"=%s',
                    (drama_id, ep_num)
                )
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
                """, (
                    drama_id,
                    ep_num,
                    ep.get('title', f'Episode {ep_num}'),
                    meta.get('cover', ''),
                    ep.get('videoUrl', ''),
                    ep.get('duration', 0),
                ))
                ep_id  = cur.fetchone()[0]
                eps_ok += 1

                # Subtitle
                sub_url = ep.get('subtitleVtt') or ep.get('subtitleSrt') or ''
                if sub_url:
                    cur.execute(
                        'SELECT id FROM "Subtitle" WHERE "episodeId"=%s LIMIT 1', (ep_id,)
                    )
                    if not cur.fetchone():
                        cur.execute("""
                            INSERT INTO "Subtitle"
                                (id, "episodeId", language, label, url, "isDefault", "createdAt")
                            VALUES
                                (gen_random_uuid(), %s, 'id', 'Bahasa Indonesia', %s, true, NOW())
                        """, (ep_id, sub_url))

            conn.commit()

        except Exception as e:
            if conn: conn.rollback()
            print(f'  ERROR: {e}')
            fail += 1

    print(f'\n{"="*55}')
    print(f'✓ Drama baru: {dramas_ok}   Episode: {eps_ok}')
    print(f'⊘ Dilewati: {skip}   ✗ Gagal: {fail}')
    print(f'\n⚠️  Semua diimport dengan isActive=False (status: Pending)')
    print(f'   Aktifkan via Admin Panel untuk publish.')
    if conn: cur.close(); conn.close()

# ── Status ────────────────────────────────────────────────────────────────────
def stage_status(r2c):
    files, token = [], None
    while True:
        kw = {'Bucket': R2_BUCKET, 'Prefix': 'freereels/', 'MaxKeys': 1000}
        if token: kw['ContinuationToken'] = token
        resp = r2c.list_objects_v2(**kw)
        files += [o['Key'] for o in resp.get('Contents', [])
                  if o['Key'].endswith('/metadata.json')]
        token = resp.get('NextContinuationToken')
        if not token: break

    collected = len(json.loads(TAB_DATA_FILE.read_text(encoding='utf-8'))) if TAB_DATA_FILE.exists() else 0
    print(f'Tab 514 terkumpul : {collected} dramas')
    print(f'R2 sudah upload   : {len(files)} dramas')
    if files:
        print(f'\nContoh R2:')
        for f in files[:5]:
            print(f'  - {f}')

# ── MAIN ──────────────────────────────────────────────────────────────────────
def main():
    p = argparse.ArgumentParser(description='FreeReels Tab-514 Full Pipeline (Indonesian Dubbed)')
    p.add_argument('--collect',   action='store_true', help='Stage 1: collect drama list')
    p.add_argument('--download',  action='store_true', help='Stage 2: compress + upload R2')
    p.add_argument('--import-db', action='store_true', dest='import_db', help='Stage 3: import DB (pending)')
    p.add_argument('--all',       action='store_true', help='Jalankan semua stage')
    p.add_argument('--status',    action='store_true', help='Cek status R2')
    p.add_argument('--limit',     type=int,  default=None, help='Batasi jumlah download')
    p.add_argument('--pages',     type=int,  default=100,  help='Max halaman collect (default: 100)')
    p.add_argument('--dry-run',   action='store_true', help='Mode simulasi (tanpa write)')
    a = p.parse_args()

    if not any([a.collect, a.download, a.import_db, a.all, a.status]):
        p.print_help(); return

    print('═' * 55)
    print('  FreeReels — Indonesian Dubbed Full Pipeline')
    print('═' * 55)
    print(f'  Mode: {"DRY-RUN" if a.dry_run else "PRODUCTION"}')
    if a.limit:
        print(f'  Limit: {a.limit} dramas')

    client = FRClient()
    if not client.login(): sys.exit(1)

    r2c = None if a.dry_run else get_r2()

    if a.status:
        stage_status(r2c); return

    dramas = {}

    if a.collect or a.all:
        print(f'\n[STAGE 1] Collect Tab 514 (max {a.pages} pages, Indonesian only)')
        dramas = stage_collect(client, max_pages=a.pages)
    else:
        if not TAB_DATA_FILE.exists():
            print(f'ERROR: {TAB_DATA_FILE} tidak ditemukan. Jalankan --collect dulu.')
            sys.exit(1)
        dramas = json.loads(TAB_DATA_FILE.read_text(encoding='utf-8'))
        print(f'Loaded {len(dramas)} dramas dari {TAB_DATA_FILE}')

    if a.download or a.all:
        print(f'\n[STAGE 2] Compress + Translate + Upload ke R2')
        if not a.dry_run:
            stage_download(r2c, dramas, limit=a.limit)
        else:
            print('DRY-RUN: skip download')

    if a.import_db or a.all:
        print(f'\n[STAGE 3] Import ke Database (isActive=False / Pending)')
        stage_import_db(r2c, dry_run=a.dry_run)

if __name__ == '__main__':
    main()
