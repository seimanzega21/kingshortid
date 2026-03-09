"""
Test API with Skip-Encrypt:1 header to bypass body encryption.
Find dubbed drama catalog and working tab feed.
"""
import sys, json, time, base64, hashlib, os
import requests
from cryptography.hazmat.primitives.ciphers import Cipher, algorithms, modes
from cryptography.hazmat.backends import default_backend

sys.stdout.reconfigure(encoding='utf-8', errors='replace')

AES_KEY = b'2r36789f45q01ae5'
APP_SECRET = '8IAcbWyCsVhYv82S2eofRqK1DF3nNDAv'
BASE = 'https://api.mydramawave.com/h5-api'

def dec(t):
    try:
        r = base64.b64decode(t); iv, ct = r[:16], r[16:]
        c = Cipher(algorithms.AES(AES_KEY[:16]), modes.CBC(iv), backend=default_backend())
        p = c.decryptor().update(ct) + c.decryptor().finalize()
        return json.loads(p[:-p[-1]].decode())
    except:
        try: return json.loads(t)
        except: return None

dh = hashlib.md5(b'freereels_scraper_v1_kingshortid').hexdigest()
s = requests.Session()
base_hdrs = {
    'app-name': 'com.dramawave.h5', 'device': 'h5', 'app-version': '1.2.20',
    'device-id': dh, 'device-hash': dh, 'country': 'ID', 'language': 'id',
    'shortcode': 'id', 'User-Agent': 'Mozilla/5.0', 'Accept': '*/*',
}
s.headers.update(base_hdrs)

# Login
r = s.post(f'{BASE}/anonymous/login', json={'device_id': dh},
           headers={'Content-Type': 'application/json', 'Skip-Encrypt': '1'}, timeout=15)
d = (dec(r.text) or r.json() or {}).get('data', {})
ak = d.get('auth_key', ''); ase = d.get('auth_secret', '')
print(f'Login: user={d.get("user_id")} key={ak[:8]}...')

def ah():
    sig = hashlib.md5(f'{APP_SECRET}&{ase}'.encode()).hexdigest()
    ts = int(time.time() * 1000)
    return {'authorization': f'oauth_signature={sig},oauth_token={ak},ts={ts}'}

def skip_post(path, body):
    """POST with Skip-Encrypt:1 — server handles plain JSON."""
    hdrs = {**ah(), 'Content-Type': 'application/json', 'Skip-Encrypt': '1'}
    r = s.post(f'{BASE}{path}', json=body, headers=hdrs, timeout=15)
    resp = dec(r.text)
    if not resp:
        try: resp = r.json()
        except: resp = {'raw': r.text[:200]}
    return resp

def skip_get(path, params=None):
    r = s.get(f'{BASE}{path}', headers={**ah(), 'Skip-Encrypt': '1'}, params=params, timeout=15)
    resp = dec(r.text)
    if not resp:
        try: resp = r.json()
        except: resp = {'raw': r.text[:200]}
    return resp

# 1. Tab feed with Skip-Encrypt
print('\n=== Tab 28 feed (Skip-Encrypt) ===')
resp = skip_post('/homepage/v2/tab/feed', {'tab_key': '28', 'page': 1, 'page_size': 3})
print(f'code={resp.get("code")} msg={resp.get("message","")[:60]}')
data = resp.get('data', {}); items = data.get('list', []) if isinstance(data, dict) else []
print(f'Items: {len(items)}')
if items:
    first = items[0]
    print('First item keys:', list(first.keys()))
    for k in ['id', 'title', 'name', 'label', 'labels', 'tags', 'dubbed', 'audio']:
        if k in first: print(f'  {k}: {json.dumps(first[k], ensure_ascii=False)[:80]}')

# 2. Try tabId vs tab_key
print('\n=== Tab feed with tabId (not tab_key) ===')
resp2 = skip_post('/homepage/v2/tab/feed', {'tabId': '28', 'page': 1, 'page_size': 3})
print(f'tabId=28: code={resp2.get("code")}')
resp3 = skip_post('/homepage/v2/tab/feed', {'tabId': 28, 'page': 1, 'page_size': 3})
print(f'tabId=28 (int): code={resp3.get("code")}')

# 3. Try tab list GET (count all tabs)
print('\n=== Tab list GET (Skip-Encrypt) ===')
resp4 = skip_get('/homepage/v2/tab/list')
data4 = resp4.get('data', {})
tabs = data4.get('list', []) if isinstance(data4, dict) else data4 if isinstance(data4, list) else []
print(f'Tabs found: {len(tabs)}')
for t in tabs:
    print(f'  tab_key={t.get("tab_key")} name={t.get("name")} biz={t.get("business_name")} active={t.get("active")}')

# 4. Drama catalog with all possible paths
print('\n=== Drama catalog paths (Skip-Encrypt POST) ===')
paths_to_try = [
    ('/drama/list', {'page': 1, 'page_size': 5}),
    ('/drama/page', {'page': 1, 'page_size': 5}),
    ('/series/list', {'page': 1, 'page_size': 5}),
    ('/content/list', {'page': 1, 'page_size': 5}),
    ('/drama/index', {'page': 1, 'page_size': 5}),
    ('/drama/all', {}),
    ('/drama/category', {'page': 1}),
    ('/category/drama/list', {'page': 1, 'page_size': 5}),
]
for path, body in paths_to_try:
    resp = skip_post(path, body)
    code = resp.get('code', '?'); msg = resp.get('message', '')[:50]
    hit = 'HIT!' if code in [200, 0] else ''
    print(f'  {path} -> {code}: {msg} {hit}')
    if code in [200, 0]:
        with open('drama_catalog.json', 'w', encoding='utf-8') as f:
            json.dump(resp, f, ensure_ascii=False, indent=2)
        print(f'  *** Saved to drama_catalog.json ***')

# 5. Check drama detail to understand labeled dubbing
print('\n=== Drama detail (to check dubbed label) ===')
# Try drama ID from popular tab
if items:
    drama_id = items[0].get('id') or items[0].get('drama_id')
    if drama_id:
        resp5 = skip_post('/drama/view', {'drama_id': drama_id})
        code5 = resp5.get('code', '?')
        print(f'Drama {drama_id}: code={code5}')
        if code5 in [200, 0]:
            dd = resp5.get('data', {})
            for k in ['title', 'dubbed', 'language', 'labels', 'tags', 'audio_type', 'dub']:
                if k in dd: print(f'  {k}: {json.dumps(dd[k], ensure_ascii=False)[:100]}')
