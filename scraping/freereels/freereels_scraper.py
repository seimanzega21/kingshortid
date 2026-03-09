"""
FreeReels / DramaWave Dubbed Drama Scraper
==========================================
Full reverse-engineered scraper targeting dubbed (Indonesian) dramas.

Auth Formula (from JS bundle):
  oauth_signature = MD5( APP_SECRET + '&' + auth_secret )
  oauth_token     = auth_key
  ts              = Date.now()

Login Body: { device_id: <md5_device_hash> }
AES-CBC key: '2r36789f45q01ae5'
"""

import requests
import hashlib
import json
import time
import base64
import os
import re
import sys
from cryptography.hazmat.primitives.ciphers import Cipher, algorithms, modes
from cryptography.hazmat.backends import default_backend
import boto3
from botocore.config import Config
import urllib.request

# ─── CONSTANTS ────────────────────────────────────────────────────────────────
APP_SECRET = '8IAcbWyCsVhYv82S2eofRqK1DF3nNDAv'   # from JS bundle
AES_KEY    = b'2r36789f45q01ae5'                   # from crypt-web JS

BASE_URL   = 'https://api.mydramawave.com/h5-api'
APP_NAME   = 'com.dramawave.h5'
DEVICE     = 'h5'
APP_VER    = '1.2.20'
COUNTRY    = 'ID'
LANGUAGE   = 'id'

# R2
R2_ENDPOINT = 'https://a142d3b29a5d64943cb251157e25eaf3.r2.cloudflarestorage.com'
R2_KEY_ID   = '07c99c897986ea52703c1285308d5e2c'
R2_SECRET   = '44788d376ffb216e1e73784b6fe1ff1423607928898a87c50819b52cdfc12e44'
R2_BUCKET   = 'shortlovers'
R2_PUBLIC   = 'https://stream.shortlovers.id'

# ─── AES-CBC ──────────────────────────────────────────────────────────────────
def aes_decrypt(text):
    try:
        raw = base64.b64decode(text)
        iv, ct = raw[:16], raw[16:]
        cipher = Cipher(algorithms.AES(AES_KEY[:16]), modes.CBC(iv), backend=default_backend())
        padded = cipher.decryptor().update(ct) + cipher.decryptor().finalize()
        return json.loads(padded[:-padded[-1]].decode())
    except Exception:
        try:
            return json.loads(text)
        except Exception:
            return None

def aes_encrypt(data):
    payload = json.dumps(data, separators=(',', ':')).encode()
    pad = 16 - (len(payload) % 16)
    payload += bytes([pad] * pad)
    iv = os.urandom(16)
    cipher = Cipher(algorithms.AES(AES_KEY[:16]), modes.CBC(iv), backend=default_backend())
    enc = cipher.encryptor()
    return base64.b64encode(iv + enc.update(payload) + enc.finalize()).decode()

# ─── AUTH ─────────────────────────────────────────────────────────────────────
def make_device_hash():
    """MD5 of a stable device fingerprint."""
    seed = 'freereels_scraper_v1_kingshortid'
    return hashlib.md5(seed.encode()).hexdigest()

def make_oauth(auth_key, auth_secret):
    """oauth_signature = MD5(APP_SECRET + '&' + auth_secret)"""
    sig = hashlib.md5(f'{APP_SECRET}&{auth_secret}'.encode()).hexdigest()
    ts  = int(time.time() * 1000)
    return f'oauth_signature={sig},oauth_token={auth_key},ts={ts}'

# ─── API CLIENT ───────────────────────────────────────────────────────────────
class DramaWaveClient:
    def __init__(self):
        self.device_hash = make_device_hash()
        self.auth_key    = None
        self.auth_secret = None
        self.sess        = requests.Session()
        self.sess.headers.update({
            'app-name':    APP_NAME,
            'device':      DEVICE,
            'app-version': APP_VER,
            'device-id':   self.device_hash,
            'device-hash': self.device_hash,
            'country':     COUNTRY,
            'language':    LANGUAGE,
            'shortcode':   'id',
            'User-Agent':  'Mozilla/5.0 (Linux; Android 12)',
            'Accept':      '*/*',
        })

    def _auth(self):
        if self.auth_key and self.auth_secret:
            return {'authorization': make_oauth(self.auth_key, self.auth_secret)}
        return {}

    def login(self):
        """Anonymous login → get auth_key and auth_secret.
        
        From JS interceptor: body is AES-encrypted, sent as application/json.
        Try both: plain with Skip-Encrypt:1, then encrypted body.
        """
        body = {'device_id': self.device_hash}
        
        # Strategy 1: Skip-Encrypt:1 header (server decrypts nothing)
        for attempt in [
            {'headers': {**self._auth(), 'Content-Type': 'application/json', 'Skip-Encrypt': '1'}, 'json': body},
            # Strategy 2: AES encrypted body, Content-Type: application/json
            {'headers': {**self._auth(), 'Content-Type': 'application/json'}, 'data': aes_encrypt(body)},
            # Strategy 3: Raw string body
            {'headers': {**self._auth(), 'Content-Type': 'text/plain'}, 'data': aes_encrypt(body)},
        ]:
            try:
                kw = {k: v for k, v in attempt.items() if k != 'headers'}
                r = self.sess.post(f'{BASE_URL}/anonymous/login',
                                   headers=attempt['headers'], timeout=15, **kw)
                resp = aes_decrypt(r.text)
                if not resp:
                    try:
                        resp = r.json()
                    except Exception:
                        resp = {}
                code = resp.get('code')
                data = resp.get('data') or {}
                print(f'[LOGIN] status={r.status_code} code={code} msg={resp.get("message","")[:40]}')
                
                if code in [200, 0]:
                    self.auth_key    = (data.get('auth_key') or data.get('key') or
                                        data.get('oauthToken') or data.get('token'))
                    self.auth_secret = (data.get('auth_secret') or data.get('secret') or
                                        data.get('oauthSecret'))
                    if self.auth_key:
                        print(f'[LOGIN] OK → key={self.auth_key[:8]}...')
                        return True
                    print(f'[LOGIN] No auth_key in: {data}')
            except Exception as e:
                print(f'[LOGIN] attempt error: {e}')
        return False

    def _post(self, path, body=None, skip_encrypt=False):
        """POST with AES-encrypted body (Content-Type: application/json).
        Use skip_encrypt=True to send raw JSON (for login only).
        """
        if skip_encrypt:
            hdrs = {**self._auth(), 'Content-Type': 'application/json', 'Skip-Encrypt': '1'}
            r = self.sess.post(f'{BASE_URL}{path}', json=body or {}, headers=hdrs, timeout=15)
        else:
            enc  = aes_encrypt(body or {})
            hdrs = {**self._auth(), 'Content-Type': 'application/json'}
            r = self.sess.post(f'{BASE_URL}{path}', data=enc, headers=hdrs, timeout=15)
        return aes_decrypt(r.text) or {}

    def _get(self, path, params=None):
        r = self.sess.get(f'{BASE_URL}{path}', headers=self._auth(), params=params, timeout=15)
        return aes_decrypt(r.text) or {}

    def get_tabs(self):
        resp = self._get('/homepage/v2/tab/list')
        return resp.get('data', {}).get('tabs', resp.get('data', []))

    def get_tab_feed(self, tab_id, page=1, size=20):
        resp = self._post('/homepage/v2/tab/feed', {
            'tabId': tab_id, 'page': page, 'pageSize': size
        })
        return resp.get('data', {})

    def get_all_in_tab(self, tab_id, max_pages=50):
        """Fetch ALL dramas from a specific tab."""
        dramas = []
        for page in range(1, max_pages + 1):
            data = self.get_tab_feed(tab_id, page=page, size=20)
            items = data.get('list', data.get('items', data.get('records', [])))
            if not items:
                break
            dramas.extend(items)
            print(f'  Tab {tab_id} page {page}: +{len(items)} (total {len(dramas)})')
            time.sleep(0.5)
        return dramas

    def get_drama_detail(self, drama_id):
        resp = self._post('/drama/view', {'dramaId': drama_id})
        return resp.get('data', {})

    def get_episodes(self, drama_id):
        for path, body in [
            ('/episode/list', {'dramaId': drama_id, 'pageSize': 200}),
            ('/chapter/list', {'bookId': drama_id, 'pageSize': 200}),
        ]:
            resp = self._post(path, body)
            items = resp.get('data', {}).get('list', resp.get('data', []))
            if isinstance(items, list) and items:
                return items
        return []

# ─── R2 ───────────────────────────────────────────────────────────────────────
def get_r2():
    return boto3.client('s3',
        endpoint_url=R2_ENDPOINT,
        aws_access_key_id=R2_KEY_ID,
        aws_secret_access_key=R2_SECRET,
        config=Config(signature_version='s3v4'),
        region_name='auto',
    )

def r2_exists(r2, key):
    try:
        r2.head_object(Bucket=R2_BUCKET, Key=key)
        return True
    except Exception:
        return False

def upload_r2(r2, data_bytes, key, ct='application/octet-stream'):
    r2.put_object(Bucket=R2_BUCKET, Key=key, Body=data_bytes, ContentType=ct)
    return f'{R2_PUBLIC}/{key}'

def download_bytes(url):
    try:
        req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0'})
        with urllib.request.urlopen(req, timeout=20) as f:
            return f.read()
    except Exception:
        return None

def safe_name(title):
    s = re.sub(r'[^\w\s-]', '', (title or 'drama').lower())
    return re.sub(r'[\s_-]+', '_', s).strip('_')[:60] or 'drama'

# ─── SCRAPER ──────────────────────────────────────────────────────────────────
def is_dubbed(item):
    """Return True if drama has dubbing/dubbed label."""
    text = json.dumps(item, ensure_ascii=False).lower()
    return any(k in text for k in ['dubb', 'dubbed', 'dubbing', 'sulih suara'])

def scrape_drama(client, r2, item, dry_run=False):
    """Upload cover + metadata for one drama. Videos stay on CDN (metadata-only pattern)."""
    drama_id = (item.get('id') or item.get('dramaId') or
                item.get('seriesId') or item.get('bookId'))
    if not drama_id:
        return None

    title     = item.get('title') or item.get('name') or f'drama_{drama_id}'
    cover_url = (item.get('cover') or item.get('coverUrl') or
                 item.get('verticalCover') or item.get('poster') or '')
    folder    = safe_name(title)
    source_id = str(drama_id)

    # Skip if metadata already exists in R2
    meta_key = f'{folder}/metadata.json'
    if r2_exists(r2, meta_key):
        print(f'  [SKIP] Already in R2: {folder}')
        return 'skip'

    # Get full detail + episodes
    detail   = client.get_drama_detail(drama_id) or item
    episodes = client.get_episodes(drama_id)

    title     = detail.get('title') or title
    cover_url = (detail.get('cover') or detail.get('coverUrl') or cover_url)
    desc      = (detail.get('description') or detail.get('intro') or
                 detail.get('synopsis') or '')

    if not episodes:
        print(f'  [SKIP] No episodes: {title}')
        return None

    # Upload cover
    cover_r2 = cover_url
    if cover_url and not dry_run:
        cover_key = f'{folder}/cover.jpg'
        if not r2_exists(r2, cover_key):
            img = download_bytes(cover_url)
            if img:
                cover_r2 = upload_r2(r2, img, cover_key, 'image/jpeg')
                print(f'  Cover → {cover_key}')
        else:
            cover_r2 = f'{R2_PUBLIC}/{cover_key}'

    # Build episode list (video URLs stay on DramaWave CDN)
    ep_list = []
    for i, ep in enumerate(episodes, 1):
        video_url = (ep.get('videoUrl') or ep.get('url') or
                     ep.get('playUrl') or ep.get('hlsUrl') or '')
        ep_list.append({
            'episode':   i,
            'episodeId': str(ep.get('id') or ep.get('episodeId') or ep.get('chapterId') or i),
            'title':     ep.get('title') or ep.get('name') or f'Episode {i}',
            'videoUrl':  video_url,
            'duration':  ep.get('duration') or ep.get('length') or 0,
        })

    metadata = {
        'id':            source_id,
        'title':         title,
        'cover':         cover_r2,
        'description':   desc,
        'totalEpisodes': len(ep_list),
        'language':      'Indonesia',
        'country':       'Indonesia',
        'source':        'freereels_dubbed',
        'sourceId':      source_id,
        'episodes':      ep_list,
    }

    if not dry_run:
        meta_bytes = json.dumps(metadata, ensure_ascii=False, indent=2).encode()
        upload_r2(r2, meta_bytes, meta_key, 'application/json')
        print(f'  Meta → {folder}/metadata.json ({len(ep_list)} eps)')

    return metadata

# ─── MAIN ─────────────────────────────────────────────────────────────────────
def main(dry_run=False, limit=None):
    print('=== FreeReels Dubbed Drama Scraper ===')
    print(f'Target: {COUNTRY}/{LANGUAGE} | Dubbed only')
    print()

    client = DramaWaveClient()
    r2 = get_r2()

    # Login
    print('[1/4] Logging in (anonymous)...')
    if not client.login():
        print('[ERROR] Login failed')
        sys.exit(1)

    # Get tabs
    print('\n[2/4] Fetching homepage tabs...')
    tabs = client.get_tabs()
    print(f'  Found {len(tabs)} tabs:')
    for t in tabs:
        tid  = t.get('tabId') or t.get('id') or t.get('name')
        name = t.get('name') or t.get('tabName') or t.get('title') or tid
        print(f'    id={tid}  name={name}')

    # Find dubbed tab or scan all tabs
    dubbed_tab_ids = []
    for t in tabs:
        name = str(t.get('name') or t.get('tabName') or '').lower()
        tid  = str(t.get('tabId') or t.get('id') or '')
        if any(k in name for k in ['dub', 'indonesia', 'sulih', 'id']):
            dubbed_tab_ids.append(tid)
            print(f'  [DUBBED TAB] id={tid} name={name}')

    if not dubbed_tab_ids:
        print('  No dedicated dubbed tab found — will scan all tabs and filter by label')
        dubbed_tab_ids = [str(t.get('tabId') or t.get('id') or '') for t in tabs]

    # Collect dramas
    print('\n[3/4] Collecting dubbed dramas...')
    all_items = []
    for tab_id in dubbed_tab_ids:
        if not tab_id:
            continue
        print(f'  Tab: {tab_id}')
        items = client.get_all_in_tab(tab_id, max_pages=30 if not limit else 5)
        # Filter dubbed
        dubbed = [x for x in items if is_dubbed(x)]
        all_items.extend(dubbed)
        print(f'  → {len(dubbed)}/{len(items)} are dubbed')

    # Deduplicate by ID
    seen = set()
    unique = []
    for x in all_items:
        xid = str(x.get('id') or x.get('dramaId') or x.get('seriesId') or '')
        if xid and xid not in seen:
            seen.add(xid)
            unique.append(x)

    print(f'\n  Total unique dubbed dramas: {len(unique)}')
    if limit:
        unique = unique[:limit]
        print(f'  Limited to: {len(unique)}')

    # Scrape
    print(f'\n[4/4] Scraping {len(unique)} dubbed dramas...')
    success, skip, fail = 0, 0, 0
    results = []

    for i, item in enumerate(unique, 1):
        title = item.get('title') or item.get('name') or f'#{i}'
        print(f'[{i}/{len(unique)}] {title}')
        try:
            res = scrape_drama(client, r2, item, dry_run=dry_run)
            if res == 'skip':
                skip += 1
            elif res:
                success += 1
                results.append(res)
            else:
                fail += 1
            time.sleep(1)
        except Exception as e:
            print(f'  ERROR: {e}')
            fail += 1

    # Save results summary
    summary_path = 'dubbed_results.json'
    with open(summary_path, 'w', encoding='utf-8') as f:
        json.dump(results, f, ensure_ascii=False, indent=2)

    print(f'\n=== DONE ===')
    print(f'  Success: {success} | Skip: {skip} | Fail: {fail}')
    print(f'  Results saved: {summary_path}')


if __name__ == '__main__':
    import argparse
    p = argparse.ArgumentParser()
    p.add_argument('--dry-run',  action='store_true', help='No R2 upload')
    p.add_argument('--limit',    type=int,            help='Max dramas')
    p.add_argument('--test',     action='store_true', help='Test: 3 dramas, dry-run')
    args = p.parse_args()

    if args.test:
        main(dry_run=True, limit=3)
    else:
        main(dry_run=args.dry_run, limit=args.limit)
