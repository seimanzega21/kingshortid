"""
FreeReels - Episode-by-episode fetch strategy
Since drama/info is dead, try:
1. Get episode list via episode paginator
2. Or use tab 514 paginator which gives ep1 per drama
3. Test if there's an episode fetch by index
"""
import requests, hashlib, json, time, base64
from cryptography.hazmat.primitives.ciphers import Cipher, algorithms, modes
from cryptography.hazmat.backends import default_backend

APP_SECRET = '8IAcbWyCsVhYv82S2eofRqK1DF3nNDAv'
AES_KEY    = b'2r36789f45q01ae5'
FR_BASE    = 'https://apiv2.free-reels.com/frv2-api'
dh         = hashlib.md5(b'freereels_master_pipeline_v1').hexdigest()

sess = requests.Session()
sess.headers.update({
    'app-name': 'com.freereels.app', 'device': 'android',
    'app-version': '2.2.10', 'device-id': dh, 'device-hash': dh,
    'country': 'ID', 'language': 'id', 'shortcode': 'id',
    'User-Agent': 'okhttp/4.12.0',
})

r = sess.post(f'{FR_BASE}/anonymous/login', json={'device_id': dh},
              headers={'Content-Type': 'application/json', 'Skip-Encrypt': '1'}, timeout=15)
d = r.json().get('data', {})
ak, ase = d.get('auth_key', ''), d.get('auth_secret', '')
print(f'Login OK')

def ah():
    sig = hashlib.md5(f'{APP_SECRET}&{ase}'.encode()).hexdigest()
    return {'authorization': f'oauth_signature={sig},oauth_token={ak},ts={int(time.time()*1000)}'}

def dec(t):
    try:
        rb = base64.b64decode(t)
        iv, ct = rb[:16], rb[16:]
        c = Cipher(algorithms.AES(AES_KEY[:16]), modes.CBC(iv), backend=default_backend())
        p = c.decryptor().update(ct) + c.decryptor().finalize()
        return json.loads(p[:-p[-1]].decode())
    except:
        try: return json.loads(t)
        except: return None

SERIES_KEY = 'qQKGMS5WbW'
EP_KEY     = 'JvVys2cBjA'  # episode 1 key

# Test 1: Single episode fetch (maybe we can fetch ep by ep)
print('\n=== Single episode fetch ===')
ep_single_endpoints = [
    f'{FR_BASE}/drama/episode',
    f'{FR_BASE}/drama/ep',
    f'{FR_BASE}/episode/info',
    f'{FR_BASE}/drama/episode/info',
    f'{FR_BASE}/drama/play',
]
for url in ep_single_endpoints:
    r = sess.get(url, headers=ah(), params={'series_id': SERIES_KEY, 'index': 2}, timeout=8)
    ep = url.split('/frv2-api/')[1]
    decoded = dec(r.text)
    code = decoded.get('code', '?') if decoded else '?'
    if r.status_code != 404:
        print(f'  HIT! {ep}: {r.status_code} code={code} len={len(r.text)}')
        print(f'    {str(decoded)[:200] if decoded else r.text[:100]}')
    else:
        print(f'  404: {ep}')
    time.sleep(0.2)

# Test 2: Episode list via POST with different field names
print('\n=== Episode list POST variants ===')
post_variants = [
    {'key': SERIES_KEY},
    {'series_key': SERIES_KEY},
    {'series_id': SERIES_KEY, 'language': 'id'},
    {'series_id': SERIES_KEY, 'lang': 'id-ID'},
    {'id': SERIES_KEY},
]
for body in post_variants:
    r = sess.post(f'{FR_BASE}/drama/episode_list',
                  headers={**ah(), 'Content-Type': 'application/json', 'Skip-Encrypt': '1'},
                  json={**body, 'page': 1, 'page_size': 20}, timeout=8)
    decoded = dec(r.text)
    code = decoded.get('code', '?') if decoded else '?'
    if r.status_code != 404:
        print(f'  HIT! body={body}: {r.status_code} code={code}')
        print(f'    {str(decoded)[:200] if decoded else r.text[:100]}')
    else:
        print(f'  404: body={body}')
    time.sleep(0.2)

# Test 3: Use 'popular' tab with different module_key
print('\n=== Tab feed with module = series episodes ===')
r = sess.post(f'{FR_BASE}/homepage/v2/tab/feed',
              json={'tab_key': '514', 'module_key': 'series_episode', 'series_id': SERIES_KEY, 'page': 1, 'page_size': 20},
              headers={**ah(), 'Content-Type': 'application/json', 'Skip-Encrypt': '1'}, timeout=15)
print(f'Status: {r.status_code}')
if r.ok:
    d = r.json()
    print(f'Response: {str(d)[:200]}')
