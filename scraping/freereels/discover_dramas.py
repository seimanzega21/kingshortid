"""
Smart Discover: Find 200+ dubbed dramas via API pagination.
Uses DramaWave homepage/tab/feed API with various methods.
Also uses search API with Indonesian keywords.
Saves to dubbed_series_ids.json
"""
import requests, re, json, time, base64, hashlib, os, sys
from cryptography.hazmat.primitives.ciphers import Cipher, algorithms, modes
from cryptography.hazmat.backends import default_backend

sys.stdout.reconfigure(encoding='utf-8', errors='replace')

APP_SECRET = '8IAcbWyCsVhYv82S2eofRqK1DF3nNDAv'
AES_KEY    = b'2r36789f45q01ae5'
BASE       = 'https://api.mydramawave.com/h5-api'
OUTPUT     = 'dubbed_series_ids.json'
TARGET     = 250

# ── Crypto ────────────────────────────────────────────────────────────────────
def dec(t):
    try:
        r = base64.b64decode(t); iv, ct = r[:16], r[16:]
        c = Cipher(algorithms.AES(AES_KEY[:16]), modes.CBC(iv), backend=default_backend())
        p = c.decryptor().update(ct) + c.decryptor().finalize()
        return json.loads(p[:-p[-1]].decode())
    except:
        try: return json.loads(t)
        except: return None

def enc(data):
    payload = json.dumps(data, separators=(',', ':')).encode()
    pad = 16 - (len(payload) % 16); payload += bytes([pad] * pad)
    iv = os.urandom(16)
    c = Cipher(algorithms.AES(AES_KEY[:16]), modes.CBC(iv), backend=default_backend())
    e = c.encryptor(); return base64.b64encode(iv + e.update(payload) + e.finalize()).decode()

# ── Login ─────────────────────────────────────────────────────────────────────
dh = hashlib.md5(b'freereels_discover_v2_smart').hexdigest()
sess = requests.Session()
sess.headers.update({
    'app-name': 'com.dramawave.h5', 'device': 'h5', 'app-version': '1.2.20',
    'device-id': dh, 'device-hash': dh, 'country': 'ID', 'language': 'id',
    'shortcode': 'id', 'User-Agent': 'Mozilla/5.0 (Linux; Android 12)',
})

def login():
    r = sess.post(f'{BASE}/anonymous/login', json={'device_id': dh},
                  headers={'Content-Type': 'application/json', 'Skip-Encrypt': '1'}, timeout=15)
    d = (dec(r.text) or r.json() or {}).get('data', {})
    ak = d.get('auth_key', ''); ase = d.get('auth_secret', '')
    print(f'Login: key={ak[:8]}...')
    return ak, ase

ak, ase = login()

def ah():
    sig = hashlib.md5(f'{APP_SECRET}&{ase}'.encode()).hexdigest()
    return {'authorization': f'oauth_signature={sig},oauth_token={ak},ts={int(time.time()*1000)}'}

# ── Load existing ──────────────────────────────────────────────────────────────
dubbed = {}
if os.path.exists(OUTPUT):
    with open(OUTPUT, encoding='utf-8') as f:
        dubbed = json.load(f)
print(f'Existing: {len(dubbed)} dubbed dramas\n')

def try_post(path, body):
    try:
        r = sess.post(f'{BASE}{path}', data=enc(body),
                      headers={**ah(), 'Content-Type': 'application/json'}, timeout=15)
        return dec(r.text) or {}
    except: return {}

def try_post_raw(path, body):
    try:
        r = sess.post(f'{BASE}{path}', json=body,
                      headers={**ah(), 'Content-Type': 'application/json', 'Skip-Encrypt': '1'}, timeout=15)
        return dec(r.text) or r.json() or {}
    except: return {}

def try_get(path, params={}):
    try:
        r = sess.get(f'{BASE}{path}', headers=ah(), params=params, timeout=15)
        return dec(r.text) or {}
    except: return {}

def extract_series_ids(items):
    """Extract series_id from various response formats."""
    ids = []
    for item in items or []:
        sid = item.get('id') or item.get('series_id') or item.get('drama_id')
        if sid and len(str(sid)) <= 20:  # Alphanumeric IDs are short
            ids.append(str(sid))
    return ids

def check_dubbed(series_id, info=None):
    """Check if a drama has Indonesian dubbed audio."""
    if not info:
        resp = try_get('/drama/info', {'series_id': series_id})
        if resp.get('code') not in [200, 0]: return None
        data = resp.get('data', {})
        info = data.get('info', data) if isinstance(data, dict) else data
    
    if not info: return None
    
    name = info.get('name', '')
    tags = info.get('tag', [])
    series_tags = info.get('series_tag', [])
    content_tags = info.get('content_tags', [])
    ep_count = info.get('episode_count', 0)
    eps = info.get('episode_list', [])
    
    # Check for Indonesian audio
    has_indo = False
    if 'Dubbing' in tags: has_indo = True
    if '(Sulih Suara)' in name: has_indo = True
    if eps and 'id-ID' in eps[0].get('audio', []): has_indo = True
    if eps and eps[0].get('external_audio_h264_m3u8'): has_indo = True
    
    if has_indo:
        return {
            'series_id': series_id,
            'title': name,
            'tags': tags,
            'genres': series_tags,
            'content_tags': content_tags,
            'episodes': ep_count,
            'cover': info.get('cover', ''),
            'desc': info.get('desc', ''),
            'status': 'complete' if info.get('finish_status') == 2 else 'ongoing',
        }
    return None

candidate_ids = set()

# ── Method 1: Search with keywords ───────────────────────────────────────────
print('=== Method 1: Search API ===')
search_terms = [
    'sulih suara', 'dubbing', 'sulih', 'dub indonesia',
    'drama dubbing', 'Indonesia dub', 'bahasa indonesia dub',
]
for term in search_terms:
    for page in range(1, 6):  # Up to 5 pages per keyword
        for post_fn in [try_post, try_post_raw]:
            resp = post_fn('/search/drama', {'keyword': term, 'page': page, 'page_size': 20})
            if resp.get('code') not in [200, 0]: continue
            items = (resp.get('data') or {}).get('list', [])
            if not items: break
            ids = extract_series_ids(items)
            new_ids = set(ids) - candidate_ids - set(dubbed.keys())
            candidate_ids.update(ids)
            if new_ids:
                print(f'  "{term}" p{page}: +{len(new_ids)} new candidates (total: {len(candidate_ids)})')
            time.sleep(0.3)
            if ids: break  # one method worked, next page

# ── Method 2: Homepage tab list ──────────────────────────────────────────────
print('\n=== Method 2: Homepage Tabs ===')
tab_resp = try_get('/homepage/v2/tab/list')
tabs = (tab_resp.get('data') or {}).get('list', [])
print(f'  Tabs found: {len(tabs)}')

for tab in tabs:
    tab_key = tab.get('tab_key') or tab.get('key')
    tab_name = tab.get('business_name') or tab.get('name', '?')
    print(f'  Tab: {tab_key} = {tab_name}')
    
    # Try various methods to fetch tab content
    for page in range(1, 11):
        got = False
        for body in [
            {'tab_key': tab_key, 'page': page, 'page_size': 20},
            {'tab_key': str(tab_key), 'page': page, 'page_size': 20},
            {'id': tab_key, 'page': page, 'page_size': 20},
        ]:
            for post_fn in [try_post, try_post_raw]:
                resp = post_fn('/homepage/v2/tab/feed', body)
                if resp.get('code') in [200, 0]:
                    items = (resp.get('data') or {}).get('list', [])
                    if items:
                        ids = extract_series_ids(items)
                        new_ids = set(ids) - candidate_ids
                        candidate_ids.update(ids)
                        if new_ids:
                            print(f'    Tab {tab_key} p{page}: +{len(new_ids)} new IDs')
                        got = True
                        break
            if got: break
        
        if not got: break
        time.sleep(0.3)

# ── Method 3: Drama list endpoints ──────────────────────────────────────────
print('\n=== Method 3: Drama List ===')
for body in [
    {'page': 1, 'page_size': 50, 'lang': 'id'},
    {'page': 1, 'page_size': 50, 'country': 'ID'},
    {'page': 1, 'page_size': 50},
]:
    for path in ['/drama/list', '/drama/recommend', '/homepage/v2/recommend']:
        resp = try_post(path, body)
        if resp.get('code') in [200, 0]:
            items = (resp.get('data') or {}).get('list', [])
            if items:
                ids = extract_series_ids(items)
                new_ids = set(ids) - candidate_ids
                candidate_ids.update(ids)
                print(f'  {path}: +{len(new_ids)} IDs (total: {len(candidate_ids)})')

# ── Validate candidates ───────────────────────────────────────────────────────
new_candidates = candidate_ids - set(dubbed.keys())
print(f'\n=== Validating {len(new_candidates)} new candidates ===')

validated = 0
for i, sid in enumerate(sorted(new_candidates), 1):
    if len(dubbed) >= TARGET:
        print(f'Target {TARGET} reached!')
        break
    
    try:
        result = check_dubbed(sid)
        if result:
            dubbed[sid] = result
            validated += 1
            print(f'  [{i:03d}] ✓ {result["title"][:40]} ({result["episodes"]} eps)')
            with open(OUTPUT, 'w', encoding='utf-8') as f:
                json.dump(dubbed, f, ensure_ascii=False, indent=2)
    except Exception as e:
        pass
    
    time.sleep(0.3)

print(f'\n{"="*50}')
print(f'Total dubbed dramas: {len(dubbed)}')
print(f'Newly validated: {validated}')
with open(OUTPUT, 'w', encoding='utf-8') as f:
    json.dump(dubbed, f, ensure_ascii=False, indent=2)
print(f'Saved → {OUTPUT}')
