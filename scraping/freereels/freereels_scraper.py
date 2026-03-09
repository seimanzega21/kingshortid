"""
FreeReels / DramaWave Indonesian Dubbed Drama Scraper
======================================================
VERIFIED working flow:
  1. Login anonymous (Skip-Encrypt:1)
  2. Find dubbed dramas via homepage tab feed OR search
  3. For each drama: GET /drama/info?series_id=ALPHANUMERIC
     → episode_list with external_audio_h264_m3u8 (Indonesian dubbed HLS)
     → subtitle_list with id-ID subtitle
  4. Upload metadata + cover to R2 (video stays on CDN via HLS)

Confirmed from live API:
  series_id='Cdg4Th1kpv' → 70 eps, Indonesian audio available
  series_id='8hX52C1Do1' → 60 eps, Indonesian audio available
  episode.external_audio_h264_m3u8 = Indonesian dubbed HLS URL
  episode.audio = list of available audio languages (contains 'id-ID')
  episode.subtitle_list = Indonesian subtitle URL (type='original')

Usage:
  python freereels_scraper.py --test      # dry-run 3 dramas
  python freereels_scraper.py --discover  # find series_ids via browser scan
  python freereels_scraper.py             # full scrape + R2 upload
"""
import requests, hashlib, json, time, base64, os, re, sys, urllib.request
from cryptography.hazmat.primitives.ciphers import Cipher, algorithms, modes
from cryptography.hazmat.backends import default_backend
import boto3
from botocore.config import Config

# ─── CONFIG ───────────────────────────────────────────────────────────────────
APP_SECRET   = '8IAcbWyCsVhYv82S2eofRqK1DF3nNDAv'
AES_KEY      = b'2r36789f45q01ae5'
BASE         = 'https://api.mydramawave.com/h5-api'
APP_NAME     = 'com.dramawave.h5'
APP_VER      = '1.2.20'

# R2
R2_ENDPOINT  = 'https://a142d3b29a5d64943cb251157e25eaf3.r2.cloudflarestorage.com'
R2_KEY_ID    = '07c99c897986ea52703c1285308d5e2c'
R2_SECRET    = '44788d376ffb216e1e73784b6fe1ff1423607928898a87c50819b52cdfc12e44'
R2_BUCKET    = 'shortlovers'
R2_PUBLIC    = 'https://stream.shortlovers.id'

# Known dubbed drama series IDs (verified from live browser)
# Format: alphanumeric string from m.mydramawave.com/series/[id]
KNOWN_DUBBED_IDS = [
    'Cdg4Th1kpv',   # Bertahan Hidup di Sekolah Elite (Sulih Suara) - 70 eps
    '8hX52C1Do1',   # Terbangun sebagai Suami Terburuknya (Sulih Suara) - 60 eps
]

# ─── AES ─────────────────────────────────────────────────────────────────────
def aes_decrypt(text):
    try:
        raw = base64.b64decode(text)
        iv, ct = raw[:16], raw[16:]
        c = Cipher(algorithms.AES(AES_KEY[:16]), modes.CBC(iv), backend=default_backend())
        p = c.decryptor().update(ct) + c.decryptor().finalize()
        return json.loads(p[:-p[-1]].decode())
    except:
        try: return json.loads(text)
        except: return None

def aes_encrypt(data):
    payload = json.dumps(data, separators=(',', ':')).encode()
    pad = 16 - (len(payload) % 16); payload += bytes([pad] * pad)
    iv = os.urandom(16)
    c = Cipher(algorithms.AES(AES_KEY[:16]), modes.CBC(iv), backend=default_backend())
    e = c.encryptor()
    return base64.b64encode(iv + e.update(payload) + e.finalize()).decode()

# ─── API CLIENT ───────────────────────────────────────────────────────────────
class DramaWaveClient:
    def __init__(self, country='ID', language='id'):
        self.country  = country
        self.language = language
        self.dh       = hashlib.md5(b'freereels_scraper_v1_kingshortid').hexdigest()
        self.auth_key = None
        self.auth_sec = None
        self.sess     = requests.Session()
        self.sess.headers.update({
            'app-name':    APP_NAME,
            'device':      'h5',
            'app-version': APP_VER,
            'device-id':   self.dh,
            'device-hash': self.dh,
            'country':     country,
            'language':    language,
            'User-Agent':  'Mozilla/5.0 (Linux; Android 12)',
            'Accept':      '*/*',
        })

    def _auth(self):
        if not (self.auth_key and self.auth_sec): return {}
        sig = hashlib.md5(f'{APP_SECRET}&{self.auth_sec}'.encode()).hexdigest()
        ts  = int(time.time() * 1000)
        return {'authorization': f'oauth_signature={sig},oauth_token={self.auth_key},ts={ts}'}

    def login(self):
        r = self.sess.post(f'{BASE}/anonymous/login', json={'device_id': self.dh},
                           headers={'Content-Type': 'application/json', 'Skip-Encrypt': '1'},
                           timeout=15)
        resp = aes_decrypt(r.text) or r.json() if r.ok else {}
        data = resp.get('data', {})
        self.auth_key = data.get('auth_key', '')
        self.auth_sec = data.get('auth_secret', '')
        ok = bool(self.auth_key)
        if ok:
            print(f'[LOGIN] OK — key={self.auth_key[:8]}... uid={data.get("user_id")}')
        else:
            print(f'[LOGIN] FAILED: {resp}')
        return ok

    def get_drama_info(self, series_id):
        """GET /drama/info?series_id=ALPHANUMERIC — returns info + episode_list."""
        r = self.sess.get(f'{BASE}/drama/info', headers=self._auth(),
                          params={'series_id': series_id}, timeout=20)
        resp = aes_decrypt(r.text) or {}
        if resp.get('code') not in [200, 0]:
            return None
        data = resp.get('data', {})
        return data.get('info', data) if isinstance(data, dict) else data

    def _post(self, path, body):
        """POST with AES-encrypted body."""
        r = self.sess.post(f'{BASE}{path}', data=aes_encrypt(body),
                           headers={**self._auth(), 'Content-Type': 'application/json'},
                           timeout=15)
        return aes_decrypt(r.text) or {}

    def _post_raw(self, path, body):
        """POST with plain JSON (Skip-Encrypt)."""
        r = self.sess.post(f'{BASE}{path}', json=body,
                           headers={**self._auth(), 'Content-Type': 'application/json',
                                    'Skip-Encrypt': '1'}, timeout=15)
        return aes_decrypt(r.text) or r.json() if r.ok else {}

    def search_dubbed_dramas(self, page=1, page_size=20):
        """Search for dubbed dramas via search/drama endpoint."""
        for kw in ['sulih suara', 'dubbing', 'dubbed', 'dub']:
            for post_fn in [self._post, self._post_raw]:
                resp = post_fn('/search/drama', {'keyword': kw, 'page': page,
                                                  'page_size': page_size})
                code = resp.get('code', '?')
                items = (resp.get('data') or {}).get('list', [])
                if code in [200, 0] and items:
                    print(f'  Search "{kw}": {len(items)} results')
                    return items
        return []

    def get_homepage_dramas(self, page=1):
        """Get dramas from homepage popular tab."""
        # Tab list first
        r = self.sess.get(f'{BASE}/homepage/v2/tab/list', headers=self._auth(), timeout=15)
        tabs_resp = aes_decrypt(r.text) or {}
        tabs = (tabs_resp.get('data') or {}).get('list', [])
        print(f'  Tabs: {[t.get("tab_key") for t in tabs]}')
        return []

    def discover_series_from_website(self, limit=200):
        """Scan DramaWave website pages to find series IDs for dubbed dramas."""
        series_ids = set(KNOWN_DUBBED_IDS)
        
        # Try to find more from sitemap or RSS-like pages
        for url in [
            'https://m.mydramawave.com/free-app/',
            'https://m.mydramawave.com/',
        ]:
            try:
                r = requests.get(url, timeout=15, headers={
                    'User-Agent': 'Mozilla/5.0',
                    'Accept-Language': 'id-ID,id;q=0.9',
                })
                html = r.text
                # Find alphanumeric series IDs in hrefs
                ids = re.findall(r'/series/([A-Za-z0-9]{8,12})/?', html)
                series_ids.update(ids)
                print(f'  Found {len(ids)} series IDs from {url}')
            except: pass

        # Filter only dubbed ones by checking drama info tags
        dubbed_ids = []
        print(f'  Screening {len(series_ids)} series IDs for dubbed...')
        for sid in list(series_ids):
            info = self.get_drama_info(sid)
            if not info: continue
            tags = info.get('tag', [])
            has_id_audio = any('id-ID' in ep.get('audio', []) 
                              for ep in info.get('episode_list', [])[:1])
            is_dubbed = 'Dubbing' in tags or has_id_audio
            if is_dubbed:
                print(f'  ✓ Dubbed: {info.get("name", sid)} ({info.get("episode_count")} eps)')
                dubbed_ids.append(sid)
            time.sleep(0.3)
        return dubbed_ids

# ─── R2 ───────────────────────────────────────────────────────────────────────
def get_r2():
    return boto3.client('s3', endpoint_url=R2_ENDPOINT,
                        aws_access_key_id=R2_KEY_ID, aws_secret_access_key=R2_SECRET,
                        config=Config(signature_version='s3v4'), region_name='auto')

def r2_exists(r2, key):
    try: r2.head_object(Bucket=R2_BUCKET, Key=key); return True
    except: return False

def upload_r2(r2, data_bytes, key, ct='application/octet-stream'):
    r2.put_object(Bucket=R2_BUCKET, Key=key, Body=data_bytes, ContentType=ct)
    return f'{R2_PUBLIC}/{key}'

def download_bytes(url, timeout=30):
    try:
        req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0'})
        with urllib.request.urlopen(req, timeout=timeout) as f:
            return f.read()
    except Exception as e:
        print(f'    Download failed: {e}'); return None

def safe_folder(title):
    s = re.sub(r'[^\w\s-]', '', (title or 'drama').lower())
    return re.sub(r'[\s_-]+', '_', s).strip('_')[:60] or 'drama'

# ─── EPISODE PROCESSING ──────────────────────────────────────────────────────
def has_indonesian_audio(episode):
    """Check if episode has Indonesian (id-ID) audio track."""
    audio_list = episode.get('audio', [])
    if 'id-ID' in audio_list: return True
    ext = episode.get('external_audio_h264_m3u8', '')
    if ext: return True  # external_audio = dubbed audio
    return False

def get_indonesian_subtitle(episode):
    """Extract Indonesian subtitle URL from episode."""
    if not episode: return None
    for sub in (episode.get('subtitle_list') or []):
        if sub.get('language') == 'id-ID':
            return {
                'srt': sub.get('subtitle', ''),
                'vtt': sub.get('vtt', ''),
                'type': sub.get('type', 'normal'),  # 'original' = from source file
            }
    return None

def build_episode_data(ep, ep_num):
    """Build episode metadata dict from API episode object."""
    ext_h264 = ep.get('external_audio_h264_m3u8', '')
    m3u8     = ep.get('m3u8_url', '')
    video    = ep.get('video_url', '')
    
    # Video URL priority: external_audio (dubbed) > m3u8 > video_url
    hls_url = ext_h264 or m3u8 or video
    
    id_sub = get_indonesian_subtitle(ep)
    
    return {
        'episode':          ep_num,
        'episodeId':        str(ep.get('id', ep_num)),
        'title':            ep.get('name', f'Episode {ep_num}'),
        'cover':            ep.get('cover', ''),
        'hlsUrl':           hls_url,
        'externalAudioH264': ext_h264,
        'externalAudioH265': ep.get('external_audio_h265_m3u8', ''),
        'originalAudioLang': ep.get('original_audio_language', 'zh-CN'),
        'availableAudio':   ep.get('audio', []),
        'indonesianSubSrt': id_sub.get('srt') if id_sub else '',
        'indonesianSubVtt': id_sub.get('vtt') if id_sub else '',
        'duration':         ep.get('duration', 0),
        'free':             ep.get('video_type', '') == 'free',
    }

# ─── SCRAPE ONE DRAMA ─────────────────────────────────────────────────────────
def scrape_drama(client, r2, series_id, dry_run=False):
    """Scrape a single drama: fetch info, upload cover, save metadata."""
    info = client.get_drama_info(series_id)
    if not info:
        print(f'  [SKIP] Cannot fetch drama info for {series_id}')
        return None

    title   = info.get('name', series_id)
    cover   = info.get('cover', '')
    tag     = info.get('tag', [])
    ep_list = info.get('episode_list', [])
    
    print(f'  Drama: {title}')
    print(f'  Tags: {tag} | Episodes: {len(ep_list)}')

    # Filter only episodes with Indonesian audio
    indo_eps = [ep for ep in ep_list if has_indonesian_audio(ep)]
    if not indo_eps:
        print(f'  [SKIP] No Indonesian audio episodes found')
        return None
    
    print(f'  Indonesian audio episodes: {len(indo_eps)}/{len(ep_list)}')

    folder   = safe_folder(title)
    meta_key = f'{folder}/metadata.json'

    if not dry_run and r2_exists(r2, meta_key):
        print(f'  [SKIP] Already in R2: {folder}')
        return 'skip'

    # Upload cover image
    cover_r2 = cover
    if cover and not dry_run:
        cover_key = f'{folder}/cover.jpg'
        if not r2_exists(r2, cover_key):
            img = download_bytes(cover)
            if img:
                cover_r2 = upload_r2(r2, img, cover_key, 'image/jpeg')
                print(f'  Cover → R2: {cover_key}')
        else:
            cover_r2 = f'{R2_PUBLIC}/{cover_key}'

    # Build episode metadata
    episodes_data = [build_episode_data(ep, i + 1) for i, ep in enumerate(indo_eps)]
    
    # Check if drama has Indonesian as tagged dubbing
    is_dubbing = 'Dubbing' in tag or any(ep.get('externalAudioH264') for ep in episodes_data)
    
    metadata = {
        'id':              series_id,
        'title':           title,
        'titleClean':      re.sub(r'\(Sulih Suara\)', '', title).strip(),
        'cover':           cover_r2,
        'description':     info.get('desc', ''),
        'tags':            tag,
        'seriesTags':      info.get('series_tag', []),
        'totalEpisodes':   len(indo_eps),
        'episodeCount':    info.get('episode_count', len(ep_list)),
        'status':          'complete' if info.get('finish_status') == 2 else 'ongoing',
        'language':        'Indonesia',
        'audioLanguage':   'id-ID',
        'originalAudio':   'zh-CN',
        'isDubbing':        is_dubbing,
        'source':          'freereels_dubbed',
        'sourceId':        series_id,
        'viewCount':       info.get('view_count', 0),
        'followCount':     info.get('follow_count', 0),
        'episodes':        episodes_data,
        'scrapedAt':       int(time.time()),
    }

    if dry_run:
        print(f'  [DRY-RUN] Would upload {folder}/metadata.json')
        print(f'  Sample ep[0]: hlsUrl={episodes_data[0]["hlsUrl"][:60]}...')
        print(f'  Indo sub ep[0]: {episodes_data[0]["indonesianSubSrt"][:60]}...')
        return metadata

    meta_bytes = json.dumps(metadata, ensure_ascii=False, indent=2).encode()
    upload_r2(r2, meta_bytes, meta_key, 'application/json')
    print(f'  Metadata → R2: {folder}/metadata.json ({len(episodes_data)} eps)')
    return metadata

# ─── MAIN ─────────────────────────────────────────────────────────────────────
def main():
    import argparse
    p = argparse.ArgumentParser(description='FreeReels Indonesian Dubbed Scraper')
    p.add_argument('--test',     action='store_true', help='Dry-run with known IDs')
    p.add_argument('--discover', action='store_true', help='Discover all dubbed drama IDs')
    p.add_argument('--ids',      nargs='+',           help='Specific series_id(s) to scrape')
    p.add_argument('--limit',    type=int,             help='Max dramas to scrape')
    a = p.parse_args()

    print('═══════════════════════════════════════════')
    print('  FreeReels Indonesian Dubbed Drama Scraper')
    print('═══════════════════════════════════════════')
    print(f'  API: {BASE}')
    print(f'  Mode: {"DRY-RUN" if a.test else "PRODUCTION"}')
    print()

    client = DramaWaveClient(country='ID', language='id')
    r2     = None if a.test else get_r2()

    print('[1/3] Authenticating...')
    if not client.login():
        print('[ERROR] Login failed'); sys.exit(1)

    print(f'\n[2/3] Getting drama IDs...')
    if a.ids:
        series_ids = a.ids
    elif a.test:
        series_ids = KNOWN_DUBBED_IDS
    elif a.discover:
        print('  Discovering dubbed dramas...')
        series_ids = client.discover_series_from_website()
    else:
        # Default: use known IDs
        series_ids = KNOWN_DUBBED_IDS
        print(f'  Using {len(series_ids)} known dubbed drama IDs')
        print('  Tip: use --discover to find more, or --ids to specify manually')

    if a.limit:
        series_ids = series_ids[:a.limit]
    
    print(f'  Will scrape {len(series_ids)} dramas')

    print(f'\n[3/3] Scraping {len(series_ids)} dubbed dramas...')
    success, skip, fail = 0, 0, 0
    results = []

    for i, sid in enumerate(series_ids, 1):
        print(f'\n[{i}/{len(series_ids)}] {sid}')
        try:
            res = scrape_drama(client, r2, sid, dry_run=a.test)
            if res == 'skip':
                skip += 1
            elif res:
                success += 1
                results.append({'series_id': sid, 'title': res.get('title', ''),
                                 'episodes': res.get('totalEpisodes', 0)})
            else:
                fail += 1
            time.sleep(1)
        except Exception as e:
            import traceback
            print(f'  ERROR: {e}')
            traceback.print_exc()
            fail += 1

    print(f'\n{"═"*43}')
    print(f'  ✓ Success: {success}  ⊘ Skipped: {skip}  ✗ Failed: {fail}')
    print(f'{"═"*43}')
    
    out = 'scrape_results.json'
    with open(out, 'w', encoding='utf-8') as f:
        json.dump(results, f, ensure_ascii=False, indent=2)
    print(f'Results saved: {out}')

if __name__ == '__main__':
    main()
