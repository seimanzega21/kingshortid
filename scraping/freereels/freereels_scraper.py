"""
FreeReels Dubbed Drama Scraper — FINAL WORKING VERSION
=======================================================
API: apiv2.free-reels.com/frv2-api
Tab: 514 = "Dubbed"
Auth: MD5(APP_SECRET + '&' + auth_secret)
Encryption: AES-CBC with key '2r36789f45q01ae5'

Usage:
  python freereels_scraper.py --test      # Test 3 dramas, no R2 upload
  python freereels_scraper.py --limit 50  # Scrape first 50 dubbed dramas
  python freereels_scraper.py             # Full run (all dubbed dramas)
"""
import requests, hashlib, json, time, base64, os, re, sys, urllib.request
from cryptography.hazmat.primitives.ciphers import Cipher, algorithms, modes
from cryptography.hazmat.backends import default_backend
import boto3
from botocore.config import Config

# ─── CONFIG ───────────────────────────────────────────────────────────────────
APP_SECRET = '8IAcbWyCsVhYv82S2eofRqK1DF3nNDAv'
AES_KEY    = b'2r36789f45q01ae5'
BASE       = 'https://apiv2.free-reels.com/frv2-api'
APP_NAME   = 'com.freereels.app'
DEVICE     = 'android'
APP_VER    = '2.2.10'

DUBBED_TAB_KEY = '514'   # Dubbed tab confirmed from live API

# R2 Config
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

# ─── AUTH ─────────────────────────────────────────────────────────────────────
def make_device_hash():
    return hashlib.md5(b'freereels_scraper_v1_kingshortid').hexdigest()

def make_oauth(auth_key, auth_secret):
    sig = hashlib.md5(f'{APP_SECRET}&{auth_secret}'.encode()).hexdigest()
    ts  = int(time.time() * 1000)
    return f'oauth_signature={sig},oauth_token={auth_key},ts={ts}'

# ─── API CLIENT ───────────────────────────────────────────────────────────────
class FreeReelsClient:
    def __init__(self, country='ID', language='id'):
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
            'country':     country,
            'language':    language,
            'User-Agent':  f'{APP_NAME}/{APP_VER} (Android 12)',
            'Accept':      '*/*',
        })

    def _auth(self):
        if self.auth_key and self.auth_secret:
            return {'authorization': make_oauth(self.auth_key, self.auth_secret)}
        return {}

    def login(self):
        """Anonymous login (plain JSON, Skip-Encrypt:1)."""
        body = {'device_id': self.device_hash}
        r = self.sess.post(f'{BASE}/anonymous/login', json=body,
                           headers={'Content-Type': 'application/json', 'Skip-Encrypt': '1'}, timeout=15)
        resp = aes_decrypt(r.text) or r.json() if r.ok else {}
        data = resp.get('data', {})
        self.auth_key    = data.get('auth_key', '')
        self.auth_secret = data.get('auth_secret', '')
        ok = bool(self.auth_key)
        if ok:
            print(f'[LOGIN] OK — key={self.auth_key[:8]}... user_id={data.get("user_id")}')
        else:
            print(f'[LOGIN] FAILED: {resp}')
        return ok

    def _post(self, path, body=None):
        enc = aes_encrypt(body or {})
        hdrs = {**self._auth(), 'Content-Type': 'application/json'}
        r = self.sess.post(f'{BASE}{path}', data=enc, headers=hdrs, timeout=15)
        return aes_decrypt(r.text) or {}

    def _post_raw(self, path, body=None):
        """POST with Skip-Encrypt:1 (plain JSON)."""
        hdrs = {**self._auth(), 'Content-Type': 'application/json', 'Skip-Encrypt': '1'}
        r = self.sess.post(f'{BASE}{path}', json=body or {}, headers=hdrs, timeout=15)
        return aes_decrypt(r.text) or r.json() if r.ok else {}

    def _get(self, path, params=None):
        r = self.sess.get(f'{BASE}{path}', headers=self._auth(), params=params, timeout=15)
        return aes_decrypt(r.text) or r.json() if r.ok else {}

    def get_tabs(self):
        resp = self._get('/homepage/v2/tab/list')
        return (resp.get('data') or {}).get('list', [])

    def get_dubbed_dramas(self, max_pages=100):
        """Fetch all dramas from the Dubbed tab."""
        dramas = []
        for page in range(1, max_pages + 1):
            # Try both encrypted and raw POST
            for post_fn, body in [
                (self._post_raw, {'tab_key': DUBBED_TAB_KEY, 'page': page, 'page_size': 20}),
                (self._post,     {'tab_key': DUBBED_TAB_KEY, 'page': page, 'page_size': 20}),
                (self._get,      None),  # fallback: GET with params
            ]:
                if post_fn == self._get:
                    resp = self._get('/homepage/v2/tab/feed',
                                     params={'tab_key': DUBBED_TAB_KEY, 'page': page, 'page_size': 20})
                else:
                    resp = post_fn('/homepage/v2/tab/feed', body)
                
                code  = resp.get('code', '?')
                items = (resp.get('data') or {}).get('list', [])
                if code in [200, 0]:
                    if not items:
                        print(f'  Page {page}: 0 items (end of feed)')
                        return dramas
                    dramas.extend(items)
                    print(f'  Dubbed tab page {page}: +{len(items)} dramas (total {len(dramas)})')
                    time.sleep(0.5)
                    break
            else:
                # All methods failed — try to log the error
                print(f'  Page {page}: all methods failed (code={code})')
                if page == 1:
                    print(f'  Full resp: {json.dumps(resp)[:200]}')
                break
        return dramas

    def get_drama_detail(self, series_id):
        return self._get('/drama/info', params={'series_id': str(series_id)}) or {}

    def get_episodes(self, series_id):
        for path, body in [
            ('/episode/list', {'series_id': series_id}),
            ('/drama/episode/list', {'series_id': series_id}),
        ]:
            for post_fn in [self._post_raw, self._post]:
                resp = post_fn(path, body)
                code = resp.get('code', '?')
                if code in [200, 0]:
                    items = (resp.get('data') or {}).get('list', [])
                    if items: return items
        return []

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

def download_bytes(url):
    try:
        req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0'})
        with urllib.request.urlopen(req, timeout=20) as f: return f.read()
    except: return None

def safe_name(title):
    s = re.sub(r'[^\w\s-]', '', (title or 'drama').lower())
    return re.sub(r'[\s_-]+', '_', s).strip('_')[:60] or 'drama'

# ─── SCRAPE ONE DRAMA ─────────────────────────────────────────────────────────
def scrape_drama(client, r2, item, dry_run=False):
    series_id = (item.get('series_id') or item.get('id') or item.get('dramaId') or '')
    title     = item.get('title') or item.get('name') or f'drama_{series_id}'
    cover_url = item.get('cover') or item.get('coverUrl') or item.get('verticalCover') or ''

    if not series_id:
        return None

    folder   = safe_name(title)
    meta_key = f'{folder}/metadata.json'

    if not dry_run and r2_exists(r2, meta_key):
        print(f'  [SKIP] Already in R2: {folder}')
        return 'skip'

    # Get episodes
    episodes = client.get_episodes(series_id)
    if not episodes:
        # Try from item data itself
        episodes = item.get('episodes', item.get('episode_list', []))
    if not episodes:
        print(f'  [SKIP] No episodes found')
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

    # Build episode list (video stays on CDN)
    ep_list = []
    for i, ep in enumerate(episodes, 1):
        video_url = ep.get('videoUrl') or ep.get('url') or ep.get('playUrl') or ep.get('hls_url') or ''
        ep_list.append({
            'episode':   i,
            'episodeId': str(ep.get('episode_id') or ep.get('id') or ep.get('episodeId') or i),
            'title':     ep.get('title') or ep.get('name') or f'Episode {i}',
            'videoUrl':  video_url,
            'duration':  ep.get('duration') or 0,
        })

    metadata = {
        'id':            str(series_id),
        'title':         title,
        'cover':         cover_r2,
        'description':   item.get('description') or item.get('intro') or '',
        'totalEpisodes': len(ep_list),
        'language':      'Indonesia',
        'country':       'Indonesia',
        'source':        'freereels_dubbed',
        'sourceId':      str(series_id),
        'episodes':      ep_list,
    }

    if not dry_run:
        meta_bytes = json.dumps(metadata, ensure_ascii=False, indent=2).encode()
        upload_r2(r2, meta_bytes, meta_key, 'application/json')
        print(f'  Meta → {folder}/metadata.json ({len(ep_list)} eps)')

    return metadata

# ─── MAIN ─────────────────────────────────────────────────────────────────────
def main(dry_run=False, limit=None, test=False):
    print('=== FreeReels Dubbed Drama Scraper ===')
    print(f'API: {BASE}')
    print(f'Dubbed Tab: {DUBBED_TAB_KEY}')
    print()

    client = FreeReelsClient(country='ID', language='id')
    r2 = None if dry_run else get_r2()

    # 1. Login
    print('[1/4] Authenticating...')
    if not client.login():
        print('[ERROR] Login failed'); sys.exit(1)

    # 2. Show all tabs
    print('\n[2/4] Tabs available:')
    tabs = client.get_tabs()
    for t in tabs:
        tk = t.get('tab_key', '?'); bn = t.get('business_name', '?'); nm = t.get('name', '?')
        marker = ' ← DUBBED' if tk == DUBBED_TAB_KEY else ''
        print(f'  tab_key={tk} ({bn}) {repr(nm)}{marker}')

    # 3. Fetch dubbed dramas
    print(f"\n[3/4] Fetching dramas from Dubbed tab ({DUBBED_TAB_KEY})...")
    dramas = client.get_dubbed_dramas(max_pages=5 if test else 100)
    print(f'  Total dubbed dramas: {len(dramas)}')

    if not dramas:
        print('[WARN] No dramas found. Saving raw feed response...')
        return

    if test:
        dramas = dramas[:3]
    elif limit:
        dramas = dramas[:limit]

    # 4. Scrape
    if not dramas[0]:
        print('Empty drama objects returned')
        return

    print(f'\n[4/4] Scraping {len(dramas)} dramas...')
    print(f'First drama keys: {list(dramas[0].keys())}')
    print(f'First drama: {json.dumps(dramas[0], ensure_ascii=False)[:300]}')

    success, skip, fail = 0, 0, 0
    results = []
    for i, item in enumerate(dramas, 1):
        title = item.get('title') or item.get('name') or f'#{i}'
        print(f'\n[{i}/{len(dramas)}] {title}')
        try:
            res = scrape_drama(client, r2, item, dry_run=dry_run)
            if res == 'skip': skip += 1
            elif res: success += 1; results.append(res)
            else: fail += 1
            time.sleep(1)
        except Exception as e:
            print(f'  ERROR: {e}'); fail += 1

    out = 'dubbed_results.json'
    with open(out, 'w', encoding='utf-8') as f:
        json.dump(results, f, ensure_ascii=False, indent=2)
    print(f'\n=== DONE: {success} success | {skip} skip | {fail} fail ===')
    print(f'Results: {out}')

if __name__ == '__main__':
    import argparse
    p = argparse.ArgumentParser()
    p.add_argument('--test',    action='store_true')
    p.add_argument('--dry-run', action='store_true')
    p.add_argument('--limit',   type=int)
    a = p.parse_args()
    main(dry_run=a.dry_run or a.test, limit=a.limit, test=a.test)
